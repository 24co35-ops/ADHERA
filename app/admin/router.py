from fastapi import APIRouter, Depends, HTTPException, Query
from app.db.supabase import supabase_admin
from app.auth.dependencies import require_role
from app.core.responses import SuccessResponse
from app.admin.schemas import AssignmentCreate, AssignmentUpdate, UserUpdate, RejectBody
from app.services.audit import log_audit_action

router = APIRouter()

@router.get("/users", response_model=SuccessResponse[list])
async def list_users(
    role: str = Query("all"),
    status: str = Query("all"),
    user: dict = Depends(require_role("admin"))
):
    q = supabase_admin.table("profiles").select("*")
    if role != "all":
        q = q.eq("role", role)
    if status == "pending":
        q = q.eq("is_active", False)
    elif status == "active":
        q = q.eq("is_active", True)
    res = q.execute()
    return SuccessResponse(data=res.data)

@router.get("/users/{id}", response_model=SuccessResponse[dict])
async def get_user(id: str, user: dict = Depends(require_role("admin"))):
    res = supabase_admin.table("profiles").select("*").eq("id", id).execute()
    if not res.data: raise HTTPException(404, "Not found")
    return SuccessResponse(data=res.data[0])

@router.patch("/users/{id}", response_model=SuccessResponse[dict])
async def update_user(id: str, payload: UserUpdate, user: dict = Depends(require_role("admin"))):
    data = payload.model_dump(exclude_unset=True)
    if not data: raise HTTPException(400, "No fields to update")
    res = supabase_admin.table("profiles").update(data).eq("id", id).execute()
    log_audit_action("ADMIN_USER_UPDATE", user["user_id"], {"target": id})
    return SuccessResponse(data=res.data[0])

@router.post("/users/{id}/approve", response_model=SuccessResponse[dict])
async def approve_user(id: str, user: dict = Depends(require_role("admin"))):
    res = supabase_admin.table("profiles").update({"is_active": True}).eq("id", id).execute()
    if not res.data: raise HTTPException(404, "User not found")
    log_audit_action("USER_APPROVED", user["user_id"], {"target": id})
    return SuccessResponse(data=res.data[0])

@router.post("/users/{id}/reject", response_model=SuccessResponse[dict])
async def reject_user(id: str, body: RejectBody, user: dict = Depends(require_role("admin"))):
    if not body.reason.strip():
        raise HTTPException(400, "Rejection reason is required")
    res = supabase_admin.table("profiles").update({"is_active": False}).eq("id", id).execute()
    if not res.data: raise HTTPException(404, "User not found")
    log_audit_action("USER_REJECTED", user["user_id"], {"target": id, "reason": body.reason})
    return SuccessResponse(data=res.data[0])

# Keep legacy routes for backward compat
@router.get("/providers/pending", response_model=SuccessResponse[list])
async def pending_providers(user: dict = Depends(require_role("admin"))):
    res = supabase_admin.table("profiles").select("*").eq("role", "provider").eq("is_active", False).execute()
    return SuccessResponse(data=res.data)

@router.post("/providers/{id}/approve", response_model=SuccessResponse[dict])
async def approve_provider(id: str, user: dict = Depends(require_role("admin"))):
    return await approve_user(id, user)

@router.post("/providers/{id}/reject", response_model=SuccessResponse[dict])
async def reject_provider(id: str, user: dict = Depends(require_role("admin"))):
    return await reject_user(id, RejectBody(reason="Legacy reject"), user)

@router.get("/assignments", response_model=SuccessResponse[list])
async def list_assignments(user: dict = Depends(require_role("admin"))):
    res = supabase_admin.table("assignments").select("*").execute()
    return SuccessResponse(data=res.data)

@router.post("/assignments", response_model=SuccessResponse[dict])
async def create_assignment(payload: AssignmentCreate, user: dict = Depends(require_role("admin"))):
    res = supabase_admin.table("assignments").insert(payload.model_dump()).execute()
    log_audit_action("ADMIN_ASSIGNMENT_CREATE", user["user_id"], {"target": payload.patient_id})
    return SuccessResponse(data=res.data[0])

@router.patch("/assignments/{id}", response_model=SuccessResponse[dict])
async def update_assignment(id: str, payload: AssignmentUpdate, user: dict = Depends(require_role("admin"))):
    res = supabase_admin.table("assignments").update(payload.model_dump()).eq("id", id).execute()
    log_audit_action("ADMIN_ASSIGNMENT_UPDATE", user["user_id"], {"target": id})
    return SuccessResponse(data=res.data[0])
