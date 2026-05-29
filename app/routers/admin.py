from fastapi import APIRouter, Depends, HTTPException, Request
from app.db.supabase import supabase_admin
from app.auth.dependencies import require_role
from datetime import datetime, timezone

router = APIRouter()

async def log_system_event(actor_id: str, action_code: str, target_id: str = None, reason: str = None):
    """
    ADH-FR-45: System Audit Log (Append-only)
    """
    if not supabase_admin:
        print(f"[AUDIT] actor={actor_id} action={action_code} target={target_id} reason={reason}")
        return
    data = {
        "actor_id": actor_id,
        "action_code": action_code,
        "target_id": target_id,
        "reason": reason,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    supabase_admin.table("audit_log").insert(data).execute()

@router.get("/users")
async def list_users(user = Depends(require_role("admin"))):
    if not supabase_admin:
        raise HTTPException(status_code=503, detail="Admin service unavailable: SUPABASE_SERVICE_ROLE_KEY not configured")
    response = supabase_admin.table("profiles").select("*").order("created_at", desc=True).execute()
    return response.data

@router.get("/audit-logs")
async def list_audit_logs(user = Depends(require_role("admin"))):
    if not supabase_admin:
        raise HTTPException(status_code=503, detail="Admin service unavailable: SUPABASE_SERVICE_ROLE_KEY not configured")
    response = supabase_admin.table("audit_log").select("*, profiles:actor_id(full_name)").order("created_at", desc=True).limit(100).execute()
    return response.data

@router.post("/providers/{id}/approve")
async def approve_provider(id: str, user = Depends(require_role("admin"))):
    if not supabase_admin:
        raise HTTPException(status_code=503, detail="Admin service unavailable: SUPABASE_SERVICE_ROLE_KEY not configured")
    # 1. Update status
    response = supabase_admin.table("profiles").update({"is_active": True}).eq("id", id).execute()
    
    # 2. Log event
    await log_system_event(user["user_id"], "PROVIDER_APPROVE", target_id=id)
    
    return response.data
