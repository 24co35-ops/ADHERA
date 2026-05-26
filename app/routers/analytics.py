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

@router.get("/trend")
async def get_adherence_trend(user = Depends(get_current_user)):
    # This is a simplified trend. In a real app, we'd group by day.
    response = supabase.table("adherence")\
        .select("status, scheduled_utc")\
        .eq("user_id", user["user_id"])\
        .order("scheduled_utc", desc=False)\
        .execute()
    
    # Simple grouping by date (mocking real logic for brevity)
    trend = {}
    for entry in response.data:
        date = entry["scheduled_utc"][:10]
        if date not in trend:
            trend[date] = {"taken": 0, "total": 0}
        trend[date]["total"] += 1
        if entry["status"] == "taken":
            trend[date]["taken"] += 1
            
    result = []
    for date, stats in trend.items():
        result.append({
            "date": date,
            "rate": (stats["taken"] / stats["total"] * 100)
        })
        
    return result
