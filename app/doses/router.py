from fastapi import APIRouter, Depends, HTTPException, status
from app.db.supabase import supabase
from app.auth.dependencies import get_current_user
from app.core.responses import SuccessResponse
from datetime import datetime, timezone, time, timedelta
import pytz

router = APIRouter()

def get_scheduled_utc_for_today(reminder: dict) -> str:
    profile_res = supabase.table("profiles").select("timezone").eq("id", reminder["user_id"]).execute()
    user_tz_str = "UTC"
    if profile_res.data:
        user_tz_str = profile_res.data[0].get("timezone") or "UTC"
        
    try:
        user_tz = pytz.timezone(user_tz_str)
    except Exception:
        user_tz = pytz.utc
        
    now_local = datetime.now(user_tz)
    today_date = now_local.date()
    t = time.fromisoformat(reminder["dose_time_utc"])
    today_utc = datetime.now(timezone.utc).date()
    
    for offset in [-1, 0, 1]:
        d_utc = today_utc + timedelta(days=offset)
        occurrence_utc = pytz.utc.localize(datetime.combine(d_utc, t))
        occurrence_local = occurrence_utc.astimezone(user_tz)
        if occurrence_local.date() == today_date:
            return occurrence_utc.isoformat().replace("+00:00", "Z")
            
    occurrence_utc = pytz.utc.localize(datetime.combine(today_utc, t))
    return occurrence_utc.isoformat().replace("+00:00", "Z")

@router.post("/{reminder_id}/taken", response_model=SuccessResponse[dict])
async def dose_taken(reminder_id: str, user: dict = Depends(get_current_user)):
    rem_res = supabase.table("reminders").select("*").eq("id", reminder_id).execute()
    if not rem_res.data:
        raise HTTPException(status_code=404, detail="Reminder not found")
    reminder = rem_res.data[0]
    scheduled_utc = get_scheduled_utc_for_today(reminder)
    
    res = supabase.table("adherence").insert({
        "reminder_id": reminder_id,
        "user_id": user["user_id"],
        "scheduled_utc": scheduled_utc,
        "status": "taken",
        "outcome_utc": datetime.now(timezone.utc).isoformat()
    }).execute()
    return SuccessResponse(data=res.data[0])

@router.post("/{reminder_id}/missed", response_model=SuccessResponse[dict])
async def dose_missed(reminder_id: str, user: dict = Depends(get_current_user)):
    rem_res = supabase.table("reminders").select("*").eq("id", reminder_id).execute()
    if not rem_res.data:
        raise HTTPException(status_code=404, detail="Reminder not found")
    reminder = rem_res.data[0]
    scheduled_utc = get_scheduled_utc_for_today(reminder)
    
    res = supabase.table("adherence").insert({
        "reminder_id": reminder_id,
        "user_id": user["user_id"],
        "scheduled_utc": scheduled_utc,
        "status": "missed",
        "outcome_utc": datetime.now(timezone.utc).isoformat()
    }).execute()
    return SuccessResponse(data=res.data[0])

@router.post("/{reminder_id}/snooze", response_model=SuccessResponse[dict])
async def dose_snooze(reminder_id: str, user: dict = Depends(get_current_user)):
    return SuccessResponse(data={"message": "Snoozed."})

@router.get("/upcoming", response_model=SuccessResponse[list])
async def doses_upcoming(user: dict = Depends(get_current_user)):
    profile_res = supabase.table("profiles").select("timezone").eq("id", user["user_id"]).execute()
    user_tz_str = "UTC"
    if profile_res.data:
        user_tz_str = profile_res.data[0].get("timezone") or "UTC"
        
    try:
        user_tz = pytz.timezone(user_tz_str)
    except Exception:
        user_tz = pytz.utc
        
    now_local = datetime.now(user_tz)
    today_date = now_local.date()
    
    reminders_res = supabase.table("reminders").select("*, medicines(*)").eq("user_id", user["user_id"]).eq("is_active", True).execute()
    
    start_local = user_tz.localize(datetime.combine(today_date, time.min))
    end_local = user_tz.localize(datetime.combine(today_date, time.max))
    start_utc = start_local.astimezone(pytz.utc)
    end_utc = end_local.astimezone(pytz.utc)
    
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
            occurrence_utc = pytz.utc.localize(datetime.combine(d_utc, t))
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
                else:
                    continue
                    
                is_completed = False
                for comp_rem_id, comp_dt in completed:
                    if comp_rem_id == reminder["id"]:
                        if abs((comp_dt - occurrence_utc).total_seconds()) < 60:
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
async def doses_history(user: dict = Depends(get_current_user)):
    res = supabase.table("adherence").select("*").eq("user_id", user["user_id"]).order("scheduled_utc", desc=True).limit(50).execute()
    return SuccessResponse(data=res.data)
