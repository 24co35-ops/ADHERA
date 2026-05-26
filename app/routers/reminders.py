from fastapi import APIRouter, Depends, HTTPException, status
from app.models.schemas import ReminderCreate, Reminder
from app.db.supabase import supabase
from app.auth.dependencies import get_current_user

router = APIRouter()

@router.post("/", response_model=Reminder, status_code=status.HTTP_201_CREATED)
async def create_reminder(reminder: ReminderCreate, user = Depends(get_current_user)):
    data = reminder.model_dump()
    data["user_id"] = user["user_id"]
    
    response = supabase.table("reminders").insert(data).execute()
    if not response.data:
        raise HTTPException(status_code=400, detail="Could not create reminder")
        
    return response.data[0]

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
