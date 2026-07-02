import logging
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from app.auth.dependencies import get_current_user
from app.core.rate_limit import limiter
from app.core.responses import SuccessResponse
from app.db.supabase import supabase

logger = logging.getLogger("adhera.analytics")
router = APIRouter()

def get_rate(data: list) -> float:
    t = len(data)
    tk = len([x for x in data if x.get('status') == 'taken'])
    return round((tk / t * 100), 1) if t > 0 else 0.0

def _check_assignment(provider_id: str, patient_id: str):
    res = supabase.table("assignments").select("id").eq("provider_id", provider_id).eq("patient_id", patient_id).eq("status", "active").execute()
    if not res.data:
        raise HTTPException(status_code=403, detail="Not assigned to this patient")

def _resolve_uid(user: dict, patient_id: str = None):
    role = user.get("role", "patient")
    if role == "patient":
        return user["user_id"]
    elif role == "provider":
        if not patient_id:
            raise HTTPException(status_code=400, detail="patient_id required for provider")
        _check_assignment(user["user_id"], patient_id)
        return patient_id
    elif role == "admin":
        if patient_id:
            return patient_id
        return None  # signals platform-wide
    return user["user_id"]

@router.get("/dashboard", response_model=SuccessResponse[dict])
@limiter.limit("60/minute")
async def get_dashboard(request: Request, patient_id: str = Query(None), user: dict = Depends(get_current_user)):
    try:
        uid = _resolve_uid(user, patient_id)
        now = datetime.now(timezone.utc)

        if uid is None:
            # Admin platform-wide aggregates
            active_patients = supabase.table("profiles").select("id", count="exact").eq("role", "patient").eq("is_active", True).execute()
            today_str = now.strftime("%Y-%m-%d")
            taken_today = supabase.table("adherence").select("id", count="exact").eq("status", "taken").gte("outcome_utc", today_str + "T00:00:00Z").lte("outcome_utc", today_str + "T23:59:59Z").execute()
            missed_today = supabase.table("adherence").select("id", count="exact").eq("status", "missed").gte("outcome_utc", today_str + "T00:00:00Z").lte("outcome_utc", today_str + "T23:59:59Z").execute()
            d30 = (now - timedelta(days=30)).isoformat()
            all_adh = supabase.table("adherence").select("status").gte("scheduled_utc", d30).execute()
            return SuccessResponse(data={
                "overall_adherence_percentage": get_rate(all_adh.data),
                "active_patients_count": active_patients.count or 0,
                "doses_taken_today": taken_today.count or 0,
                "doses_missed_today": missed_today.count or 0,
                "weekly_adherence": get_rate(all_adh.data),
                "monthly_adherence": get_rate(all_adh.data),
                "weekly_warning": False
            })

        res = supabase.table("adherence").select("status, scheduled_utc").eq("user_id", uid).execute()
        w_data = [x for x in res.data if x.get('scheduled_utc', '') >= (now - timedelta(days=7)).isoformat()]
        m_data = [x for x in res.data if x.get('scheduled_utc', '') >= (now - timedelta(days=30)).isoformat()]
        wr = get_rate(w_data)
        mr = get_rate(m_data)
        # Streak calculation
        streak = 0
        dates_with_all_taken = {}
        for r in res.data:
            scheduled = r.get('scheduled_utc', '')
            if not scheduled:
                continue
            d = scheduled[:10]
            if d not in dates_with_all_taken:
                dates_with_all_taken[d] = {'taken': 0, 'total': 0}
            dates_with_all_taken[d]['total'] += 1
            if r.get('status') == 'taken':
                dates_with_all_taken[d]['taken'] += 1
        sorted_dates = sorted(dates_with_all_taken.keys(), reverse=True)
        for d in sorted_dates:
            if dates_with_all_taken[d]['taken'] == dates_with_all_taken[d]['total'] and dates_with_all_taken[d]['total'] > 0:
                streak += 1
            else:
                break
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        missed_this_month = len([x for x in res.data if x.get('status') == 'missed' and x.get('scheduled_utc', '') >= month_start.isoformat()])
        return SuccessResponse(data={
            "weekly_adherence": wr,
            "monthly_adherence": mr,
            "weekly_warning": wr < 70,
            "weekly_percentage": wr,
            "streak": streak,
            "missed_this_month": missed_this_month
        })
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Analytics dashboard error for %s: %s", user.get("user_id"), str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Analytics error: {str(e)}")

@router.get("/adherence", response_model=SuccessResponse[dict])
@limiter.limit("60/minute")
async def get_adherence(request: Request, patient_id: str = Query(None), user: dict = Depends(get_current_user)):
    try:
        uid = _resolve_uid(user, patient_id)
        if uid is None:
            # Admin platform-wide
            now = datetime.now(timezone.utc)
            d30 = (now - timedelta(days=30)).isoformat()
            res = supabase.table("adherence").select("*").gte("scheduled_utc", d30).execute()
            return SuccessResponse(data={"rate": get_rate(res.data), "overall_percentage": get_rate(res.data), "weekly_percentage": get_rate(res.data), "history": res.data[:50]})
        res = supabase.table("adherence").select("*").eq("user_id", uid).execute()
        now = datetime.now(timezone.utc)
        w7 = [x for x in res.data if x.get('scheduled_utc', '') >= (now - timedelta(days=7)).isoformat()]
        return SuccessResponse(data={"rate": get_rate(res.data), "overall_percentage": get_rate(res.data), "weekly_percentage": get_rate(w7), "history": res.data})
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Analytics adherence error for %s: %s", user.get("user_id"), str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Analytics error: {str(e)}")

@router.get("/trend", response_model=SuccessResponse[list])
@limiter.limit("60/minute")
async def get_trend(request: Request, patient_id: str = Query(None), user: dict = Depends(get_current_user)):
    try:
        uid = _resolve_uid(user, patient_id)
        d30 = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
        if uid is None:
            res = supabase.table("adherence").select("status, scheduled_utc").gte("scheduled_utc", d30).execute()
        else:
            res = supabase.table("adherence").select("status, scheduled_utc").eq("user_id", uid).gte("scheduled_utc", d30).execute()
        return SuccessResponse(data=res.data)
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Analytics trend error for %s: %s", user.get("user_id"), str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Analytics error: {str(e)}")
