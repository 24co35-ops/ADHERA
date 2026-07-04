"""
engine.py - Insights Engine

Orchestrates data fetching and detector execution for a given patient,
then persists newly detected flags to the patient_flags table.
"""

import logging
from datetime import datetime, timedelta, timezone

from app.db.supabase import supabase
from app.insights.detectors import (
    detect_dose_drift,
    detect_post_side_effect_drop,
    detect_silent_inactivity,
    detect_weekend_pattern,
)

logger = logging.getLogger("adhera.insights")


def run_insights_for_patient(user_id: str) -> list[dict]:
    """
    Run all four insight detectors for a patient and persist new flags.

    Fetches 30-day adherence/feedback windows and active medicine count,
    calls detectors, deduplicates against existing unresolved flags,
    inserts novel flags into patient_flags, and returns the inserted list.
    """
    d30 = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()

    # 1. Adherence rows — last 30 days
    try:
        adh_res = supabase.table("adherence").select("*").eq("user_id", user_id).gte("scheduled_utc", d30).execute()
        adherence_rows = adh_res.data or []
    except Exception as e:
        logger.error("insights: failed to fetch adherence for %s: %s", user_id, e)
        adherence_rows = []

    # 2. Feedback rows — last 30 days
    try:
        fb_res = supabase.table("feedback").select("*").eq("user_id", user_id).gte("occurred_at", d30).execute()
        feedback_rows = fb_res.data or []
    except Exception as e:
        logger.error("insights: failed to fetch feedback for %s: %s", user_id, e)
        feedback_rows = []

    # 3. Active medicine count
    try:
        med_res = supabase.table("medicines").select("id").eq("user_id", user_id).eq("is_active", True).execute()
        active_medicine_count = len(med_res.data or [])
    except Exception as e:
        logger.error("insights: failed to fetch medicines for %s: %s", user_id, e)
        active_medicine_count = 0

    # 4. Most recent adherence row
    try:
        latest_res = (
            supabase.table("adherence")
            .select("scheduled_utc, user_id")
            .eq("user_id", user_id)
            .order("scheduled_utc", desc=True)
            .limit(1)
            .execute()
        )
        latest_adherence_row = (latest_res.data or [None])[0]
    except Exception as e:
        logger.error("insights: failed to fetch latest adherence for %s: %s", user_id, e)
        latest_adherence_row = None

    # 5. Existing unresolved flag types for deduplication
    try:
        existing_res = (
            supabase.table("patient_flags")
            .select("flag_type")
            .eq("user_id", user_id)
            .is_("resolved_at", "null")
            .execute()
        )
        existing_flag_types = {row["flag_type"] for row in (existing_res.data or [])}
    except Exception as e:
        logger.warning("insights: failed to fetch existing flags for %s, proceeding without dedup: %s", user_id, e)
        existing_flag_types = set()

    # 6. Run detectors
    candidate_flags: list[dict] = []

    drift = detect_dose_drift(adherence_rows)
    if drift:
        candidate_flags.append(drift)

    weekend = detect_weekend_pattern(adherence_rows)
    if weekend:
        candidate_flags.append(weekend)

    side_effect_flags = detect_post_side_effect_drop(feedback_rows, adherence_rows)
    candidate_flags.extend(side_effect_flags)

    inactivity = detect_silent_inactivity(active_medicine_count, latest_adherence_row)
    if inactivity:
        candidate_flags.append(inactivity)

    # 7. Insert novel (non-duplicate) flags
    inserted: list[dict] = []
    for flag in candidate_flags:
        flag_type = flag.get("flag_type")
        if flag_type in existing_flag_types:
            logger.debug("insights: skipping duplicate flag %s for %s", flag_type, user_id)
            continue

        row = {
            "user_id": user_id,
            "flag_type": flag_type,
            "severity": flag.get("severity"),
            "details": flag.get("details", {}),
        }
        if flag.get("related_medicine_id"):
            row["related_medicine_id"] = flag["related_medicine_id"]
        if flag.get("related_feedback_id"):
            row["related_feedback_id"] = flag["related_feedback_id"]

        try:
            ins_res = supabase.table("patient_flags").insert(row).execute()
            if ins_res.data:
                inserted.append(ins_res.data[0])
                existing_flag_types.add(flag_type)  # prevent double-insert within same run
        except Exception as e:
            logger.error("insights: failed to insert flag %s for %s: %s", flag_type, user_id, e)

    logger.info("insights: %d new flags inserted for %s", len(inserted), user_id)
    return inserted
