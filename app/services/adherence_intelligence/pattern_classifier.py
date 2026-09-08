"""Adherence pattern classifier — identifies WHY a patient is non-adherent."""
import asyncio
import logging
from collections import Counter
from datetime import datetime, timedelta, timezone

from app.db.supabase import supabase

logger = logging.getLogger(__name__)

_WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


async def classify_adherence_pattern(patient_id: str, lookback_days: int = 30) -> dict:
    """Classify a patient's adherence pattern over the lookback window.

    Priority order:
      1. complete_discontinuation — no logs for ≥14 days
      2. temporal               — >60% misses on same 1-2 weekdays
      3. temporary_irregularity — one gap of 2-5 days, overall ≥75% adherent
      4. intermittent           — ≥3 misses, no weekday cluster, <80% adherent
      5. adherent               — default pass
      6. no_data                — no logs at all
    """
    cutoff = (datetime.now(timezone.utc) - timedelta(days=lookback_days)).isoformat()
    now = datetime.now(timezone.utc)

    res = await asyncio.to_thread(
        lambda: supabase.table("adherence")
        .select("status, scheduled_utc")
        .eq("user_id", patient_id)
        .gte("scheduled_utc", cutoff)
        .order("scheduled_utc")
        .execute()
    )
    logs = res.data or []

    if not logs:
        return {
            "pattern_type": "no_data",
            "pattern_label": "No data",
            "description": "No dose logs found in the lookback period.",
            "lookback_days": lookback_days,
            "total_doses_scheduled": 0,
            "total_doses_missed": 0,
            "miss_rate": 0.0,
            "longest_gap_days": 0,
            "clustered_on_days": [],
            "days_since_last_log": -1,
        }

    total = len(logs)
    missed_logs = [log for log in logs if log["status"] == "missed"]
    missed = len(missed_logs)
    miss_rate = missed / total if total else 0.0
    adherence_rate = 1.0 - miss_rate

    last_log_date = datetime.fromisoformat(logs[-1]["scheduled_utc"].replace("Z", "+00:00"))
    days_since_last = (now - last_log_date).days

    # Longest gap between consecutive scheduled doses
    dates = sorted(datetime.fromisoformat(log["scheduled_utc"].replace("Z", "+00:00")) for log in logs)
    longest_gap = 0
    for i in range(1, len(dates)):
        gap = (dates[i] - dates[i - 1]).days
        if gap > longest_gap:
            longest_gap = gap

    # Weekday cluster for missed doses
    miss_weekdays = [datetime.fromisoformat(log["scheduled_utc"].replace("Z", "+00:00")).weekday() for log in missed_logs]
    weekday_counts = Counter(miss_weekdays)
    clustered_days: list[str] = []
    top2_count = sum(c for _, c in weekday_counts.most_common(2))
    if missed > 0 and top2_count / missed > 0.60:
        clustered_days = [_WEEKDAYS[wd] for wd, _ in weekday_counts.most_common(2) if weekday_counts[wd] > 0]

    # Pattern classification (priority order)
    if days_since_last >= 14:
        ptype, label, desc = (
            "complete_discontinuation",
            "Stopped taking medication",
            f"No doses logged in {days_since_last} days — possible complete discontinuation.",
        )
    elif clustered_days and missed >= 2:
        ptype, label, desc = (
            "temporal",
            "Weekday pattern",
            f"Misses cluster on {' and '.join(clustered_days)} — possible schedule or lifestyle conflict.",
        )
    elif missed >= 1 and 2 <= longest_gap <= 5 and adherence_rate >= 0.75:
        # Check it's one continuous gap
        gaps = [(dates[i] - dates[i - 1]).days for i in range(1, len(dates))]
        multi_gap = sum(1 for g in gaps if g >= 2)
        if multi_gap == 1:
            ptype, label, desc = (
                "temporary_irregularity",
                "Temporary gap",
                f"Single gap of {longest_gap} days with {adherence_rate:.0%} overall adherence — likely a temporary disruption.",
            )
        else:
            ptype, label, desc = (
                "intermittent",
                "Intermittent non-adherence",
                f"Scattered misses ({missed} total) with {adherence_rate:.0%} adherence — no clear pattern.",
            )
    elif missed >= 3 and not clustered_days and adherence_rate < 0.80:
        ptype, label, desc = (
            "intermittent",
            "Intermittent non-adherence",
            f"{missed} missed doses with no consistent weekday pattern — intermittent non-adherence.",
        )
    else:
        ptype, label, desc = (
            "adherent",
            "Adherent",
            f"Patient is {adherence_rate:.0%} adherent over the last {lookback_days} days.",
        )

    return {
        "pattern_type": ptype,
        "pattern_label": label,
        "description": desc,
        "lookback_days": lookback_days,
        "total_doses_scheduled": total,
        "total_doses_missed": missed,
        "miss_rate": round(miss_rate, 3),
        "longest_gap_days": longest_gap,
        "clustered_on_days": clustered_days,
        "days_since_last_log": days_since_last,
    }
