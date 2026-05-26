from fastapi import APIRouter, Depends, HTTPException, status
from app.models.schemas import DoseStatus
from app.db.supabase import supabase
from app.auth.dependencies import get_current_user
from datetime import datetime, timezone

router = APIRouter()

@router.post("/{dose_id}/status")
async def update_dose_status(dose_id: str, dose_status: DoseStatus, user = Depends(get_current_user)):
    # 1. Verify dose exists and belongs to user
    dose = supabase.table("doses").select("*").eq("id", dose_id).eq("user_id", user["user_id"]).execute()
    if not dose.data:
        raise HTTPException(status_code=404, detail="Dose not found")
    
    current_dose = dose.data[0]
    new_status = dose_status.status
    
    # 2. Handle Snooze logic (ADH-FR-29)
    if new_status == "snoozed":
        if current_dose["snooze_count"] >= 3:
            new_status = "missed" # Third snooze auto-marks Missed
            correction_note = "Auto-marked missed after 3 snoozes"
        else:
            data = {
                "status": "snoozed",
                "snooze_count": current_dose["snooze_count"] + 1,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
            response = supabase.table("doses").update(data).eq("id", dose_id).execute()
            return {"status": "snoozed", "count": data["snooze_count"]}

    # 3. Update dose record
    update_data = {
        "status": new_status,
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    response = supabase.table("doses").update(update_data).eq("id", dose_id).execute()
    if not response.data:
        raise HTTPException(status_code=400, detail="Could not update dose status")
        
    # Note: Trigger dose_final_outcome_sync in DB will handle insertion into adherence table
    
    return {"status": "success", "final_status": new_status}

@router.get("/upcoming", response_model=list)
async def get_upcoming_doses(user = Depends(get_current_user)):
    # Fetch doses that are pending or snoozed
    response = supabase.table("doses").select("*, reminders(dose_label, dose_time_utc, medicines(name, dosage_amount, dosage_unit))").eq("user_id", user["user_id"]).in_("status", ["pending", "snoozed"]).order("scheduled_utc").execute()
    return response.data
