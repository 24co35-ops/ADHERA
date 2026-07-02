import requests
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status

from app.auth.dependencies import get_current_user
from app.config import settings
from app.core.rate_limit import limiter
from app.core.responses import SuccessResponse
from app.db.supabase import supabase
from app.feedback.schemas import FeedbackCreate
from app.services.audit import log_audit_action

router = APIRouter()

def _check_assignment(provider_id: str, patient_id: str):
    res = supabase.table("assignments").select("id").eq("provider_id", provider_id).eq("patient_id", patient_id).eq("status", "active").execute()
    if not res.data:
        raise HTTPException(status_code=403, detail="Not assigned to this patient")

@router.post("/", response_model=SuccessResponse[dict], status_code=status.HTTP_201_CREATED)
@limiter.limit("60/minute")
async def create_feedback(request: Request, feedback: FeedbackCreate, user: dict = Depends(get_current_user)):
    role = user.get("role", "patient")
    if role != "patient":
        raise HTTPException(status_code=403, detail="Only patients can submit feedback")
    data = feedback.model_dump()
    data["user_id"] = user["user_id"]
    res = supabase.table("feedback").insert(data).execute()

    if feedback.severity == 4:
        try:
            url = f"{settings.SUPABASE_URL}/functions/v1/emergency-alert"
            headers = {"Authorization": f"Bearer {settings.SUPABASE_ANON_KEY}", "Content-Type": "application/json"}
            prov = supabase.table("assignments").select("profiles!provider_id(email)").eq("patient_id", user["user_id"]).eq("status", "active").execute()
            cont = supabase.table("emergency_contacts").select("email").eq("user_id", user["user_id"]).execute()
            provider_email = None
            if prov.data:
                p_item = prov.data[0]
                if "profiles" in p_item and isinstance(p_item["profiles"], dict):
                    provider_email = p_item["profiles"].get("email")
                elif "provider_id" in p_item:
                    prof = supabase.table("profiles").select("contact_number").eq("id", p_item["provider_id"]).execute()
                    provider_email = prof.data[0].get("contact_number") if prof.data else None
            payload = {
                "patient_id": user["user_id"],
                "medicine_name": feedback.medicine_id,
                "description": feedback.description,
                "severity": feedback.severity,
                "provider_email": provider_email,
                "emergency_contact_email": cont.data[0]["email"] if cont.data else None
            }
            requests.post(url, headers=headers, json=payload, timeout=5)
        except Exception:
            log_audit_action("EMERGENCY_ALERT_FAILED", user["user_id"], {"feedback_id": res.data[0]["id"] if res.data else None})

    return SuccessResponse(data=res.data[0])

@router.get("/", response_model=SuccessResponse[list])
@limiter.limit("60/minute")
async def list_feedback(
    request: Request,
    patient_id: str = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user: dict = Depends(get_current_user)
):
    role = user.get("role", "patient")
    if role == "patient":
        q = supabase.table("feedback").select("*").eq("user_id", user["user_id"]).order("created_at", desc=True).range(offset, offset + limit - 1)
    elif role == "provider":
        if not patient_id:
            raise HTTPException(status_code=400, detail="patient_id required for provider")
        _check_assignment(user["user_id"], patient_id)
        q = supabase.table("feedback").select("*").eq("user_id", patient_id).order("created_at", desc=True).range(offset, offset + limit - 1)
    elif role == "admin":
        if patient_id:
            q = supabase.table("feedback").select("*").eq("user_id", patient_id).order("created_at", desc=True).range(offset, offset + limit - 1)
        else:
            q = supabase.table("feedback").select("*").order("created_at", desc=True).range(offset, offset + limit - 1)
    else:
        raise HTTPException(status_code=403, detail="Forbidden")
    res = q.execute()
    return SuccessResponse(data=res.data)
