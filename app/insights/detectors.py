"""
detectors.py - Patient Adherence Insights Detectors

This module implements algorithms for detecting invisible adherence failure signals.
Unlike simple adherence percentages, these detectors highlight patterns:
1. dose_drift: Catching progressive shift in timing before full dropout.
2. weekend_pattern: Catching routine-dependent forgetting on Saturdays and Sundays.
3. post_side_effect_drop: Catching intentional drug discontinuation due to side effects.
4. silent_inactivity: Catching disengagement where no logging/missed records occur.
"""

from datetime import datetime, timezone, timedelta

def _parse_dt(dt_val) -> datetime:
    """Parse string/datetime to a timezone-aware UTC datetime."""
    if isinstance(dt_val, str):
        if dt_val.endswith("Z"):
            dt_val = dt_val[:-1] + "+00:00"
        dt = datetime.fromisoformat(dt_val)
    else:
        dt = dt_val
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)

def detect_dose_drift(adherence_rows: list, threshold_minutes: float = 45.0) -> dict | None:
    """
    Dose Drift Detector
    Designed to catch early-warning drift in dose administration timing.
    Triggers when late-stage doses are taken significantly later than early-stage doses.
    """
    taken_rows = [r for r in adherence_rows if r.get("status") == "taken"]
    if not taken_rows:
        return None

    # Sort chronologically by scheduled time
    sorted_rows = sorted(taken_rows, key=lambda r: _parse_dt(r["scheduled_utc"]))
    last_seven = sorted_rows[-7:]
    
    if len(last_seven) < 5:
        return None

    delays = []
    for r in last_seven:
        scheduled = _parse_dt(r["scheduled_utc"])
        outcome = _parse_dt(r.get("outcome_utc") or r["scheduled_utc"])
        delay = (outcome - scheduled).total_seconds() / 60.0
        delays.append(delay)

    mid = len(last_seven) // 2
    early_delays = delays[:mid]
    late_delays = delays[-mid:]

    early_avg = sum(early_delays) / len(early_delays)
    late_avg = sum(late_delays) / len(late_delays)

    if late_avg - early_avg > threshold_minutes:
        user_id = last_seven[0].get("user_id")
        return {
            "flag_type": "dose_drift",
            "user_id": user_id,
            "severity": 2,
            "details": {
                "early_avg_delay_min": round(early_avg, 1),
                "late_avg_delay_min": round(late_avg, 1),
                "trend": "worsening"
            }
        }
    return None

def detect_weekend_pattern(adherence_rows: list, min_occurrences: int = 3) -> dict | None:
    """
    Weekend Pattern Detector
    Designed to catch routine-dependent forgetting during Saturdays and Sundays.
    Triggers when more than half of the patient's missed doses occur on weekends.
    """
    missed_rows = [r for r in adherence_rows if r.get("status") == "missed"]
    if len(missed_rows) < min_occurrences:
        return None

    weekend_misses = 0
    weekday_misses = 0

    for r in missed_rows:
        dt = _parse_dt(r["scheduled_utc"])
        if dt.weekday() in (5, 6):  # Saturday, Sunday
            weekend_misses += 1
        else:
            weekday_misses += 1

    total_misses = weekend_misses + weekday_misses
    weekend_ratio = weekend_misses / total_misses if total_misses > 0 else 0.0

    if weekend_ratio > 0.5 and weekend_misses >= min_occurrences:
        user_id = missed_rows[0].get("user_id")
        return {
            "flag_type": "weekend_pattern",
            "user_id": user_id,
            "severity": 1,
            "details": {
                "weekend_misses": weekend_misses,
                "weekday_misses": weekday_misses,
                "weekend_ratio": round(weekend_ratio, 2)
            }
        }
    return None

def detect_post_side_effect_drop(feedback_rows: list, adherence_rows: list, window_days: int = 5) -> list[dict]:
    """
    Post Side-Effect Drop Detector
    Designed to catch intentional drug discontinuation due to side effects.
    Triggers when adherence drops by >= 30% in the window after a moderate/severe side-effect log.
    """
    flags = []
    eligible_feedback = [f for f in feedback_rows if f.get("severity", 0) >= 2]

    for fb in eligible_feedback:
        fb_time = _parse_dt(fb["occurred_at"])
        user_id = fb.get("user_id")
        medicine_id = fb.get("medicine_id")
        fb_id = fb.get("id")

        before_start = fb_time - timedelta(days=window_days)
        after_end = fb_time + timedelta(days=window_days)

        before_window_rows = []
        after_window_rows = []

        for r in adherence_rows:
            r_time = _parse_dt(r["scheduled_utc"])
            if before_start <= r_time <= fb_time:
                before_window_rows.append(r)
            elif fb_time < r_time <= after_end:
                after_window_rows.append(r)

        if len(before_window_rows) < 2 or len(after_window_rows) < 2:
            continue

        taken_before = len([x for x in before_window_rows if x.get("status") == "taken"])
        rate_before = (taken_before / len(before_window_rows)) * 100.0

        taken_after = len([x for x in after_window_rows if x.get("status") == "taken"])
        rate_after = (taken_after / len(after_window_rows)) * 100.0

        if rate_before - rate_after >= 30.0:
            desc = fb.get("description") or ""
            flags.append({
                "flag_type": "post_side_effect_drop",
                "user_id": user_id,
                "severity": 3,
                "related_feedback_id": fb_id,
                "related_medicine_id": medicine_id,
                "details": {
                    "adherence_before_pct": round(rate_before, 1),
                    "adherence_after_pct": round(rate_after, 1),
                    "side_effect_severity": fb.get("severity"),
                    "side_effect_desc": desc[:100]
                }
            })

    return flags

def detect_silent_inactivity(active_medicine_count: int, latest_adherence_row: dict | None, inactivity_threshold_days: float = 5.0) -> dict | None:
    """
    Silent Inactivity Detector
    Designed to catch total disengagement leaving no log or missed record.
    Triggers when a patient has active medications but hasn't logged anything for >= inactivity_threshold_days.
    """
    if active_medicine_count == 0:
        return None

    user_id = latest_adherence_row.get("user_id") if latest_adherence_row else None

    if latest_adherence_row is None:
        return {
            "flag_type": "silent_inactivity",
            "user_id": user_id,
            "severity": 4,
            "details": {
                "days_since_last_log": None,
                "active_medicine_count": active_medicine_count
            }
        }

    last_log_time = _parse_dt(latest_adherence_row["scheduled_utc"])
    now = datetime.now(timezone.utc)
    diff_days = (now - last_log_time).total_seconds() / (24 * 3600)

    if diff_days >= inactivity_threshold_days:
        return {
            "flag_type": "silent_inactivity",
            "user_id": user_id,
            "severity": 4,
            "details": {
                "days_since_last_log": round(diff_days, 1),
                "active_medicine_count": active_medicine_count
            }
        }

    return None
