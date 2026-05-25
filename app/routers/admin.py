from fastapi import APIRouter, Depends
from app.db.supabase import supabase_admin
from app.auth.dependencies import require_role

router = APIRouter()

@router.get("/users")
async def list_users(user = Depends(require_role("admin"))):
    response = supabase_admin.table("profiles").select("*").execute()
    return response.data

@router.post("/providers/{id}/approve")
async def approve_provider(id: str, user = Depends(require_role("admin"))):
    response = supabase_admin.table("profiles").update({"is_active": True}).eq("id", id).execute()
    return response.data
