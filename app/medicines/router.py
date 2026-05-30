from fastapi import APIRouter, Depends, HTTPException, status
from app.db.supabase import supabase
from app.auth.dependencies import get_current_user
from app.core.responses import SuccessResponse
from app.medicines.schemas import MedicineCreate, MedicineUpdate, ReminderCreate

router = APIRouter()

@router.post("/", response_model=SuccessResponse[dict], status_code=status.HTTP_201_CREATED)
async def create_medicine(medicine: MedicineCreate, user: dict = Depends(get_current_user)):
    data = medicine.model_dump()
    data["user_id"] = user["user_id"]
    data["start_date"] = data["start_date"].isoformat()
    if data["end_date"]: data["end_date"] = data["end_date"].isoformat()
    res = supabase.table("medicines").insert(data).execute()
    return SuccessResponse(data=res.data[0])

@router.get("/", response_model=SuccessResponse[list])
async def list_medicines(user: dict = Depends(get_current_user)):
    res = supabase.table("medicines").select("*").eq("user_id", user["user_id"]).eq("is_active", True).execute()
    return SuccessResponse(data=res.data)

@router.get("/{id}", response_model=SuccessResponse[dict])
async def get_medicine(id: str, user: dict = Depends(get_current_user)):
    res = supabase.table("medicines").select("*").eq("id", id).eq("user_id", user["user_id"]).execute()
    if not res.data: raise HTTPException(status_code=404, detail="Medicine not found")
    return SuccessResponse(data=res.data[0])

@router.patch("/{id}", response_model=SuccessResponse[dict])
async def update_medicine(id: str, medicine: MedicineUpdate, user: dict = Depends(get_current_user)):
    data = medicine.model_dump(exclude_unset=True)
    res = supabase.table("medicines").update(data).eq("id", id).eq("user_id", user["user_id"]).execute()
    return SuccessResponse(data=res.data[0])

@router.delete("/{id}", response_model=SuccessResponse[dict])
async def delete_medicine(id: str, user: dict = Depends(get_current_user)):
    supabase.table("medicines").update({"is_active": False}).eq("id", id).eq("user_id", user["user_id"]).execute()
    return SuccessResponse(data={"message": "Deleted."})

@router.post("/{id}/reminders", response_model=SuccessResponse[dict], status_code=status.HTTP_201_CREATED)
async def create_reminder(id: str, reminder: ReminderCreate, user: dict = Depends(get_current_user)):
    data = reminder.model_dump()
    data["medicine_id"] = id
    data["user_id"] = user["user_id"]
    res = supabase.table("reminders").insert(data).execute()
    return SuccessResponse(data=res.data[0])

@router.get("/{id}/reminders", response_model=SuccessResponse[list])
async def get_reminders(id: str, user: dict = Depends(get_current_user)):
    res = supabase.table("reminders").select("*").eq("medicine_id", id).eq("user_id", user["user_id"]).eq("is_active", True).execute()
    return SuccessResponse(data=res.data)
