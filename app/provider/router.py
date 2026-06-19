from fastapi import APIRouter, Depends, HTTPException, Request
from app.db.supabase import supabase
from app.auth.dependencies import require_role
from app.core.responses import SuccessResponse
from app.core.rate_limit import limiter

router = APIRouter()

@router.get("/patients", response_model=SuccessResponse[list])
@limiter.limit("60/minute")
async def list_patients(request: Request, user: dict = Depends(require_role("provider"))):
    assignments = supabase.table("assignments").select("patient_id").eq("provider_id", user["user_id"]).eq("status", "active").execute()
    result = []
    try:
        users = supabase.auth.admin.list_users()
        email_map = {u.id: u.email for u in users}
    except Exception:
        email_map = {}
        
    for a in assignments.data:
        prof = supabase.table("profiles").select("full_name, contact_number").eq("id", a["patient_id"]).execute()
        if prof.data:
            p = prof.data[0]
            p["email"] = email_map.get(a["patient_id"])
            result.append({"patient_id": a["patient_id"], "profiles": p})
    return SuccessResponse(data=result)

@router.get("/patients/{id}", response_model=SuccessResponse[dict])
@limiter.limit("60/minute")
async def get_patient(request: Request, id: str, user: dict = Depends(require_role("provider"))):
    res = supabase.table("profiles").select("*").eq("id", id).execute()
    if not res.data: raise HTTPException(status_code=404, detail="Not found")
    profile = res.data[0]
    try:
        u = supabase.auth.admin.get_user_by_id(id)
        profile["email"] = u.user.email
    except Exception:
        pass
    return SuccessResponse(data=profile)

@router.get("/patients/{id}/report", response_model=SuccessResponse[dict])
@limiter.limit("60/minute")
async def get_patient_report(request: Request, id: str, user: dict = Depends(require_role("provider"))):
    res = supabase.table("reports").select("*").eq("user_id", id).order("created_at", desc=True).limit(1).execute()
    return SuccessResponse(data=res.data[0] if res.data else {})
