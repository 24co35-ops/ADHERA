import logging
from fastapi import APIRouter, Depends, HTTPException, status
from app.models.schemas import ProfileUpdate, EmergencyContactBase
from app.db.supabase import supabase
from app.auth.dependencies import get_current_user

logger = logging.getLogger("adhera.profile")
router = APIRouter()


@router.get("/")
async def get_profile(user: dict = Depends(get_current_user)):
    """Fetch the authenticated user's profile."""
    response = supabase.table("profiles").select("*").eq("id", user["user_id"]).execute()
    if not response.data:
        raise HTTPException(status_code=404, detail="Profile not found.")
    return response.data[0]


@router.patch("/")
async def update_profile(profile: ProfileUpdate, user: dict = Depends(get_current_user)):
    """Partially update the authenticated user's profile."""
    data = profile.model_dump(exclude_unset=True)
    if not data:
        raise HTTPException(status_code=400, detail="No fields provided to update.")

    # Serialize date fields to ISO strings for Supabase
    if "date_of_birth" in data and data["date_of_birth"] is not None:
        data["date_of_birth"] = data["date_of_birth"].isoformat()

    response = supabase.table("profiles").update(data).eq("id", user["user_id"]).execute()
    if not response.data:
        raise HTTPException(status_code=404, detail="Profile not found.")
    return response.data[0]


@router.get("/emergency-contact")
async def get_emergency_contact(user: dict = Depends(get_current_user)):
    """Fetch the authenticated user's emergency contact, if set."""
    response = (
        supabase.table("emergency_contacts")
        .select("*")
        .eq("user_id", user["user_id"])
        .execute()
    )
    if not response.data:
        return None
    return response.data[0]


@router.put("/emergency-contact")
async def upsert_emergency_contact(
    contact: EmergencyContactBase, user: dict = Depends(get_current_user)
):
    """Create or replace the authenticated user's emergency contact."""
    data = contact.model_dump()
    data["user_id"] = user["user_id"]

    response = supabase.table("emergency_contacts").upsert(data, on_conflict="user_id").execute()
    if not response.data:
        raise HTTPException(status_code=400, detail="Could not save emergency contact.")
    return response.data[0]
