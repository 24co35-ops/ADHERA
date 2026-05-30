from fastapi import APIRouter, Depends, HTTPException
from app.db.supabase import supabase_admin
from app.auth.dependencies import get_current_user
from app.core.responses import SuccessResponse
from app.profile.schemas import ProfileUpdate, EmergencyContact

router = APIRouter()

@router.get("/", response_model=SuccessResponse[dict])
async def get_profile(user: dict = Depends(get_current_user)):
    res = supabase_admin.table("profiles").select("*").eq("id", user["user_id"]).execute()
    if not res.data:
        raise HTTPException(status_code=404, detail="Profile not found.")
    return SuccessResponse(data=res.data[0])

@router.patch("/", response_model=SuccessResponse[dict])
async def update_profile(profile: ProfileUpdate, user: dict = Depends(get_current_user)):
    data = profile.model_dump(exclude_unset=True)
    if not data:
        raise HTTPException(status_code=400, detail="No fields provided.")
    res = supabase_admin.table("profiles").update(data).eq("id", user["user_id"]).execute()
    return SuccessResponse(data=res.data[0])

@router.get("/emergency-contact", response_model=SuccessResponse[dict])
async def get_emergency_contact(user: dict = Depends(get_current_user)):
    res = supabase_admin.table("emergency_contacts").select("*").eq("user_id", user["user_id"]).execute()
    return SuccessResponse(data=res.data[0] if res.data else {})

@router.put("/emergency-contact", response_model=SuccessResponse[dict])
async def update_emergency_contact(contact: EmergencyContact, user: dict = Depends(get_current_user)):
    data = contact.model_dump()
    data["user_id"] = user["user_id"]
    res = supabase_admin.table("emergency_contacts").upsert(data, on_conflict="user_id").execute()
    return SuccessResponse(data=res.data[0])

@router.delete("/emergency-contact", response_model=SuccessResponse[dict])
async def delete_emergency_contact(user: dict = Depends(get_current_user)):
    supabase_admin.table("emergency_contacts").delete().eq("user_id", user["user_id"]).execute()
    return SuccessResponse(data={"message": "Deleted emergency contact."})
