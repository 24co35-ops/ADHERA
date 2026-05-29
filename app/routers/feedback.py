from fastapi import APIRouter, Depends, HTTPException, status
from app.models.schemas import FeedbackCreate
from app.db.supabase import supabase, supabase_admin
from app.auth.dependencies import get_current_user

router = APIRouter()

@router.post("/")
async def create_feedback(feedback: FeedbackCreate, user = Depends(get_current_user)):
    data = feedback.model_dump()
    data["user_id"] = user["user_id"]
    
    response = supabase.table("feedback").insert(data).execute()
    if not response.data:
        raise HTTPException(status_code=400, detail="Could not record feedback")
    
    # Emergency escalation (Severity 4 - ADH-FR-34)
    if feedback.severity == 4:
        # 1. Fetch assigned provider
        assignment = supabase.table("assignments").select("provider_id").eq("patient_id", user["user_id"]).eq("status", "active").execute()
        provider_email = None
        if assignment.data:
            provider_prof = supabase.table("profiles").select("email").eq("id", assignment.data[0]["provider_id"]).execute()
            if provider_prof.data:
                provider_email = provider_prof.data[0]["email"]

        # 2. Fetch emergency contact
        contact = supabase.table("emergency_contacts").select("email").eq("user_id", user["user_id"]).execute()
        contact_email = contact.data[0]["email"] if contact.data else None

        # 3. Trigger Emergency Dispatch (Simulation via Edge Function call if implemented, or print)
        # Note: In production, we'd use supabase.functions.invoke('dispatch-emergency', ...)
        print(f"!!! EMERGENCY !!! User {user['user_id']} reported Severity 4 side effect.")
        print(f"Alerting Provider: {provider_email}")
        print(f"Alerting Emergency Contact: {contact_email}")
        
    return response.data[0]

@router.get("/")
async def list_feedback(user = Depends(get_current_user)):
    response = supabase.table("feedback").select("*").eq("user_id", user["user_id"]).execute()
    return response.data
