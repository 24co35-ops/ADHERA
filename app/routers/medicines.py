from datetime import date
from fastapi import APIRouter, Depends, HTTPException, status
from app.models.schemas import MedicineCreate, Medicine
from app.db.supabase import supabase
from app.auth.dependencies import get_current_user

router = APIRouter()

@router.post("/", response_model=Medicine, status_code=status.HTTP_201_CREATED)
async def create_medicine(medicine: MedicineCreate, user = Depends(get_current_user)):
    # Basic validation
    if medicine.start_date < date.today():
        raise HTTPException(status_code=400, detail="Start date cannot be in the past")
    
    data = medicine.model_dump()
    data["user_id"] = user["user_id"]
    data["is_active"] = True
    
    response = supabase.table("medicines").insert(data).execute()
    if not response.data:
        raise HTTPException(status_code=400, detail="Could not create medicine")
        
    return response.data[0]

@router.get("/", response_model=list[Medicine])
async def list_medicines(user = Depends(get_current_user)):
    response = supabase.table("medicines").select("*").eq("user_id", user["user_id"]).eq("is_active", True).execute()
    return response.data

@router.get("/{id}", response_model=Medicine)
async def get_medicine(id: str, user = Depends(get_current_user)):
    response = supabase.table("medicines").select("*").eq("id", id).eq("user_id", user["user_id"]).execute()
    if not response.data:
        raise HTTPException(status_code=404, detail="Medicine not found")
    return response.data[0]

@router.patch("/{id}", response_model=Medicine)
async def update_medicine(id: str, medicine: MedicineCreate, user = Depends(get_current_user)):
    data = medicine.model_dump(exclude_unset=True)
    response = supabase.table("medicines").update(data).eq("id", id).eq("user_id", user["user_id"]).execute()
    if not response.data:
        raise HTTPException(status_code=404, detail="Medicine not found")
    return response.data[0]

@router.delete("/{id}")
async def delete_medicine(id: str, user = Depends(get_current_user)):
    # Soft delete
    response = supabase.table("medicines").update({"is_active": False}).eq("id", id).eq("user_id", user["user_id"]).execute()
    if not response.data:
        raise HTTPException(status_code=404, detail="Medicine not found")
    return {"message": "Medicine deleted"}
