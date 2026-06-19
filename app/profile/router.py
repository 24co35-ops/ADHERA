from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import StreamingResponse
from app.db.supabase import supabase
from app.auth.dependencies import get_current_user
from app.core.responses import SuccessResponse
from app.core.rate_limit import limiter
from app.profile.schemas import ProfileUpdate, EmergencyContact, PushSubscriptionCreate
import csv
import io
import json as json_mod
import datetime

router = APIRouter()

@router.get("/", response_model=SuccessResponse[dict])
@limiter.limit("60/minute")
async def get_profile(request: Request, user: dict = Depends(get_current_user)):
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
@limiter.limit("60/minute")
async def update_profile(request: Request, profile: ProfileUpdate, user: dict = Depends(get_current_user)):
    data = profile.model_dump(exclude_unset=True)
    if not data:
        raise HTTPException(status_code=400, detail="No fields provided.")
    res = supabase.table("profiles").update(data).eq("id", user["user_id"]).execute()
    profile_data = res.data[0]
    profile_data.pop("mfa_secret", None)
    return SuccessResponse(data=profile_data)

@router.get("/emergency-contact", response_model=SuccessResponse[dict])
@limiter.limit("60/minute")
async def get_emergency_contact(request: Request, user: dict = Depends(get_current_user)):
    res = supabase.table("emergency_contacts").select("*").eq("user_id", user["user_id"]).execute()
    return SuccessResponse(data=res.data[0] if res.data else {})

@router.put("/emergency-contact", response_model=SuccessResponse[dict])
@limiter.limit("60/minute")
async def update_emergency_contact(request: Request, contact: EmergencyContact, user: dict = Depends(get_current_user)):
    data = contact.model_dump()
    data["user_id"] = user["user_id"]
    res = supabase.table("emergency_contacts").upsert(data, on_conflict="user_id").execute()
    return SuccessResponse(data=res.data[0])

@router.delete("/emergency-contact", response_model=SuccessResponse[dict])
@limiter.limit("60/minute")
async def delete_emergency_contact(request: Request, user: dict = Depends(get_current_user)):
    supabase.table("emergency_contacts").delete().eq("user_id", user["user_id"]).execute()
    return SuccessResponse(data={"message": "Deleted emergency contact."})

@router.post("/push-subscription", response_model=SuccessResponse[dict])
@limiter.limit("60/minute")
async def save_push_subscription(request: Request, subscription: PushSubscriptionCreate, user: dict = Depends(get_current_user)):
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

@router.get("/export")
@limiter.limit("60/minute")
async def export_data(
    request: Request,
    format: str = Query("json", pattern="^(json|csv)$"),
    user: dict = Depends(get_current_user)
):
    uid = user["user_id"]

    # Fetch all patient data
    adherence_res = supabase.table("adherence").select(
        "scheduled_utc, status, notes, reminders(dose_label, medicines(name))"
    ).eq("user_id", uid).order("scheduled_utc", desc=True).execute()
    medicines_res = supabase.table("medicines").select("*").eq("user_id", uid).execute()
    feedback_res = supabase.table("feedback").select("*").eq("user_id", uid).execute()

    adherence = adherence_res.data or []
    medicines = medicines_res.data or []
    feedback = feedback_res.data or []

    timestamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d%H%M%S")
    storage_path = f"{uid}/{timestamp}.{format}"

    if format == "json":
        content = json_mod.dumps(
            {"adherence": adherence, "medicines": medicines, "feedback": feedback},
            default=str
        ).encode("utf-8")
        content_type = "application/json"
    else:
        buf = io.StringIO()
        writer = csv.DictWriter(buf, fieldnames=["date", "medicine_name", "dose_label", "status", "notes"])
        writer.writeheader()
        for row in adherence:
            rem = row.get("reminders") or {}
            med = rem.get("medicines") or {} if isinstance(rem, dict) else {}
            writer.writerow({
                "date": (row.get("scheduled_utc") or "")[:10],
                "medicine_name": med.get("name", "") if isinstance(med, dict) else "",
                "dose_label": rem.get("dose_label", "") if isinstance(rem, dict) else "",
                "status": row.get("status", ""),
                "notes": row.get("notes", "") or "",
            })
        content = buf.getvalue().encode("utf-8")
        content_type = "text/csv"

    # Upload to Supabase Storage (private exports bucket)
    bucket = supabase.storage.from_("exports")
    try:
        bucket.upload(storage_path, content, {"content-type": content_type, "upsert": "true"})
    except Exception:
        try:
            bucket.update(storage_path, content, {"content-type": content_type})
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Storage upload failed: {str(e)}")

    # Signed URL valid 15 minutes (900 seconds)
    signed = bucket.create_signed_url(storage_path, 900)
    signed_url = signed.get("signedURL") or signed.get("signedUrl") or ""

    return SuccessResponse(data={"signed_url": signed_url, "format": format, "expires_in": 900})
