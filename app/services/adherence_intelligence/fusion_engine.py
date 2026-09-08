"""Signal fusion engine — computes a rule-based risk score from dose/feedback/adherence data."""
import asyncio
import logging
from datetime import datetime, timedelta, timezone

from app.db.supabase import supabase

logger = logging.getLogger(__name__)

_CUTOFF = lambda days: (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()  # noqa: E731


async def compute_risk_score(patient_id: str) -> dict:
    """Return a 0-100 risk score with evidence list for a single patient.

    Rules (additive, capped at 100):
      +25 if ≥3 missed doses in last 7 days
      +20 if weekly_rate < 0.70 (from latest weekly report)
      +15 if any feedback severity ≥ 3 in last 7 days
      +10 if ≥3 feedback reports in last 7 days
      +10 if current streak is 0 (streak broken)
    Snooze signals omitted: schema has no snooze_count column.
    """
    cutoff = _CUTOFF(7)
    now_iso = datetime.now(timezone.utc).isoformat()

    # Fetch concurrently — all independent queries
    adh_res, fb_res, report_res = await asyncio.gather(
        asyncio.to_thread(
            lambda: supabase.table("adherence")
            .select("status, scheduled_utc, outcome_utc")
            .eq("user_id", patient_id)
            .gte("scheduled_utc", cutoff)
            .execute()
        ),
        asyncio.to_thread(
            lambda: supabase.table("feedback")
            .select("severity, created_at")
            .eq("user_id", patient_id)
            .gte("created_at", cutoff)
            .execute()
        ),
        asyncio.to_thread(
            lambda: supabase.table("reports")
            .select("adherence_rate, period_type")
            .eq("user_id", patient_id)
            .eq("period_type", "weekly")
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        ),
    )

    dose_logs = adh_res.data or []
    feedbacks = fb_res.data or []
    reports = report_res.data or []

    if not dose_logs:
        return {
            "patient_id": patient_id,
            "risk_score": 0,
            "risk_level": "LOW",
            "evidence": ["insufficient_data: no dose logs in last 7 days"],
            "computed_at": now_iso,
        }

    score = 0
    evidence: list[str] = []

    # Rule 1: ≥3 missed doses
    missed = sum(1 for d in dose_logs if d["status"] == "missed")
    if missed >= 3:
        score += 25
        evidence.append(f"{missed} missed doses in the last 7 days")

    # Rule 2: weekly adherence rate < 70%
    weekly_rate: float | None = None
    if reports:
        weekly_rate = float(reports[0]["adherence_rate"]) / 100
        if weekly_rate < 0.70:
            score += 20
            evidence.append(f"Weekly adherence rate is {weekly_rate:.0%} (below 70%)")

    # Data inconsistency flag: all taken but rate is low
    if weekly_rate is not None and weekly_rate < 0.70 and missed == 0 and dose_logs:
        evidence.append("Data inconsistency: all recent doses marked taken but weekly rate is low")

    # Rule 3: any feedback severity ≥ 3
    severe_fb = [f for f in feedbacks if f["severity"] >= 3]
    if severe_fb:
        score += 15
        evidence.append(f"Side-effect severity ≥3 reported {len(severe_fb)} time(s) this week")

    # Rule 4: ≥3 feedback reports
    if len(feedbacks) >= 3:
        score += 10
        evidence.append(f"{len(feedbacks)} side-effect reports in the last 7 days")

    # Rule 5: streak broken (no taken dose today or yesterday)
    taken_days = {d["scheduled_utc"][:10] for d in dose_logs if d["status"] == "taken"}
    yesterday = (datetime.now(timezone.utc) - timedelta(days=1)).strftime("%Y-%m-%d")
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    if today not in taken_days and yesterday not in taken_days:
        score += 10
        evidence.append("No doses taken in the last 2 days — streak may be broken")

    score = min(score, 100)
    risk_level = "HIGH" if score >= 50 else ("MODERATE" if score >= 25 else "LOW")

    return {
        "patient_id": patient_id,
        "risk_score": score,
        "risk_level": risk_level,
        "evidence": evidence or ["No risk signals detected"],
        "computed_at": now_iso,
    }
