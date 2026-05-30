from fastapi import APIRouter, Depends, HTTPException, status
from app.db.supabase import supabase
from app.auth.dependencies import get_current_user
from app.core.responses import SuccessResponse
from app.doses.schemas import DoseStatus
from datetime import datetime, timezone

router = APIRouter()

@router.post("/{reminder_id}/taken", response_model=SuccessResponse[dict])
async def dose_taken(reminder_id: str, user: dict = Depends(get_current_user)):
    res = supabase.table("adherence").insert({
        "reminder_id": reminder_id,
        "user_id": user["user_id"],
        "scheduled_utc": datetime.now(timezone.utc).isoformat(),
        "status": "taken",
        "outcome_utc": datetime.now(timezone.utc).isoformat()
    }).execute()
    return SuccessResponse(data=res.data[0])

@router.post("/{reminder_id}/missed", response_model=SuccessResponse[dict])
async def dose_missed(reminder_id: str, user: dict = Depends(get_current_user)):
    res = supabase.table("adherence").insert({
        "reminder_id": reminder_id,
        "user_id": user["user_id"],
        "scheduled_utc": datetime.now(timezone.utc).isoformat(),
        "status": "missed",
        "outcome_utc": datetime.now(timezone.utc).isoformat()
    }).execute()
    return SuccessResponse(data=res.data[0])

@router.post("/{reminder_id}/snooze", response_model=SuccessResponse[dict])
async def dose_snooze(reminder_id: str, user: dict = Depends(get_current_user)):
    # Simple snooze endpoint to mark snooze count on operational state in a real impl.
    # For now, it returns success.
    return SuccessResponse(data={"message": "Snoozed."})

@router.get("/upcoming", response_model=SuccessResponse[list])
async def doses_upcoming(user: dict = Depends(get_current_user)):
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    res = supabase.table("adherence").select("*, reminders(*, medicines(*))").eq("user_id", user["user_id"]).eq("status", "pending").gte("scheduled_utc", today + "T00:00:00Z").lte("scheduled_utc", today + "T23:59:59Z").execute()
    return SuccessResponse(data=res.data)

@router.get("/history", response_model=SuccessResponse[list])
async def doses_history(user: dict = Depends(get_current_user)):
    res = supabase.table("adherence").select("*").eq("user_id", user["user_id"]).order("scheduled_utc", desc=True).limit(50).execute()
    return SuccessResponse(data=res.data)
