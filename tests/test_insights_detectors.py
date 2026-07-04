"""
Unit tests for app.insights.detectors - dose drift, weekend pattern,
post side-effect drop, and silent inactivity detectors.
"""

import pytest
from datetime import datetime, timezone, timedelta
from app.insights.detectors import (
    detect_dose_drift,
    detect_weekend_pattern,
    detect_post_side_effect_drop,
    detect_silent_inactivity,
)

TEST_USER = "user-123"
TEST_MED = "med-456"
TEST_FEEDBACK = "fb-789"


class TestDoseDrift:
    """Unit tests for detect_dose_drift."""

    def test_dose_drift_detected(self):
        # 7 taken rows. Early stage averages 10 min delay, late stage averages 60 min delay.
        # Difference = 50 min, which is > threshold_minutes=45.
        base = datetime(2025, 1, 1, 10, 0, 0, tzinfo=timezone.utc)
        rows = [
            {"status": "taken", "scheduled_utc": (base + timedelta(days=i)).isoformat(),
             "outcome_utc": (base + timedelta(days=i, minutes=10)).isoformat(), "user_id": TEST_USER}
            for i in range(4)
        ] + [
            {"status": "taken", "scheduled_utc": (base + timedelta(days=i)).isoformat(),
             "outcome_utc": (base + timedelta(days=i, minutes=60)).isoformat(), "user_id": TEST_USER}
            for i in range(4, 7)
        ]
        
        flag = detect_dose_drift(rows, threshold_minutes=45)
        assert flag is not None
        assert flag["flag_type"] == "dose_drift"
        assert flag["user_id"] == TEST_USER
        assert flag["severity"] == 2
        assert flag["details"]["early_avg_delay_min"] == 10.0
        assert flag["details"]["late_avg_delay_min"] == 60.0
        assert flag["details"]["trend"] == "worsening"

    def test_dose_drift_no_flag(self):
        # Constant delay of 15 min. No drift.
        base = datetime(2025, 1, 1, 10, 0, 0, tzinfo=timezone.utc)
        rows = [
            {"status": "taken", "scheduled_utc": (base + timedelta(days=i)).isoformat(),
             "outcome_utc": (base + timedelta(days=i, minutes=15)).isoformat(), "user_id": TEST_USER}
            for i in range(7)
        ]
        flag = detect_dose_drift(rows, threshold_minutes=45)
        assert flag is None

    def test_dose_drift_insufficient_data(self):
        # Fewer than 5 taken rows
        base = datetime(2025, 1, 1, 10, 0, 0, tzinfo=timezone.utc)
        rows = [
            {"status": "taken", "scheduled_utc": (base + timedelta(days=i)).isoformat(),
             "outcome_utc": (base + timedelta(days=i, minutes=10)).isoformat(), "user_id": TEST_USER}
            for i in range(4)
        ]
        flag = detect_dose_drift(rows, threshold_minutes=45)
        assert flag is None


class TestWeekendPattern:
    """Unit tests for detect_weekend_pattern."""

    def test_weekend_pattern_detected(self):
        # Sat, Sun, Sat misses. ratio = 3 / 4 = 0.75 > 0.5. Weekend misses = 3 >= min_occurrences=3.
        base_sat = datetime(2025, 1, 4, 10, 0, 0, tzinfo=timezone.utc)  # Saturday
        base_sun = datetime(2025, 1, 5, 10, 0, 0, tzinfo=timezone.utc)  # Sunday
        base_mon = datetime(2025, 1, 6, 10, 0, 0, tzinfo=timezone.utc)  # Monday

        rows = [
            {"status": "missed", "scheduled_utc": base_sat.isoformat(), "user_id": TEST_USER},
            {"status": "missed", "scheduled_utc": base_sun.isoformat(), "user_id": TEST_USER},
            {"status": "missed", "scheduled_utc": (base_sat + timedelta(weeks=1)).isoformat(), "user_id": TEST_USER},
            {"status": "missed", "scheduled_utc": base_mon.isoformat(), "user_id": TEST_USER},
        ]
        flag = detect_weekend_pattern(rows, min_occurrences=3)
        assert flag is not None
        assert flag["flag_type"] == "weekend_pattern"
        assert flag["user_id"] == TEST_USER
        assert flag["severity"] == 1
        assert flag["details"]["weekend_misses"] == 3
        assert flag["details"]["weekday_misses"] == 1
        assert flag["details"]["weekend_ratio"] == 0.75

    def test_weekend_pattern_no_flag(self):
        # Ratio of weekend misses is <= 0.5
        base_sat = datetime(2025, 1, 4, 10, 0, 0, tzinfo=timezone.utc)
        base_mon = datetime(2025, 1, 6, 10, 0, 0, tzinfo=timezone.utc)
        rows = [
            {"status": "missed", "scheduled_utc": base_sat.isoformat(), "user_id": TEST_USER},
            {"status": "missed", "scheduled_utc": base_mon.isoformat(), "user_id": TEST_USER},
            {"status": "missed", "scheduled_utc": (base_mon + timedelta(days=1)).isoformat(), "user_id": TEST_USER},
            {"status": "missed", "scheduled_utc": (base_mon + timedelta(days=2)).isoformat(), "user_id": TEST_USER},
        ]
        flag = detect_weekend_pattern(rows, min_occurrences=3)
        assert flag is None

    def test_weekend_pattern_insufficient_data(self):
        # Fewer than min_occurrences total missed
        base_sat = datetime(2025, 1, 4, 10, 0, 0, tzinfo=timezone.utc)
        rows = [
            {"status": "missed", "scheduled_utc": base_sat.isoformat(), "user_id": TEST_USER},
            {"status": "missed", "scheduled_utc": (base_sat + timedelta(weeks=1)).isoformat(), "user_id": TEST_USER},
        ]
        flag = detect_weekend_pattern(rows, min_occurrences=3)
        assert flag is None


class TestPostSideEffectDrop:
    """Unit tests for detect_post_side_effect_drop."""

    def test_post_side_effect_drop_detected(self):
        # Feedback occurred at Jan 10.
        # Before window (Jan 5 - Jan 10): 3 scheduled, 3 taken -> 100%
        # After window (Jan 10 - Jan 15): 3 scheduled, 1 taken -> 33.3%
        # Diff = 66.7% >= 30%.
        fb_time = datetime(2025, 1, 10, 12, 0, 0, tzinfo=timezone.utc)
        feedback = [
            {
                "id": TEST_FEEDBACK,
                "user_id": TEST_USER,
                "medicine_id": TEST_MED,
                "severity": 3,
                "occurred_at": fb_time.isoformat(),
                "description": "Severe headache after dose",
            }
        ]
        adherence = [
            # Before window
            {"status": "taken", "scheduled_utc": (fb_time - timedelta(days=4)).isoformat(), "user_id": TEST_USER},
            {"status": "taken", "scheduled_utc": (fb_time - timedelta(days=2)).isoformat(), "user_id": TEST_USER},
            {"status": "taken", "scheduled_utc": (fb_time - timedelta(hours=2)).isoformat(), "user_id": TEST_USER},
            # After window
            {"status": "taken", "scheduled_utc": (fb_time + timedelta(days=1)).isoformat(), "user_id": TEST_USER},
            {"status": "missed", "scheduled_utc": (fb_time + timedelta(days=3)).isoformat(), "user_id": TEST_USER},
            {"status": "missed", "scheduled_utc": (fb_time + timedelta(days=4)).isoformat(), "user_id": TEST_USER},
        ]
        
        flags = detect_post_side_effect_drop(feedback, adherence, window_days=5)
        assert len(flags) == 1
        flag = flags[0]
        assert flag["flag_type"] == "post_side_effect_drop"
        assert flag["user_id"] == TEST_USER
        assert flag["severity"] == 3
        assert flag["related_feedback_id"] == TEST_FEEDBACK
        assert flag["related_medicine_id"] == TEST_MED
        assert flag["details"]["adherence_before_pct"] == 100.0
        assert flag["details"]["adherence_after_pct"] == 33.3
        assert flag["details"]["side_effect_severity"] == 3
        assert flag["details"]["side_effect_desc"] == "Severe headache after dose"

    def test_post_side_effect_drop_no_flag(self):
        # Adherence drop of 10% (under 30%)
        fb_time = datetime(2025, 1, 10, 12, 0, 0, tzinfo=timezone.utc)
        feedback = [
            {
                "id": TEST_FEEDBACK,
                "user_id": TEST_USER,
                "medicine_id": TEST_MED,
                "severity": 2,
                "occurred_at": fb_time.isoformat(),
                "description": "Nausea",
            }
        ]
        adherence = [
            {"status": "taken", "scheduled_utc": (fb_time - timedelta(days=1)).isoformat(), "user_id": TEST_USER},
            {"status": "taken", "scheduled_utc": (fb_time - timedelta(days=2)).isoformat(), "user_id": TEST_USER},
            {"status": "taken", "scheduled_utc": (fb_time + timedelta(days=1)).isoformat(), "user_id": TEST_USER},
            {"status": "taken", "scheduled_utc": (fb_time + timedelta(days=2)).isoformat(), "user_id": TEST_USER},
        ]
        flags = detect_post_side_effect_drop(feedback, adherence, window_days=5)
        assert len(flags) == 0

    def test_post_side_effect_drop_insufficient_data(self):
        # Fewer than 2 rows in one of the windows
        fb_time = datetime(2025, 1, 10, 12, 0, 0, tzinfo=timezone.utc)
        feedback = [
            {
                "id": TEST_FEEDBACK,
                "user_id": TEST_USER,
                "medicine_id": TEST_MED,
                "severity": 2,
                "occurred_at": fb_time.isoformat(),
                "description": "Nausea",
            }
        ]
        adherence = [
            {"status": "taken", "scheduled_utc": (fb_time - timedelta(days=1)).isoformat(), "user_id": TEST_USER},
            # Only one row in before window, one in after window
            {"status": "taken", "scheduled_utc": (fb_time + timedelta(days=1)).isoformat(), "user_id": TEST_USER},
        ]
        flags = detect_post_side_effect_drop(feedback, adherence, window_days=5)
        assert len(flags) == 0


class TestSilentInactivity:
    """Unit tests for detect_silent_inactivity."""

    def test_silent_inactivity_no_active_medicines(self):
        flag = detect_silent_inactivity(active_medicine_count=0, latest_adherence_row=None)
        assert flag is None

    def test_silent_inactivity_no_log_history(self):
        # Active medicines > 0 but no log history ever
        flag = detect_silent_inactivity(active_medicine_count=2, latest_adherence_row=None)
        assert flag is not None
        assert flag["flag_type"] == "silent_inactivity"
        assert flag["severity"] == 4
        assert flag["details"]["days_since_last_log"] is None
        assert flag["details"]["active_medicine_count"] == 2

    def test_silent_inactivity_threshold_exceeded(self):
        # Last log was 6 days ago, threshold is 5 days
        now = datetime.now(timezone.utc)
        last_log = {"scheduled_utc": (now - timedelta(days=6)).isoformat(), "user_id": TEST_USER}
        flag = detect_silent_inactivity(active_medicine_count=1, latest_adherence_row=last_log, inactivity_threshold_days=5)
        assert flag is not None
        assert flag["flag_type"] == "silent_inactivity"
        assert flag["user_id"] == TEST_USER
        assert flag["severity"] == 4
        assert flag["details"]["days_since_last_log"] >= 6.0
        assert flag["details"]["active_medicine_count"] == 1

    def test_silent_inactivity_no_flag(self):
        # Last log was 2 days ago, threshold is 5 days
        now = datetime.now(timezone.utc)
        last_log = {"scheduled_utc": (now - timedelta(days=2)).isoformat(), "user_id": TEST_USER}
        flag = detect_silent_inactivity(active_medicine_count=1, latest_adherence_row=last_log, inactivity_threshold_days=5)
        assert flag is None
