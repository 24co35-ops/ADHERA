from fastapi import APIRouter, Depends
from app.db.supabase import supabase
from app.auth.dependencies import get_current_user

router = APIRouter()

@router.get("/dashboard")
async def get_dashboard_data(user = Depends(get_current_user)):
    # 1. Get adherence rate
    adherence = supabase.table("adherence").select("status").eq("user_id", user["user_id"]).execute()
    
    total = len(adherence.data)
    taken = len([x for x in adherence.data if x['status'] == 'taken'])
    rate = (taken / total * 100) if total > 0 else 0
    
    return {
        "adherence_rate": rate,
        "total_doses": total,
        "taken_doses": taken
    }
