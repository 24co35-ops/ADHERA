from fastapi import APIRouter, Depends, HTTPException
from app.db.supabase import supabase
from app.auth.dependencies import get_current_user
from app.core.responses import SuccessResponse
from app.medicines.schemas import ReminderUpdate
from app.services.audit import log_audit_action

router = APIRouter()

def _check_reminder_access(user: dict, reminder_id: str):
    """Get reminder and verify access. Returns reminder dict."""
    res = supabase.table("reminders").select("*").eq("id", reminder_id).execute()
    if not res.data:
        raise HTTPException(status_code=404, detail="Reminder not found")
    rem = res.data[0]
    role = user.get("role", "patient")
    if role == "patient" and rem["user_id"] != user["user_id"]:
        raise HTTPException(status_code=403, detail="Forbidden")
    if role == "provider":
        asg = supabase.table("assignments").select("id").eq("provider_id", user["user_id"]).eq("patient_id", rem["user_id"]).eq("status", "active").execute()
        if not asg.data:
            raise HTTPException(status_code=403, detail="Not assigned to this patient")
    return rem

@router.patch("/{id}", response_model=SuccessResponse[dict])
async def update_reminder(id: str, payload: ReminderUpdate, user: dict = Depends(get_current_user)):
    _check_reminder_access(user, id)
    data = payload.model_dump(exclude_unset=True)
    if not data:
        raise HTTPException(status_code=400, detail="No fields to update")
    if "dose_label" in data and data["dose_label"]:
        data["dose_label"] = data["dose_label"].lower()
    if "dose_time_utc" in data and data["dose_time_utc"]:
        if len(data["dose_time_utc"]) == 5:
            data["dose_time_utc"] = data["dose_time_utc"] + ":00"
    res = supabase.table("reminders").update(data).eq("id", id).execute()
    if not res.data:
        raise HTTPException(status_code=404, detail="Reminder not found")
    log_audit_action("REMINDER_UPDATED", user["user_id"], {"target": id})
    return SuccessResponse(data=res.data[0])

@router.delete("/{id}", response_model=SuccessResponse[dict])
async def delete_reminder(id: str, user: dict = Depends(get_current_user)):
    _check_reminder_access(user, id)
    supabase.table("reminders").update({"is_active": False}).eq("id", id).execute()
    log_audit_action("REMINDER_DELETED", user["user_id"], {"target": id})
    return SuccessResponse(data={"id": id, "is_active": False})
