from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException

from app.auth.dependencies import get_current_user
from app.db.supabase import supabase

router = APIRouter(tags=["assignments"])


def _attach_provider_profile(row: dict) -> dict:
    """Fetch provider profile separately (assignments.provider_id → auth.users, not profiles)."""
    provider_id = row.get("provider_id")
    if not provider_id:
        return row
    try:
        prof = supabase.table("profiles").select("id, full_name, contact_number").eq("id", provider_id).single().execute()
        row["profiles"] = prof.data or {}
    except Exception:
        row["profiles"] = {}
    try:
        u = supabase.auth.admin.get_user_by_id(provider_id)
        row["profiles"]["email"] = u.user.email
    except Exception:
        row["profiles"].setdefault("email", "")
    return row


@router.get("/assignments/my-provider")
async def get_my_provider(user=Depends(get_current_user)):
    try:
        result = supabase.table("assignments").select("*").eq("patient_id", user["user_id"]).eq("status", "active").execute()
        if result.data:
            row = _attach_provider_profile(result.data[0])
            return {"success": True, "assigned": True, "data": row}
        return {"success": True, "assigned": False, "data": None}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/assignments/search-providers")
async def search_providers(query: str = "", user=Depends(get_current_user)):
    try:
        q = supabase.table("profiles").select("id, full_name, contact_number").eq("role", "provider").eq("is_active", True)
        if query:
            q = q.ilike("full_name", f"%{query}%")
        result = q.limit(20).execute()
        data = result.data or []
        try:
            auth_users = supabase.auth.admin.list_users()
            email_map = {u.id: u.email for u in auth_users}
            for p in data:
                p["email"] = email_map.get(p["id"], "")
        except Exception:
            for p in data:
                p["email"] = ""
        return {"success": True, "data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/assignments/request")
async def request_provider(payload: dict, user=Depends(get_current_user)):
    try:
        provider_id = payload.get("provider_id")
        if not provider_id:
            raise HTTPException(status_code=400, detail="provider_id is required")
        existing = supabase.table("assignments").select("id").eq("patient_id", user["user_id"]).eq("status", "active").execute().data
        if existing:
            raise HTTPException(status_code=409, detail="You are already assigned to a provider")
        pending = supabase.table("assignments").select("id").eq("patient_id", user["user_id"]).eq("status", "pending").execute().data
        if pending:
            raise HTTPException(status_code=409, detail="You already have a pending request")
        supabase.table("assignments").insert({
            "patient_id": user["user_id"],
            "provider_id": provider_id,
            "status": "pending",
            "assigned_on": datetime.now(timezone.utc).isoformat()
        }).execute()
        return {"success": True, "message": "Request sent to provider successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/assignments/request")
async def cancel_request(user=Depends(get_current_user)):
    try:
        supabase.table("assignments").update({"status": "cancelled"}).eq("patient_id", user["user_id"]).eq("status", "pending").execute()
        return {"success": True, "message": "Request cancelled"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
