import logging
from datetime import datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request

from app.auth.dependencies import get_current_user
from app.core.rate_limit import limiter
from app.core.responses import SuccessResponse
from app.db.supabase import supabase
from app.insights.engine import run_insights_for_patient

logger = logging.getLogger("adhera.doses")
router = APIRouter()

def get_scheduled_utc_for_today(reminder: dict) -> str:
    profile_res = supabase.table("profiles").select("timezone").eq("id", reminder["user_id"]).execute()
    user_tz_str = "UTC"
    if profile_res.data:
        user_tz_str = profile_res.data[0].get("timezone") or "UTC"

    try:
        user_tz = ZoneInfo(user_tz_str)
    except Exception:
        user_tz = ZoneInfo("UTC")

    now_local = datetime.now(user_tz)
    today_date = now_local.date()
    t = time.fromisoformat(reminder["dose_time_utc"])
    today_utc = datetime.now(timezone.utc).date()

    for offset in [-1, 0, 1]:
        d_utc = today_utc + timedelta(days=offset)
        occurrence_utc = datetime.combine(d_utc, t, tzinfo=timezone.utc)
        occurrence_local = occurrence_utc.astimezone(user_tz)
        if occurrence_local.date() == today_date:
            return occurrence_utc.isoformat().replace("+00:00", "Z")

    occurrence_utc = datetime.combine(today_utc, t, tzinfo=timezone.utc)
    return occurrence_utc.isoformat().replace("+00:00", "Z")

@router.post("/{reminder_id}/taken", response_model=SuccessResponse[dict])
@limiter.limit("60/minute")
async def dose_taken(request: Request, reminder_id: str, background_tasks: BackgroundTasks, user: dict = Depends(get_current_user)):
    rem_res = supabase.table("reminders").select("*").eq("id", reminder_id).eq("user_id", user["user_id"]).execute()
    if not rem_res.data:
        raise HTTPException(status_code=404, detail="Reminder not found")
    reminder = rem_res.data[0]
    scheduled_utc = get_scheduled_utc_for_today(reminder)

    try:
        existing = supabase.table("adherence").select("id") \
            .eq("reminder_id", reminder_id).eq("user_id", user["user_id"]) \
            .eq("status", "taken").eq("scheduled_utc", scheduled_utc).execute()
        if existing and isinstance(existing.data, list) and existing.data:
            return SuccessResponse(data=existing.data[0])
    except Exception:
        pass

    res = supabase.table("adherence").insert({
        "reminder_id": reminder_id,
        "user_id": user["user_id"],
        "scheduled_utc": scheduled_utc,
        "status": "taken",
        "outcome_utc": datetime.now(timezone.utc).isoformat()
    }).execute()
    background_tasks.add_task(run_insights_for_patient, user["user_id"])
    return SuccessResponse(data=res.data[0])

@router.post("/{reminder_id}/missed", response_model=SuccessResponse[dict])
@limiter.limit("60/minute")
async def dose_missed(request: Request, reminder_id: str, background_tasks: BackgroundTasks, user: dict = Depends(get_current_user)):
    rem_res = supabase.table("reminders").select("*").eq("id", reminder_id).eq("user_id", user["user_id"]).execute()
    if not rem_res.data:
        raise HTTPException(status_code=404, detail="Reminder not found")
    reminder = rem_res.data[0]
    scheduled_utc = get_scheduled_utc_for_today(reminder)

    try:
        existing = supabase.table("adherence").select("id") \
            .eq("reminder_id", reminder_id).eq("user_id", user["user_id"]) \
            .eq("status", "missed").eq("scheduled_utc", scheduled_utc).execute()
        if existing and isinstance(existing.data, list) and existing.data:
            return SuccessResponse(data=existing.data[0])
    except Exception:
        pass

    res = supabase.table("adherence").insert({
        "reminder_id": reminder_id,
        "user_id": user["user_id"],
        "scheduled_utc": scheduled_utc,
        "status": "missed",
        "outcome_utc": datetime.now(timezone.utc).isoformat()
    }).execute()
    background_tasks.add_task(run_insights_for_patient, user["user_id"])
    return SuccessResponse(data=res.data[0])

@router.post("/{reminder_id}/snooze", response_model=SuccessResponse[dict])
@limiter.limit("60/minute")
async def dose_snooze(request: Request, reminder_id: str, user: dict = Depends(get_current_user)):
    rem_res = supabase.table("reminders").select("*").eq("id", reminder_id).eq("user_id", user["user_id"]).execute()
    if not rem_res.data:
        raise HTTPException(status_code=404, detail="Reminder not found")
    reminder = rem_res.data[0]
    scheduled_utc = get_scheduled_utc_for_today(reminder)

    # Check previous snooze count in snooze_log
    snooze_count = 0
    try:
        snooze_res = (
            supabase.table("snooze_log")
            .select("snooze_count")
            .eq("reminder_id", reminder_id)
            .eq("user_id", user["user_id"])
            .eq("scheduled_utc", scheduled_utc)
            .order("snooze_count", desc=True)
            .limit(1)
            .execute()
        )
        if snooze_res.data and len(snooze_res.data) > 0:
            snooze_count = int(snooze_res.data[0].get("snooze_count", 0))
    except Exception:
        # Fallback to adherence table count if snooze_log query fails
        try:
            today_start_utc = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
            adh_snooze = (
                supabase.table("adherence")
                .select("id")
                .eq("reminder_id", reminder_id)
                .eq("user_id", user["user_id"])
                .eq("status", "snoozed")
                .gte("scheduled_utc", today_start_utc)
                .execute()
            )
            snooze_count = len(adh_snooze.data or [])
        except Exception:
            snooze_count = 0

    if snooze_count >= 3:
        raise HTTPException(status_code=409, detail="Maximum snooze limit (3) reached for this dose.")

    new_count = snooze_count + 1
    # Snooze = reschedule 10 minutes from now
    snoozed_until = (datetime.now(timezone.utc) + timedelta(minutes=10)).isoformat()

    try:
        supabase.table("snooze_log").insert({
            "reminder_id": reminder_id,
            "user_id": user["user_id"],
            "scheduled_utc": scheduled_utc,
            "snoozed_at": datetime.now(timezone.utc).isoformat(),
            "resume_at": snoozed_until,
            "snooze_count": new_count
        }).execute()
    except Exception:
        pass

    adh_data = {"snoozed": True, "snooze_count": new_count, "reminder_id": reminder_id}
    try:
        res = supabase.table("adherence").insert({
            "reminder_id": reminder_id,
            "user_id": user["user_id"],
            "scheduled_utc": scheduled_utc,
            "status": "snoozed",
            "outcome_utc": snoozed_until
        }).execute()
        if res.data:
            adh_data = res.data[0]
    except Exception as adh_err:
        logger.warning("Optional adherence snooze record skipped or constraint unmigrated: %s", adh_err)

    return SuccessResponse(data=adh_data)

@router.get("/upcoming", response_model=SuccessResponse[list])
@limiter.limit("60/minute")
async def doses_upcoming(request: Request, user: dict = Depends(get_current_user)):
    profile_res = supabase.table("profiles").select("timezone").eq("id", user["user_id"]).execute()
    user_tz_str = "UTC"
    if profile_res.data:
        user_tz_str = profile_res.data[0].get("timezone") or "UTC"

    try:
        user_tz = ZoneInfo(user_tz_str)
    except Exception:
        user_tz = ZoneInfo("UTC")

    now_local = datetime.now(user_tz)
    today_date = now_local.date()

    reminders_res = supabase.table("reminders").select("*, medicines(*)").eq("user_id", user["user_id"]).eq("is_active", True).execute()

    start_local = datetime.combine(today_date, time.min, tzinfo=user_tz)
    end_local = datetime.combine(today_date, time.max, tzinfo=user_tz)
    start_utc = start_local.astimezone(timezone.utc)
    end_utc = end_local.astimezone(timezone.utc)

    adherence_res = supabase.table("adherence").select("*").eq("user_id", user["user_id"]).gte("scheduled_utc", start_utc.isoformat()).lte("scheduled_utc", end_utc.isoformat()).execute()

    completed = set()
    for entry in adherence_res.data:
        dt_comp = datetime.fromisoformat(entry["scheduled_utc"].replace("Z", "+00:00"))
        completed.add((entry["reminder_id"], dt_comp))

    upcoming = []
    for reminder in reminders_res.data:
        med = reminder.get("medicines")
        if not med or not med.get("is_active", True):
            continue

        med_start_str = med.get("start_date")
        med_end_str = med.get("end_date")
        if med_start_str:
            med_start = datetime.strptime(med_start_str, "%Y-%m-%d").date()
            if today_date < med_start:
                continue
        if med_end_str:
            med_end = datetime.strptime(med_end_str, "%Y-%m-%d").date()
            if today_date > med_end:
                continue

        time_str = reminder["dose_time_utc"]
        try:
            t = time.fromisoformat(time_str)
        except Exception:
            continue

        today_utc = datetime.now(timezone.utc).date()
        for offset in [-1, 0, 1]:
            d_utc = today_utc + timedelta(days=offset)
            occurrence_utc = datetime.combine(d_utc, t, tzinfo=timezone.utc)
            occurrence_local = occurrence_utc.astimezone(user_tz)

            if occurrence_local.date() == today_date:
                rec_type = reminder["recurrence_type"]
                if rec_type == "daily":
                    pass
                elif rec_type == "weekday":
                    params = reminder.get("recurrence_params") or []
                    if occurrence_local.isoweekday() not in params:
                        continue
                elif rec_type == "alternate":
                    if med_start_str:
                        days_diff = (occurrence_local.date() - med_start).days
                        if days_diff % 2 != 0:
                            continue
                elif rec_type == "prn":
                    pass  # PRN (as-needed) meds are always shown as available
                else:
                    continue

                is_completed = False
                for comp_rem_id, comp_dt in completed:
                    if comp_rem_id == reminder["id"]:
                        # Same UTC slot (normal idempotency)
                        if abs((comp_dt - occurrence_utc).total_seconds()) < 60:
                            is_completed = True
                            break
                        # DST fallback: different UTC but same local wall-clock time
                        comp_local = comp_dt.astimezone(user_tz)
                        if comp_local.time() == occurrence_local.time() and comp_local.date() == occurrence_local.date():
                            is_completed = True
                            break

                if not is_completed:
                    upcoming.append({
                        "id": reminder["id"],
                        "scheduled_utc": occurrence_utc.isoformat().replace("+00:00", "Z"),
                        "status": "pending",
                        "reminders": reminder
                    })

    upcoming.sort(key=lambda x: x["scheduled_utc"])
    return SuccessResponse(data=upcoming)

@router.get("/history", response_model=SuccessResponse[list])
@limiter.limit("60/minute")
async def doses_history(request: Request, user: dict = Depends(get_current_user)):
    res = supabase.table("adherence").select("*").eq("user_id", user["user_id"]).order("scheduled_utc", desc=True).limit(50).execute()
    return SuccessResponse(data=res.data)
