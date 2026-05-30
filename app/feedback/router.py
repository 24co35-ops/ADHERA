from fastapi import APIRouter, Depends, HTTPException, status
from app.db.supabase import supabase
from app.auth.dependencies import get_current_user
from app.core.responses import SuccessResponse
from app.feedback.schemas import FeedbackCreate
import requests
import json
from app.config import settings

router = APIRouter()

@router.post("/", response_model=SuccessResponse[dict], status_code=status.HTTP_201_CREATED)
async def create_feedback(feedback: FeedbackCreate, user: dict = Depends(get_current_user)):
    data = feedback.model_dump()
    data["user_id"] = user["user_id"]
    res = supabase.table("feedback").insert(data).execute()

    if feedback.severity == 4:
        # Trigger emergency-alert Edge Function via requests
        url = f"{settings.SUPABASE_URL}/functions/v1/emergency-alert"
        headers = {"Authorization": f"Bearer {settings.SUPABASE_ANON_KEY}", "Content-Type": "application/json"}
        # Fetch provider and contact
        prov = supabase.table("assignments").select("profiles!provider_id(email)").eq("patient_id", user["user_id"]).eq("status", "active").execute()
        cont = supabase.table("emergency_contacts").select("email").eq("user_id", user["user_id"]).execute()
        
        payload = {
            "patient_id": user["user_id"],
            "medicine_name": feedback.medicine_id,
            "description": feedback.description,
            "severity": feedback.severity,
            "provider_email": prov.data[0]["profiles"]["email"] if prov.data else None,
            "emergency_contact_email": cont.data[0]["email"] if cont.data else None
        }
        try:
            requests.post(url, headers=headers, json=payload, timeout=5)
        except Exception:
            pass

    return SuccessResponse(data=res.data[0])

@router.get("/", response_model=SuccessResponse[list])
async def list_feedback(user: dict = Depends(get_current_user)):
    res = supabase.table("feedback").select("*").eq("user_id", user["user_id"]).execute()
    return SuccessResponse(data=res.data)
