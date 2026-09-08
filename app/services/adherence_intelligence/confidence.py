"""Confidence scorer — measures how many signal sources are present for a patient."""
import asyncio
import logging
from datetime import datetime, timedelta, timezone

from app.db.supabase import supabase

logger = logging.getLogger(__name__)

_LABELS = {1.0: "High", 0.8: "Moderate", 0.6: "Moderate", 0.4: "Low", 0.2: "Low", 0.0: "Insufficient data"}


def _label(score: float) -> str:
    # Round to nearest 0.2 bucket
    bucket = round(score * 5) / 5
    return _LABELS.get(bucket, "Low")


async def compute_confidence(patient_id: str, lookback_days: int = 7) -> dict:
    """Score confidence in the risk assessment based on available signal sources.

    Five sources checked:
      1. dose_logs       — adherence rows in lookback window
      2. side_effect_reports — feedback rows in lookback window
      3. adherence_stats — weekly report exists
      4. snooze_behavior — not available in schema; always missing
      5. medication_history — at least one medicine record

    Reducers (each drops score by 0.2):
      - Most recent dose log older than 14 days
      - Only 1 medication tracked
      - Patient profile created < 7 days ago
    """
    cutoff = (datetime.now(timezone.utc) - timedelta(days=lookback_days)).isoformat()
    now = datetime.now(timezone.utc)

    adh_res, fb_res, rep_res, med_res, prof_res = await asyncio.gather(
        asyncio.to_thread(lambda: supabase.table("adherence").select("scheduled_utc").eq("user_id", patient_id).gte("scheduled_utc", cutoff).limit(1).execute()),
        asyncio.to_thread(lambda: supabase.table("feedback").select("id").eq("user_id", patient_id).gte("created_at", cutoff).limit(1).execute()),
        asyncio.to_thread(lambda: supabase.table("reports").select("id").eq("user_id", patient_id).eq("period_type", "weekly").limit(1).execute()),
        asyncio.to_thread(lambda: supabase.table("medicines").select("id, created_at").eq("user_id", patient_id).execute()),
        asyncio.to_thread(lambda: supabase.table("profiles").select("created_at").eq("id", patient_id).limit(1).execute()),
    )

    # Check most recent dose (for reducer)
    recent_adh = await asyncio.to_thread(
        lambda: supabase.table("adherence").select("scheduled_utc").eq("user_id", patient_id).order("scheduled_utc", desc=True).limit(1).execute()
    )

    signals_present = []
    signals_missing = []

    if adh_res.data:
        signals_present.append("dose_logs")
    else:
        signals_missing.append("dose_logs")

    if fb_res.data:
        signals_present.append("side_effect_reports")
    else:
        signals_missing.append("side_effect_reports")

    if rep_res.data:
        signals_present.append("adherence_stats")
    else:
        signals_missing.append("adherence_stats")

    # ponytail: snooze_behavior not in schema — always missing
    signals_missing.append("snooze_behavior")

    if med_res.data:
        signals_present.append("medication_history")
    else:
        signals_missing.append("medication_history")

    raw_score = len(signals_present) / 5
    reducers: list[str] = []

    # Reducer: most recent dose > 14 days old
    if recent_adh.data:
        last_date = datetime.fromisoformat(recent_adh.data[0]["scheduled_utc"].replace("Z", "+00:00"))
        if (now - last_date).days > 14:
            reducers.append("Most recent dose log is older than 14 days")
            raw_score = max(0.0, raw_score - 0.2)

    # Reducer: only 1 medication
    if len(med_res.data or []) == 1:
        reducers.append("Only 1 medication being tracked")
        raw_score = max(0.0, raw_score - 0.2)

    # Reducer: account < 7 days old
    if prof_res.data:
        created = datetime.fromisoformat(prof_res.data[0]["created_at"].replace("Z", "+00:00"))
        if (now - created).days < 7:
            reducers.append("Patient account is less than 7 days old")
            raw_score = max(0.0, raw_score - 0.2)

    label = _label(raw_score)
    note = (
        f"Confidence is {label.lower()} based on {len(signals_present)} of 5 signal sources"
        + (f"; reduced by: {', '.join(reducers)}" if reducers else "")
        + "."
    )

    return {
        "confidence_label": label,
        "confidence_score": round(raw_score, 2),
        "signals_available": len(signals_present),
        "signals_total": 5,
        "signals_present": signals_present,
        "signals_missing": signals_missing,
        "reducers_applied": reducers,
        "note": note,
    }
