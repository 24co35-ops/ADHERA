from fastapi import APIRouter, Depends, HTTPException
from app.db.supabase import supabase
from app.auth.dependencies import require_role
from app.core.responses import SuccessResponse

router = APIRouter()

@router.get("/patients", response_model=SuccessResponse[list])
async def list_patients(user: dict = Depends(require_role("provider"))):
    res = supabase.table("assignments").select("patient_id, profiles(full_name, contact_number)").eq("provider_id", user["user_id"]).eq("status", "active").execute()
    return SuccessResponse(data=res.data)

@router.get("/patients/{id}", response_model=SuccessResponse[dict])
async def get_patient(id: str, user: dict = Depends(require_role("provider"))):
    res = supabase.table("profiles").select("*").eq("id", id).execute()
    if not res.data: raise HTTPException(status_code=404, detail="Not found")
    return SuccessResponse(data=res.data[0])

@router.get("/patients/{id}/report", response_model=SuccessResponse[dict])
async def get_patient_report(id: str, user: dict = Depends(require_role("provider"))):
    res = supabase.table("reports").select("*").eq("user_id", id).order("created_at", desc=True).limit(1).execute()
    return SuccessResponse(data=res.data[0] if res.data else {})
