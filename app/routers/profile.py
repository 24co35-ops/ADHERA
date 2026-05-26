from fastapi import APIRouter, Depends, HTTPException, status
from app.models.schemas import ProfileUpdate, EmergencyContactBase
from app.db.supabase import supabase
from app.auth.dependencies import get_current_user

router = APIRouter()

@router.get("/")
async def get_profile(user = Depends(get_current_user)):
    response = supabase.table("profiles").select("*").eq("id", user["user_id"]).execute()
    if not response.data:
        raise HTTPException(status_code=404, detail="Profile not found")
    return response.data[0]

@router.patch("/")
async def update_profile(profile: ProfileUpdate, user = Depends(get_current_user)):
    data = profile.model_dump(exclude_unset=True)
    if not data:
        raise HTTPException(status_code=400, detail="No fields to update")
    
    response = supabase.table("profiles").update(data).eq("id", user["user_id"]).execute()
    return response.data[0]

@router.get("/emergency-contact")
async def get_emergency_contact(user = Depends(get_current_user)):
    response = supabase.table("emergency_contacts").select("*").eq("user_id", user["user_id"]).execute()
    if not response.data:
        return None
    return response.data[0]

@router.put("/emergency-contact")
async def upsert_emergency_contact(contact: EmergencyContactBase, user = Depends(get_current_user)):
    data = contact.model_dump()
    data["user_id"] = user["user_id"]
    
    # Upsert logic
    response = supabase.table("emergency_contacts").upsert(data).execute()
    return response.data[0]
