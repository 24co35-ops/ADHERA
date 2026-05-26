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
    
    # Emergency escalation (Severity 4)
    if feedback.severity == 4:
        # Here we would trigger an edge function or send an email
        # For a fully functional local build, we could log it
        print(f"EMERGENCY ALERT for user {user['user_id']}: {feedback.description}")
        
    return response.data[0]

@router.get("/")
async def list_feedback(user = Depends(get_current_user)):
    response = supabase.table("feedback").select("*").eq("user_id", user["user_id"]).execute()
    return response.data
