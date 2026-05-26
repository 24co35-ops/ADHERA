from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from app.models.schemas import ReminderCreate, Reminder
from app.db.supabase import supabase
from app.auth.dependencies import get_current_user

router = APIRouter()

async def check_reminder_conflict(user_id: str, new_dose_time: str, timezone: str):
    """
    ADH-FR-19: Advisory conflict warning when a new reminder falls within 30 minutes 
    of an existing one (non-blocking).
    """
    response = supabase.table("reminders").select("dose_time_utc").eq("user_id", user_id).eq("is_active", True).execute()
    if not response.data:
        return None
    
    new_time = datetime.strptime(new_dose_time, "%H:%M:%S")
    
    for existing in response.data:
        ext_time = datetime.strptime(existing["dose_time_utc"], "%H:%M:%S")
        diff = abs((new_time - ext_time).total_seconds()) / 60
        if diff <= 30:
            return f"Conflict detected: Another dose is scheduled within 30 minutes at {existing['dose_time_utc']}"
    
    return None

@router.post("/", response_model=Reminder, status_code=status.HTTP_201_CREATED)
async def create_reminder(reminder: ReminderCreate, user = Depends(get_current_user)):
    data = reminder.model_dump()
    data["user_id"] = user["user_id"]
    
    # Check for conflict (ADH-FR-19)
    conflict_warning = await check_reminder_conflict(user["user_id"], reminder.dose_time_utc, reminder.timezone)
    
    response = supabase.table("reminders").insert(data).execute()
    if not response.data:
        raise HTTPException(status_code=400, detail="Could not create reminder")
        
    result = response.data[0]
    if conflict_warning:
        result["warning"] = conflict_warning
        
    return result

@router.get("/{medicine_id}", response_model=list[Reminder])
async def list_reminders(medicine_id: str, user = Depends(get_current_user)):
    response = supabase.table("reminders").select("*").eq("medicine_id", medicine_id).eq("user_id", user["user_id"]).eq("is_active", True).execute()
    return response.data

@router.patch("/{id}", response_model=Reminder)
async def update_reminder(id: str, reminder: ReminderCreate, user = Depends(get_current_user)):
    data = reminder.model_dump(exclude_unset=True)
    response = supabase.table("reminders").update(data).eq("id", id).eq("user_id", user["user_id"]).execute()
    if not response.data:
        raise HTTPException(status_code=404, detail="Reminder not found")
    return response.data[0]

@router.delete("/{id}")
async def delete_reminder(id: str, user = Depends(get_current_user)):
    # Soft delete
    response = supabase.table("reminders").update({"is_active": False}).eq("id", id).eq("user_id", user["user_id"]).execute()
    if not response.data:
        raise HTTPException(status_code=404, detail="Reminder not found")
    return {"message": "Reminder deleted"}
