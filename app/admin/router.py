from fastapi import APIRouter, Depends, HTTPException, Query, Request
from app.db.supabase import supabase
from app.auth.dependencies import require_role
from app.core.responses import SuccessResponse
from app.admin.schemas import AssignmentCreate, AssignmentUpdate, UserUpdate, RejectBody
from app.services.audit import log_audit_action
from app.core.rate_limit import limiter

router = APIRouter()

@router.get("/users", response_model=SuccessResponse[list])
@limiter.limit("60/minute")
async def list_users(
    request: Request,
    role: str = Query("all"),
    status: str = Query("all"),
    user: dict = Depends(require_role("admin"))
):
    q = supabase.table("profiles").select("*")
    if role != "all":
        q = q.eq("role", role)
    if status == "pending":
        q = q.eq("is_active", False)
    elif status == "active":
        q = q.eq("is_active", True)
    res = q.execute()
    from app.core.utils import calculate_age
    for p in res.data:
        p["age"] = calculate_age(p.get("date_of_birth"))
    try:
        users = supabase.auth.admin.list_users()
        email_map = {u.id: u.email for u in users}
        for p in res.data:
            p["email"] = email_map.get(p["id"])
    except Exception:
        pass
    return SuccessResponse(data=res.data)

@router.get("/users/{id}", response_model=SuccessResponse[dict])
@limiter.limit("60/minute")
async def get_user(request: Request, id: str, user: dict = Depends(require_role("admin"))):
    res = supabase.table("profiles").select("*").eq("id", id).execute()
    if not res.data: raise HTTPException(404, "Not found")
    profile = res.data[0]
    from app.core.utils import calculate_age
    profile["age"] = calculate_age(profile.get("date_of_birth"))
    try:
        u = supabase.auth.admin.get_user_by_id(id)
        profile["email"] = u.user.email
    except Exception:
        pass
    return SuccessResponse(data=profile)

@router.patch("/users/{id}", response_model=SuccessResponse[dict])
@limiter.limit("60/minute")
async def update_user(request: Request, id: str, payload: UserUpdate, user: dict = Depends(require_role("admin"))):
    data = payload.model_dump(exclude_unset=True)
    if not data: raise HTTPException(400, "No fields to update")
    res = supabase.table("profiles").update(data).eq("id", id).execute()
    log_audit_action("ADMIN_USER_UPDATE", user["user_id"], {"target": id})
    return SuccessResponse(data=res.data[0])

@router.post("/users/{id}/approve", response_model=SuccessResponse[dict])
@limiter.limit("60/minute")
async def approve_user(request: Request, id: str, user: dict = Depends(require_role("admin"))):
    res = supabase.table("profiles").update({"is_active": True}).eq("id", id).execute()
    if not res.data: raise HTTPException(404, "User not found")
    log_audit_action("USER_APPROVED", user["user_id"], {"target": id})
    return SuccessResponse(data=res.data[0])

@router.post("/users/{id}/reject", response_model=SuccessResponse[dict])
@limiter.limit("60/minute")
async def reject_user(request: Request, id: str, body: RejectBody, user: dict = Depends(require_role("admin"))):
    if not body.reason.strip():
        raise HTTPException(400, "Rejection reason is required")
    res = supabase.table("profiles").update({"is_active": False}).eq("id", id).execute()
    if not res.data: raise HTTPException(404, "User not found")
    log_audit_action("USER_REJECTED", user["user_id"], {"target": id, "reason": body.reason})
    return SuccessResponse(data=res.data[0])

# Keep legacy routes for backward compat
@router.get("/providers/pending", response_model=SuccessResponse[list])
@limiter.limit("60/minute")
async def pending_providers(request: Request, user: dict = Depends(require_role("admin"))):
    res = supabase.table("profiles").select("*").eq("role", "provider").eq("is_active", False).execute()
    try:
        users = supabase.auth.admin.list_users()
        email_map = {u.id: u.email for u in users}
        for p in res.data:
            p["email"] = email_map.get(p["id"])
    except Exception:
        pass
    return SuccessResponse(data=res.data)

@router.post("/providers/{id}/approve", response_model=SuccessResponse[dict])
@limiter.limit("60/minute")
async def approve_provider(request: Request, id: str, user: dict = Depends(require_role("admin"))):
    return await approve_user(request, id, user)

@router.post("/providers/{id}/reject", response_model=SuccessResponse[dict])
@limiter.limit("60/minute")
async def reject_provider(request: Request, id: str, user: dict = Depends(require_role("admin"))):
    return await reject_user(request, id, RejectBody(reason="Legacy reject"), user)

@router.get("/assignments", response_model=SuccessResponse[list])
@limiter.limit("60/minute")
async def list_assignments(request: Request, user: dict = Depends(require_role("admin"))):
    res = supabase.table("assignments").select("*").execute()
    return SuccessResponse(data=res.data)

@router.post("/assignments", response_model=SuccessResponse[dict])
@limiter.limit("60/minute")
async def create_assignment(request: Request, payload: AssignmentCreate, user: dict = Depends(require_role("admin"))):
    res = supabase.table("assignments").insert(payload.model_dump()).execute()
    log_audit_action("ADMIN_ASSIGNMENT_CREATE", user["user_id"], {"target": payload.patient_id})
    return SuccessResponse(data=res.data[0])

@router.patch("/assignments/{id}", response_model=SuccessResponse[dict])
@limiter.limit("60/minute")
async def update_assignment(request: Request, id: str, payload: AssignmentUpdate, user: dict = Depends(require_role("admin"))):
    res = supabase.table("assignments").update(payload.model_dump()).eq("id", id).execute()
    log_audit_action("ADMIN_ASSIGNMENT_UPDATE", user["user_id"], {"target": id})
    return SuccessResponse(data=res.data[0])
