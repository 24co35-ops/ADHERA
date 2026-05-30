from fastapi import APIRouter, Depends, HTTPException
from app.db.supabase import supabase
from app.auth.dependencies import require_role
from app.core.responses import SuccessResponse
from app.admin.schemas import AssignmentCreate, AssignmentUpdate, UserUpdate
from app.services.audit import log_audit_action

router = APIRouter()

@router.get("/users/{id}", response_model=SuccessResponse[dict])
async def get_user(id: str, user: dict = Depends(require_role("admin"))):
    res = supabase.table("profiles").select("*").eq("id", id).execute()
    if not res.data: raise HTTPException(404, "Not found")
    return SuccessResponse(data=res.data[0])

@router.patch("/users/{id}", response_model=SuccessResponse[dict])
async def update_user(id: str, payload: UserUpdate, user: dict = Depends(require_role("admin"))):
    res = supabase.table("profiles").update(payload.model_dump()).eq("id", id).execute()
    log_audit_action("ADMIN_USER_UPDATE", None, {"target": id})
    return SuccessResponse(data=res.data[0])

@router.get("/providers/pending", response_model=SuccessResponse[list])
async def pending_providers(user: dict = Depends(require_role("admin"))):
    res = supabase.table("profiles").select("*").eq("role", "provider").eq("is_active", False).execute()
    return SuccessResponse(data=res.data)

@router.post("/providers/{id}/approve", response_model=SuccessResponse[dict])
async def approve_provider(id: str, user: dict = Depends(require_role("admin"))):
    res = supabase.table("profiles").update({"is_active": True}).eq("id", id).execute()
    log_audit_action("ADMIN_PROVIDER_APPROVE", None, {"target": id})
    return SuccessResponse(data=res.data[0])

@router.post("/providers/{id}/reject", response_model=SuccessResponse[dict])
async def reject_provider(id: str, user: dict = Depends(require_role("admin"))):
    res = supabase.table("profiles").update({"is_active": False}).eq("id", id).execute()
    log_audit_action("ADMIN_PROVIDER_REJECT", None, {"target": id})
    return SuccessResponse(data=res.data[0])

@router.get("/assignments", response_model=SuccessResponse[list])
async def list_assignments(user: dict = Depends(require_role("admin"))):
    res = supabase.table("assignments").select("*").execute()
    return SuccessResponse(data=res.data)

@router.post("/assignments", response_model=SuccessResponse[dict])
async def create_assignment(payload: AssignmentCreate, user: dict = Depends(require_role("admin"))):
    res = supabase.table("assignments").insert(payload.model_dump()).execute()
    log_audit_action("ADMIN_ASSIGNMENT_CREATE", None, {"target": payload.patient_id})
    return SuccessResponse(data=res.data[0])

@router.patch("/assignments/{id}", response_model=SuccessResponse[dict])
async def update_assignment(id: str, payload: AssignmentUpdate, user: dict = Depends(require_role("admin"))):
    res = supabase.table("assignments").update(payload.model_dump()).eq("id", id).execute()
    log_audit_action("ADMIN_ASSIGNMENT_UPDATE", None, {"target": id})
    return SuccessResponse(data=res.data[0])
