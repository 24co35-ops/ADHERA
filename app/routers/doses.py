from fastapi import APIRouter, Depends, HTTPException, status
from app.models.schemas import DoseStatus
from app.db.supabase import supabase
from app.auth.dependencies import get_current_user
from datetime import datetime, timezone

router = APIRouter()

@router.post("/{reminder_id}/status")
async def update_dose_status(reminder_id: str, dose_status: DoseStatus, user = Depends(get_current_user)):
    # 1. Verify reminder exists and belongs to user
    reminder = supabase.table("reminders").select("*").eq("id", reminder_id).eq("user_id", user["user_id"]).execute()
    if not reminder.data:
        raise HTTPException(status_code=404, detail="Reminder not found")
        
    # 2. Insert adherence record
    data = {
        "reminder_id": reminder_id,
        "user_id": user["user_id"],
        "scheduled_utc": datetime.now(timezone.utc).isoformat(), # Simplified for now, should be actual scheduled time
        "status": dose_status.status,
        "correction_note": dose_status.correction_note
    }
    
    response = supabase.table("adherence").insert(data).execute()
    if not response.data:
        raise HTTPException(status_code=400, detail="Could not update dose status")
        
    return {"status": "success"}
