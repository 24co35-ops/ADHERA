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
from datetime import datetime
import os

router = APIRouter()

@router.get("/", response_model=SuccessResponse[dict])
@limiter.limit("60/minute")
async def get_profile(request: Request, user: dict = Depends(get_current_user)):
    res = supabase.table("profiles").select("*").eq("id", user["user_id"]).execute()
    if not res.data:
        raise HTTPException(status_code=404, detail="Profile not found.")
    profile = res.data[0]
    profile.pop("mfa_secret", None)
    from app.core.utils import calculate_age
    profile["age"] = calculate_age(profile.get("date_of_birth"))
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
async def save_push_subscription(request: Request, subscription: dict, user: dict = Depends(get_current_user)):
    try:
        user_id = user["user_id"]
        endpoint = subscription.get("endpoint")
        keys = subscription.get("keys", {})
        auth = keys.get("auth") if isinstance(keys, dict) else None
        p256dh = keys.get("p256dh") if isinstance(keys, dict) else None
        if not endpoint or not auth or not p256dh:
            raise HTTPException(status_code=400, detail="Invalid subscription object — missing endpoint or keys")
        data = {
            "user_id": user_id,
            "endpoint": endpoint,
            "auth": auth,
            "p256dh": p256dh,
            "updated_at": datetime.utcnow().isoformat()
        }
        res = supabase.table("push_subscriptions").upsert(data, on_conflict="user_id").execute()
        if not res.data:
            raise HTTPException(status_code=500, detail="Failed to save push subscription.")
        return SuccessResponse(data=res.data[0])
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save subscription: {str(e)}")

@router.delete("/push-subscription")
@limiter.limit("30/minute")
async def delete_push_subscription(request: Request, user=Depends(get_current_user)):
    try:
        user_id = user["user_id"]
        result = supabase.table("push_subscriptions").delete().eq("user_id", user_id).execute()
        return {"success": True, "message": "Push subscription removed"}
    except Exception as e:
        print(f"DELETE push-subscription error for user {user_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to remove subscription: {str(e)}"
        )

@router.get("/vapid-public-key", response_model=SuccessResponse[dict])
@limiter.limit("60/minute")
async def get_vapid_public_key(request: Request, user: dict = Depends(get_current_user)):
    return SuccessResponse(data={"public_key": os.environ.get("VAPID_PUBLIC_KEY", "")})


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
        "scheduled_utc, status, correction_note, reminders(dose_label, medicines(name))"
    ).eq("user_id", uid).order("scheduled_utc", desc=True).execute()
    medicines_res = supabase.table("medicines").select("*").eq("user_id", uid).execute()
    feedback_res = supabase.table("feedback").select("*").eq("user_id", uid).execute()

    adherence = adherence_res.data or []
    medicines = medicines_res.data or []
    feedback = feedback_res.data or []

    # Map correction_note to notes for the output format
    for row in adherence:
        row["notes"] = row.get("correction_note") or ""

    if format == "json":
        content = json_mod.dumps(
            {"adherence": adherence, "medicines": medicines, "feedback": feedback},
            default=str
        )
        return StreamingResponse(
            io.BytesIO(content.encode("utf-8")),
            media_type="application/json",
            headers={"Content-Disposition": "attachment; filename=adhera_export.json"}
        )
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
        content = buf.getvalue()
        return StreamingResponse(
            io.BytesIO(content.encode("utf-8")),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=adhera_export.csv"}
        )
