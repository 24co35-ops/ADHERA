from fastapi import APIRouter, Depends
from app.db.supabase import supabase
from app.auth.dependencies import get_current_user
from app.core.responses import SuccessResponse
from datetime import datetime, timezone, timedelta

router = APIRouter()

def get_rate(data: list) -> float:
    t = len(data)
    tk = len([x for x in data if x['status'] == 'taken'])
    return round((tk / t * 100), 1) if t > 0 else 0.0

@router.get("/dashboard", response_model=SuccessResponse[dict])
async def get_dashboard(user: dict = Depends(get_current_user)):
    now = datetime.now(timezone.utc)
    res = supabase.table("adherence").select("status, scheduled_utc").eq("user_id", user["user_id"]).execute()
    w_data = [x for x in res.data if x['scheduled_utc'] >= (now - timedelta(days=7)).isoformat()]
    m_data = [x for x in res.data if x['scheduled_utc'] >= (now - timedelta(days=30)).isoformat()]
    
    wr = get_rate(w_data)
    mr = get_rate(m_data)
    return SuccessResponse(data={"weekly_adherence": wr, "monthly_adherence": mr, "weekly_warning": wr < 70})

@router.get("/adherence", response_model=SuccessResponse[dict])
async def get_adherence(user: dict = Depends(get_current_user)):
    res = supabase.table("adherence").select("*").eq("user_id", user["user_id"]).execute()
    return SuccessResponse(data={"rate": get_rate(res.data), "history": res.data})

@router.get("/trend", response_model=SuccessResponse[list])
async def get_trend(user: dict = Depends(get_current_user)):
    d14 = (datetime.now(timezone.utc) - timedelta(days=14)).isoformat()
    res = supabase.table("adherence").select("status, scheduled_utc").eq("user_id", user["user_id"]).gte("scheduled_utc", d14).execute()
    return SuccessResponse(data=res.data)
