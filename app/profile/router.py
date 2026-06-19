from fastapi import APIRouter, Depends, HTTPException
from app.db.supabase import supabase
from app.auth.dependencies import get_current_user
from app.core.responses import SuccessResponse
from app.profile.schemas import ProfileUpdate, EmergencyContact, PushSubscriptionCreate

router = APIRouter()

@router.get("/", response_model=SuccessResponse[dict])
async def get_profile(user: dict = Depends(get_current_user)):
    res = supabase.table("profiles").select("*").eq("id", user["user_id"]).execute()
    if not res.data:
        raise HTTPException(status_code=404, detail="Profile not found.")
    profile = res.data[0]
    profile.pop("mfa_secret", None)
    try:
        u = supabase.auth.admin.get_user_by_id(user["user_id"])
        profile["email"] = u.user.email
    except Exception:
        pass
    return SuccessResponse(data=profile)

@router.patch("/", response_model=SuccessResponse[dict])
async def update_profile(profile: ProfileUpdate, user: dict = Depends(get_current_user)):
    data = profile.model_dump(exclude_unset=True)
    if not data:
        raise HTTPException(status_code=400, detail="No fields provided.")
    res = supabase.table("profiles").update(data).eq("id", user["user_id"]).execute()
    profile_data = res.data[0]
    profile_data.pop("mfa_secret", None)
    return SuccessResponse(data=profile_data)

@router.get("/emergency-contact", response_model=SuccessResponse[dict])
async def get_emergency_contact(user: dict = Depends(get_current_user)):
    res = supabase.table("emergency_contacts").select("*").eq("user_id", user["user_id"]).execute()
    return SuccessResponse(data=res.data[0] if res.data else {})

@router.put("/emergency-contact", response_model=SuccessResponse[dict])
async def update_emergency_contact(contact: EmergencyContact, user: dict = Depends(get_current_user)):
    data = contact.model_dump()
    data["user_id"] = user["user_id"]
    res = supabase.table("emergency_contacts").upsert(data, on_conflict="user_id").execute()
    return SuccessResponse(data=res.data[0])

@router.delete("/emergency-contact", response_model=SuccessResponse[dict])
async def delete_emergency_contact(user: dict = Depends(get_current_user)):
    supabase.table("emergency_contacts").delete().eq("user_id", user["user_id"]).execute()
    return SuccessResponse(data={"message": "Deleted emergency contact."})

@router.post("/push-subscription", response_model=SuccessResponse[dict])
async def save_push_subscription(subscription: PushSubscriptionCreate, user: dict = Depends(get_current_user)):
    data = {
        "user_id": user["user_id"],
        "endpoint": subscription.endpoint,
        "auth": subscription.keys.auth,
        "p256dh": subscription.keys.p256dh,
        "subscription": subscription.model_dump()
    }
    res = supabase.table("push_subscriptions").upsert(data, on_conflict="user_id,endpoint").execute()
    if not res.data:
        raise HTTPException(status_code=500, detail="Failed to save push subscription.")
    return SuccessResponse(data=res.data[0])

