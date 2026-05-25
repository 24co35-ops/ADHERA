from fastapi import APIRouter, Depends
from app.db.supabase import supabase
from app.auth.dependencies import require_role

router = APIRouter()

@router.get("/patients")
async def get_patients(user = Depends(require_role("provider"))):
    # Fetch patients assigned to this provider
    response = supabase.table("assignments")\
        .select("profiles(full_name, contact_number)")\
        .eq("provider_id", user["user_id"])\
        .eq("status", "active")\
        .execute()
    return response.data
