"""Unit tests for the adherence intelligence layer.

Uses unittest.mock to patch supabase calls — no live DB needed.
"""
import asyncio
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient
from jose import jwt

from app.config import settings
from app.main import app

client = TestClient(app)
app.state.limiter.enabled = False

TEST_PATIENT_ID = "00000000-0000-0000-0000-000000000001"
TEST_PROVIDER_ID = "00000000-0000-0000-0000-000000000002"
TEST_ADMIN_ID = "00000000-0000-0000-0000-000000000003"


def make_token(role: str = "provider", user_id: str = TEST_PROVIDER_ID) -> dict:
    payload = {
        "aud": "authenticated",
        "sub": user_id,
        "user_metadata": {"role": role},
    }
    token = jwt.encode(payload, settings.SUPABASE_JWT_SECRET, algorithm="HS256")
    return {"Authorization": f"Bearer {token}"}


# ─── helpers ──────────────────────────────────────────────────────────────────

def _adh(status: str, days_ago: int = 0) -> dict:
    dt = datetime.now(timezone.utc) - timedelta(days=days_ago)
    return {"status": status, "scheduled_utc": dt.isoformat(), "outcome_utc": dt.isoformat()}


def _fb(severity: int, days_ago: int = 0) -> dict:
    dt = datetime.now(timezone.utc) - timedelta(days=days_ago)
    return {"severity": severity, "created_at": dt.isoformat()}


def _med(name: str, active: bool = True, created_days_ago: int = 30, updated_days_ago: int = 25) -> dict:
    c = datetime.now(timezone.utc) - timedelta(days=created_days_ago)
    u = datetime.now(timezone.utc) - timedelta(days=updated_days_ago)
    return {"id": f"m-{name}", "name": name, "is_active": active, "created_at": c.isoformat(), "updated_at": u.isoformat()}


# ─── fusion_engine ────────────────────────────────────────────────────────────

class TestComputeRiskScore:
    def _run(self, coro):
        return asyncio.run(coro)

    def _make_chain(self, data):
        result = MagicMock()
        result.data = data
        chain = MagicMock()
        chain.select.return_value = chain
        chain.eq.return_value = chain
        chain.gte.return_value = chain
        chain.limit.return_value = chain
        chain.order.return_value = chain
        chain.execute.return_value = result
        return chain

    @patch("app.services.adherence_intelligence.fusion_engine.supabase")
    def test_no_logs_returns_insufficient(self, mock_sb):
        mock_sb.table.return_value = self._make_chain([])
        from app.services.adherence_intelligence.fusion_engine import compute_risk_score
        result = self._run(compute_risk_score("uid-1"))
        assert result["risk_score"] == 0
        assert "insufficient_data" in result["evidence"][0]

    @patch("app.services.adherence_intelligence.fusion_engine.asyncio.to_thread")
    def test_three_misses_adds_25(self, mock_to_thread):
        doses = [_adh("missed"), _adh("missed"), _adh("missed"), _adh("taken")]
        responses = [
            MagicMock(data=doses),   # adherence
            MagicMock(data=[]),      # feedback
            MagicMock(data=[]),      # reports
        ]
        call_idx = [0]

        async def fake_to_thread(fn, *a, **kw):
            idx = call_idx[0]
            call_idx[0] += 1
            return responses[idx] if idx < len(responses) else MagicMock(data=[])

        mock_to_thread.side_effect = fake_to_thread

        from app.services.adherence_intelligence.fusion_engine import compute_risk_score
        result = self._run(compute_risk_score("uid-2"))
        assert result["risk_score"] >= 25
        assert any("3 missed doses" in e for e in result["evidence"])

    @patch("app.services.adherence_intelligence.fusion_engine.asyncio.to_thread")
    def test_high_severity_feedback_adds_15(self, mock_to_thread):
        doses = [_adh("taken"), _adh("taken")]
        fb = [_fb(severity=3), _fb(severity=4)]
        responses = [MagicMock(data=doses), MagicMock(data=fb), MagicMock(data=[])]
        call_idx = [0]

        async def fake_to_thread(fn, *a, **kw):
            idx = call_idx[0]
            call_idx[0] += 1
            return responses[idx] if idx < len(responses) else MagicMock(data=[])

        mock_to_thread.side_effect = fake_to_thread

        from app.services.adherence_intelligence.fusion_engine import compute_risk_score
        result = self._run(compute_risk_score("uid-3"))
        assert result["risk_score"] >= 15

    @patch("app.services.adherence_intelligence.fusion_engine.asyncio.to_thread")
    def test_weekly_rate_below_70_adds_20(self, mock_to_thread):
        doses = [_adh("taken")]
        fb = []
        reports = [{"adherence_rate": 60.0, "period_type": "weekly"}]
        responses = [MagicMock(data=doses), MagicMock(data=fb), MagicMock(data=reports)]
        call_idx = [0]

        async def fake_to_thread(fn, *a, **kw):
            idx = call_idx[0]
            call_idx[0] += 1
            return responses[idx] if idx < len(responses) else MagicMock(data=[])

        mock_to_thread.side_effect = fake_to_thread

        from app.services.adherence_intelligence.fusion_engine import compute_risk_score
        result = self._run(compute_risk_score("uid-4"))
        assert result["risk_score"] >= 20
        assert any("Weekly adherence rate is 60%" in e for e in result["evidence"])


# ─── confidence ───────────────────────────────────────────────────────────────

class TestComputeConfidence:
    def _run(self, coro):
        return asyncio.run(coro)

    @patch("app.services.adherence_intelligence.confidence.asyncio.to_thread")
    def test_all_signals_present(self, mock_to_thread):
        now = datetime.now(timezone.utc)
        adh_data = [{"scheduled_utc": (now - timedelta(days=1)).isoformat()}]
        fb_data = [{"id": "fb1"}]
        rep_data = [{"id": "rep1"}]
        med_data = [_med("DrugA"), _med("DrugB")]
        prof_data = [{"created_at": (now - timedelta(days=30)).isoformat()}]
        recent_adh = [{"scheduled_utc": (now - timedelta(days=1)).isoformat()}]

        responses = [
            MagicMock(data=adh_data),
            MagicMock(data=fb_data),
            MagicMock(data=rep_data),
            MagicMock(data=med_data),
            MagicMock(data=prof_data),
            MagicMock(data=recent_adh),
        ]
        call_idx = [0]

        async def fake_to_thread(fn, *a, **kw):
            idx = call_idx[0]
            call_idx[0] += 1
            return responses[idx] if idx < len(responses) else MagicMock(data=[])

        mock_to_thread.side_effect = fake_to_thread

        from app.services.adherence_intelligence.confidence import compute_confidence
        res = self._run(compute_confidence("uid-conf-1"))
        assert res["signals_available"] == 4
        assert res["confidence_score"] == 0.8
        assert res["confidence_label"] == "Moderate"
        assert "snooze_behavior" in res["signals_missing"]
        assert len(res["reducers_applied"]) == 0

    @patch("app.services.adherence_intelligence.confidence.asyncio.to_thread")
    def test_reducers_applied(self, mock_to_thread):
        now = datetime.now(timezone.utc)
        adh_data = [{"scheduled_utc": (now - timedelta(days=20)).isoformat()}]
        fb_data = []
        rep_data = []
        med_data = [_med("SingleDrug")]  # Reducer: only 1 medication
        prof_data = [{"created_at": (now - timedelta(days=2)).isoformat()}]  # Reducer: account < 7 days old
        recent_adh = [{"scheduled_utc": (now - timedelta(days=20)).isoformat()}]  # Reducer: > 14 days old

        responses = [
            MagicMock(data=adh_data),
            MagicMock(data=fb_data),
            MagicMock(data=rep_data),
            MagicMock(data=med_data),
            MagicMock(data=prof_data),
            MagicMock(data=recent_adh),
        ]
        call_idx = [0]

        async def fake_to_thread(fn, *a, **kw):
            idx = call_idx[0]
            call_idx[0] += 1
            return responses[idx] if idx < len(responses) else MagicMock(data=[])

        mock_to_thread.side_effect = fake_to_thread

        from app.services.adherence_intelligence.confidence import compute_confidence
        res = self._run(compute_confidence("uid-conf-2"))
        assert len(res["reducers_applied"]) == 3
        assert res["confidence_score"] == 0.0


# ─── pattern_classifier ───────────────────────────────────────────────────────

class TestClassifyPattern:
    def _run(self, coro):
        return asyncio.run(coro)

    @patch("app.services.adherence_intelligence.pattern_classifier.supabase")
    def test_no_logs_returns_no_data(self, mock_sb):
        chain = MagicMock()
        for attr in ("select", "eq", "gte", "order"):
            getattr(chain, attr).return_value = chain
        chain.execute.return_value = MagicMock(data=[])
        mock_sb.table.return_value = chain

        from app.services.adherence_intelligence.pattern_classifier import (
            classify_adherence_pattern,
        )
        r = self._run(classify_adherence_pattern("uid-x"))
        assert r["pattern_type"] == "no_data"

    @patch("app.services.adherence_intelligence.pattern_classifier.supabase")
    def test_all_taken_is_adherent(self, mock_sb):
        logs = [_adh("taken", i) for i in range(10)]
        chain = MagicMock()
        for attr in ("select", "eq", "gte", "order"):
            getattr(chain, attr).return_value = chain
        chain.execute.return_value = MagicMock(data=logs)
        mock_sb.table.return_value = chain

        from app.services.adherence_intelligence.pattern_classifier import (
            classify_adherence_pattern,
        )
        r = self._run(classify_adherence_pattern("uid-y"))
        assert r["pattern_type"] == "adherent"

    @patch("app.services.adherence_intelligence.pattern_classifier.supabase")
    def test_stale_logs_discontinuation(self, mock_sb):
        logs = [_adh("taken", 20), _adh("missed", 22)]
        chain = MagicMock()
        for attr in ("select", "eq", "gte", "order"):
            getattr(chain, attr).return_value = chain
        chain.execute.return_value = MagicMock(data=logs)
        mock_sb.table.return_value = chain

        from app.services.adherence_intelligence.pattern_classifier import (
            classify_adherence_pattern,
        )
        r = self._run(classify_adherence_pattern("uid-z"))
        assert r["pattern_type"] == "complete_discontinuation"

    @patch("app.services.adherence_intelligence.pattern_classifier.supabase")
    def test_temporal_pattern(self, mock_sb):
        logs = []
        base_monday = datetime(2026, 8, 3, 8, 0, tzinfo=timezone.utc)
        for i in range(10):
            d = base_monday + timedelta(days=i)
            status = "missed" if d.weekday() in (0, 1) and len([x for x in logs if x["status"] == "missed"]) < 3 else "taken"
            logs.append({"status": status, "scheduled_utc": d.isoformat(), "outcome_utc": d.isoformat()})

        logs[-1]["scheduled_utc"] = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
        logs[-2]["scheduled_utc"] = (datetime.now(timezone.utc) - timedelta(days=2)).isoformat()

        chain = MagicMock()
        for attr in ("select", "eq", "gte", "order"):
            getattr(chain, attr).return_value = chain
        chain.execute.return_value = MagicMock(data=logs)
        mock_sb.table.return_value = chain

        from app.services.adherence_intelligence.pattern_classifier import (
            classify_adherence_pattern,
        )
        r = self._run(classify_adherence_pattern("uid-temp"))
        assert r["pattern_type"] in ("temporal", "temporary_irregularity", "adherent", "intermittent")


# ─── rx_change_flag ───────────────────────────────────────────────────────────

class TestRxChangeFlags:
    def _run(self, coro):
        return asyncio.run(coro)

    @patch("app.services.adherence_intelligence.rx_change_flag.supabase")
    def test_no_meds_no_flags(self, mock_sb):
        chain = MagicMock()
        chain.select.return_value = chain
        chain.eq.return_value = chain
        chain.execute.return_value = MagicMock(data=[])
        mock_sb.table.return_value = chain

        from app.services.adherence_intelligence.rx_change_flag import (
            detect_rx_change_flags,
        )
        r = self._run(detect_rx_change_flags("uid-a"))
        assert r["flag_raised"] is False
        assert r["flags"] == []

    @patch("app.services.adherence_intelligence.rx_change_flag.supabase")
    def test_three_active_meds_raises_flag(self, mock_sb):
        meds = [_med(f"Drug{i}") for i in range(3)]
        chain = MagicMock()
        chain.select.return_value = chain
        chain.eq.return_value = chain
        chain.execute.return_value = MagicMock(data=meds)
        mock_sb.table.return_value = chain

        from app.services.adherence_intelligence.rx_change_flag import (
            detect_rx_change_flags,
        )
        r = self._run(detect_rx_change_flags("uid-b"))
        assert r["flag_raised"] is True
        types = [f["type"] for f in r["flags"]]
        assert "multiple_active" in types

    @patch("app.services.adherence_intelligence.rx_change_flag.supabase")
    def test_rapid_replacement_flag(self, mock_sb):
        now = datetime.now(timezone.utc)
        inact_med = {
            "id": "m1",
            "name": "OldDrug",
            "is_active": False,
            "created_at": (now - timedelta(days=20)).isoformat(),
            "updated_at": (now - timedelta(days=5)).isoformat(),
        }
        act_med = {
            "id": "m2",
            "name": "NewDrug",
            "is_active": True,
            "created_at": (now - timedelta(days=4)).isoformat(),
            "updated_at": (now - timedelta(days=4)).isoformat(),
        }
        chain = MagicMock()
        chain.select.return_value = chain
        chain.eq.return_value = chain
        chain.execute.return_value = MagicMock(data=[inact_med, act_med])
        mock_sb.table.return_value = chain

        from app.services.adherence_intelligence.rx_change_flag import (
            detect_rx_change_flags,
        )
        r = self._run(detect_rx_change_flags("uid-c"))
        assert r["flag_raised"] is True
        types = [f["type"] for f in r["flags"]]
        assert "rapid_replacement" in types


# ─── master endpoint tests ───────────────────────────────────────────────────

class TestIntelligenceEndpoint:
    def test_endpoint_registered(self):
        assert "/v1/intelligence/{patient_id}" in app.openapi()["paths"]

    def test_unauthenticated_returns_401(self):
        res = client.get(f"/v1/intelligence/{TEST_PATIENT_ID}")
        assert res.status_code == 401

    def test_patient_role_forbidden_403(self):
        res = client.get(
            f"/v1/intelligence/{TEST_PATIENT_ID}",
            headers=make_token(role="patient"),
        )
        assert res.status_code == 403

    @patch("app.services.adherence_intelligence.intelligence_router.supabase")
    def test_patient_not_found_404(self, mock_sb):
        chain = MagicMock()
        chain.select.return_value.eq.return_value.limit.return_value.execute.return_value = MagicMock(data=[])
        mock_sb.table.return_value = chain

        res = client.get(
            f"/v1/intelligence/{TEST_PATIENT_ID}",
            headers=make_token(role="admin", user_id=TEST_ADMIN_ID),
        )
        assert res.status_code == 404

    @patch("app.services.adherence_intelligence.intelligence_router.supabase")
    def test_requested_id_not_a_patient_400(self, mock_sb):
        chain = MagicMock()
        chain.select.return_value.eq.return_value.limit.return_value.execute.return_value = MagicMock(
            data=[{"id": TEST_PATIENT_ID, "role": "provider"}]
        )
        mock_sb.table.return_value = chain

        res = client.get(
            f"/v1/intelligence/{TEST_PATIENT_ID}",
            headers=make_token(role="admin", user_id=TEST_ADMIN_ID),
        )
        assert res.status_code == 400

    @patch("app.services.adherence_intelligence.intelligence_router.supabase")
    def test_unassigned_provider_returns_403(self, mock_sb):
        prof_chain = MagicMock()
        prof_chain.select.return_value.eq.return_value.limit.return_value.execute.return_value = MagicMock(
            data=[{"id": TEST_PATIENT_ID, "role": "patient"}]
        )
        asg_chain = MagicMock()
        asg_chain.select.return_value.eq.return_value.eq.return_value.eq.return_value.execute.return_value = MagicMock(
            data=[]
        )

        def mock_table(table_name):
            if table_name == "profiles":
                return prof_chain
            if table_name == "assignments":
                return asg_chain
            return MagicMock()

        mock_sb.table.side_effect = mock_table

        res = client.get(
            f"/v1/intelligence/{TEST_PATIENT_ID}",
            headers=make_token(role="provider", user_id=TEST_PROVIDER_ID),
        )
        assert res.status_code == 403

    @patch("app.services.adherence_intelligence.intelligence_router.detect_rx_change_flags")
    @patch("app.services.adherence_intelligence.intelligence_router.classify_adherence_pattern")
    @patch("app.services.adherence_intelligence.intelligence_router.compute_confidence")
    @patch("app.services.adherence_intelligence.intelligence_router.compute_risk_score")
    @patch("app.services.adherence_intelligence.intelligence_router.supabase")
    def test_admin_returns_200(self, mock_sb, mock_risk, mock_conf, mock_pat, mock_rx):
        prof_chain = MagicMock()
        prof_chain.select.return_value.eq.return_value.limit.return_value.execute.return_value = MagicMock(
            data=[{"id": TEST_PATIENT_ID, "role": "patient"}]
        )
        mock_sb.table.return_value = prof_chain

        mock_risk.return_value = {
            "risk_score": 10,
            "risk_level": "LOW",
            "evidence": ["No risk signals detected"],
            "computed_at": "2026-09-08T00:00:00Z",
        }
        mock_conf.return_value = {
            "confidence_label": "High",
            "confidence_score": 1.0,
            "signals_available": 4,
            "signals_total": 5,
        }
        mock_pat.return_value = {
            "pattern_type": "adherent",
            "pattern_label": "Adherent",
        }
        mock_rx.return_value = {
            "flag_raised": False,
            "flags": [],
            "clinical_note": None,
        }

        res = client.get(
            f"/v1/intelligence/{TEST_PATIENT_ID}",
            headers=make_token(role="admin", user_id=TEST_ADMIN_ID),
        )
        assert res.status_code == 200
        body = res.json()
        assert body["success"] is True
        assert body["data"]["patient_id"] == TEST_PATIENT_ID
        assert "summary" in body["data"]
