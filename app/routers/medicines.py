from fastapi import APIRouter, Depends, HTTPException, status
from app.models.schemas import MedicineCreate, Medicine
from app.db.supabase import supabase
from app.auth.dependencies import get_current_user

router = APIRouter()

@router.post("/", response_model=Medicine, status_code=status.HTTP_201_CREATED)
async def create_medicine(medicine: MedicineCreate, user = Depends(get_current_user)):
    data = medicine.model_dump()
    data["user_id"] = user["user_id"]
    
    response = supabase.table("medicines").insert(data).execute()
    if not response.data:
        raise HTTPException(status_code=400, detail="Could not create medicine")
        
    return response.data[0]

@router.get("/", response_model=list[Medicine])
async def list_medicines(user = Depends(get_current_user)):
    response = supabase.table("medicines").select("*").eq("user_id", user["user_id"]).eq("is_active", True).execute()
    return response.data
