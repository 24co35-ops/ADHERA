import logging
from datetime import datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from app.auth.dependencies import get_current_user
from app.core.exceptions import is_timeout_error
from app.core.rate_limit import limiter
from app.core.responses import SuccessResponse
from app.db.supabase import supabase

logger = logging.getLogger("adhera.analytics")
router = APIRouter()


def get_rate(data: list) -> float:
    final_doses = [x for x in data if x.get("status") in ("taken", "missed")]
    t = len(final_doses)
    tk = len([x for x in final_doses if x.get("status") == "taken"])
    return round((tk / t * 100), 1) if t > 0 else 0.0


def _check_assignment(provider_id: str, patient_id: str):
    try:
        res = (
            supabase.table("assignments")
            .select("id")
            .eq("provider_id", provider_id)
            .eq("patient_id", patient_id)
            .eq("status", "active")
            .execute()
        )
        if not res.data:
            raise HTTPException(status_code=403, detail="Not assigned to this patient")
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error checking assignment for %s -> %s: %s", provider_id, patient_id, str(e))
        if is_timeout_error(e):
            raise HTTPException(status_code=504, detail="Database timeout checking patient assignment")
        raise HTTPException(status_code=503, detail="Unable to verify patient assignment")


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
            active_patients = (
                supabase.table("profiles")
                .select("id", count="exact")
                .eq("role", "patient")
                .eq("is_active", True)
                .execute()
            )
            today_str = now.strftime("%Y-%m-%d")
            taken_today = (
                supabase.table("adherence")
                .select("id", count="exact")
                .eq("status", "taken")
                .gte("outcome_utc", today_str + "T00:00:00Z")
                .lte("outcome_utc", today_str + "T23:59:59Z")
                .execute()
            )
            missed_today = (
                supabase.table("adherence")
                .select("id", count="exact")
                .eq("status", "missed")
                .gte("outcome_utc", today_str + "T00:00:00Z")
                .lte("outcome_utc", today_str + "T23:59:59Z")
                .execute()
            )
            d30 = (now - timedelta(days=30)).isoformat()
            all_adh = supabase.table("adherence").select("status").gte("scheduled_utc", d30).limit(1000).execute()
            return SuccessResponse(data={
                "overall_adherence_percentage": get_rate(all_adh.data or []),
                "active_patients_count": active_patients.count or 0,
                "doses_taken_today": taken_today.count or 0,
                "doses_missed_today": missed_today.count or 0,
                "weekly_adherence": get_rate(all_adh.data or []),
                "monthly_adherence": get_rate(all_adh.data or []),
                "weekly_warning": False,
            })

        # Resolve user timezone
        profile_res = supabase.table("profiles").select("timezone").eq("id", uid).execute()
        user_tz_str = "UTC"
        if profile_res.data:
            user_tz_str = profile_res.data[0].get("timezone") or "UTC"
        try:
            user_tz = ZoneInfo(user_tz_str)
        except Exception:
            user_tz = ZoneInfo("UTC")

        now_local = datetime.now(user_tz)
        today_date = now_local.date()

        # Get reminders
        reminders_res = (
            supabase.table("reminders")
            .select("*, medicines(*)")
            .eq("user_id", uid)
            .eq("is_active", True)
            .execute()
        )

        start_local = datetime.combine(today_date, time.min, tzinfo=user_tz)
        end_local = datetime.combine(today_date, time.max, tzinfo=user_tz)
        start_utc = start_local.astimezone(timezone.utc)
        end_utc = end_local.astimezone(timezone.utc)

        # Get adherence for today (selective columns)
        adherence_res = (
            supabase.table("adherence")
            .select("id, reminder_id, status, scheduled_utc")
            .eq("user_id", uid)
            .gte("scheduled_utc", start_utc.isoformat())
            .lte("scheduled_utc", end_utc.isoformat())
            .execute()
        )

        completed = set()
        today_taken = 0
        for entry in (adherence_res.data or []):
            dt_comp = datetime.fromisoformat(entry["scheduled_utc"].replace("Z", "+00:00"))
            completed.add((entry["reminder_id"], dt_comp))
            if entry.get("status") == "taken":
                today_taken += 1

        # Calculate upcoming
        today_pending = 0
        for reminder in (reminders_res.data or []):
            med = reminder.get("medicines")
            if not med or not med.get("is_active", True):
                continue
            med_start_str = med.get("start_date")
            med_end_str = med.get("end_date")
            if med_start_str:
                med_start = datetime.strptime(med_start_str, "%Y-%m-%d").date()
                if today_date < med_start:
                    continue
            if med_end_str:
                med_end = datetime.strptime(med_end_str, "%Y-%m-%d").date()
                if today_date > med_end:
                    continue

            time_str = reminder.get("dose_time_utc")
            if not time_str:
                continue
            try:
                t = time.fromisoformat(time_str)
            except Exception:
                continue

            today_utc = datetime.now(timezone.utc).date()
            for offset in [-1, 0, 1]:
                d_utc = today_utc + timedelta(days=offset)
                occurrence_utc = datetime.combine(d_utc, t, tzinfo=timezone.utc)
                occurrence_local = occurrence_utc.astimezone(user_tz)

                if occurrence_local.date() == today_date:
                    rec_type = reminder.get("recurrence_type")
                    if rec_type == "daily":
                        pass
                    elif rec_type == "weekday":
                        params = reminder.get("recurrence_params") or []
                        if occurrence_local.isoweekday() not in params:
                            continue
                    elif rec_type == "alternate":
                        if med_start_str:
                            days_diff = (occurrence_local.date() - med_start).days
                            if days_diff % 2 != 0:
                                continue
                    elif rec_type == "prn":
                        pass  # PRN (as-needed) meds are always shown as available
                    else:
                        continue

                    is_completed = False
                    for comp_rem_id, comp_dt in completed:
                        if comp_rem_id == reminder["id"]:
                            if abs((comp_dt - occurrence_utc).total_seconds()) < 60:
                                is_completed = True
                                break
                    if not is_completed:
                        today_pending += 1

        today_total = len(adherence_res.data or []) + today_pending

        def parse_ts(s):
            return datetime.fromisoformat(s.replace("Z", "+00:00")) if s else datetime.min.replace(tzinfo=timezone.utc)

        # Query selective columns for metrics & streak calculation
        res = (
            supabase.table("adherence")
            .select("status, scheduled_utc")
            .eq("user_id", uid)
            .execute()
        )
        adh_data = res.data or []

        cutoff_7 = now - timedelta(days=7)
        cutoff_30 = now - timedelta(days=30)
        w_data = [x for x in adh_data if parse_ts(x.get("scheduled_utc")) >= cutoff_7]
        m_data = [x for x in adh_data if parse_ts(x.get("scheduled_utc")) >= cutoff_30]
        wr = get_rate(w_data)
        mr = get_rate(m_data)

        # Streak calculation
        streak = 0
        dates_with_all_taken = {}
        for r in adh_data:
            scheduled = r.get("scheduled_utc", "")
            if not scheduled:
                continue
            dt_utc = datetime.fromisoformat(scheduled.replace("Z", "+00:00"))
            dt_local = dt_utc.astimezone(user_tz)
            d = dt_local.date().isoformat()
            if d not in dates_with_all_taken:
                dates_with_all_taken[d] = {"taken": 0, "total": 0}
            dates_with_all_taken[d]["total"] += 1
            if r.get("status") == "taken":
                dates_with_all_taken[d]["taken"] += 1

        sorted_dates = sorted(dates_with_all_taken.keys(), reverse=True)
        for d in sorted_dates:
            if dates_with_all_taken[d]["taken"] == dates_with_all_taken[d]["total"] and dates_with_all_taken[d]["total"] > 0:
                streak += 1
            else:
                break

        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        missed_this_month = len([
            x for x in adh_data if x.get("status") == "missed" and parse_ts(x.get("scheduled_utc")) >= month_start
        ])

        return SuccessResponse(data={
            "weekly_adherence": wr,
            "monthly_adherence": mr,
            "weekly_warning": wr < 70,
            "weekly_percentage": wr,
            "streak": streak,
            "missed_this_month": missed_this_month,
            "today_taken": today_taken,
            "today_total": today_total,
        })
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Analytics dashboard error for %s: %s", user.get("user_id"), str(e), exc_info=True)
        if is_timeout_error(e):
            raise HTTPException(status_code=504, detail="Database query timed out while loading dashboard analytics.")
        raise HTTPException(status_code=500, detail=f"Analytics error: {str(e)}")


@router.get("/adherence", response_model=SuccessResponse[dict])
@limiter.limit("60/minute")
async def get_adherence(request: Request, patient_id: str = Query(None), user: dict = Depends(get_current_user)):
    try:
        def parse_ts(s):
            return datetime.fromisoformat(s.replace("Z", "+00:00")) if s else datetime.min.replace(tzinfo=timezone.utc)

        uid = _resolve_uid(user, patient_id)
        now = datetime.now(timezone.utc)
        cutoff_7 = now - timedelta(days=7)

        if uid is None:
            # Admin platform-wide
            d30 = (now - timedelta(days=30)).isoformat()
            res = (
                supabase.table("adherence")
                .select("id, status, scheduled_utc, outcome_utc, reminder_id")
                .gte("scheduled_utc", d30)
                .execute()
            )
            history = res.data or []
            return SuccessResponse(data={
                "rate": get_rate(history),
                "overall_percentage": get_rate(history),
                "weekly_percentage": get_rate(history),
                "history": history[:50],
            })

        # Query selective columns to avoid heavy payload serialization
        res = (
            supabase.table("adherence")
            .select("id, status, scheduled_utc, outcome_utc, reminder_id")
            .eq("user_id", uid)
            .execute()
        )
        history = res.data or []
        w7 = [x for x in history if parse_ts(x.get("scheduled_utc")) >= cutoff_7]
        rate = get_rate(history)
        w_rate = get_rate(w7)

        return SuccessResponse(data={
            "rate": rate,
            "overall_percentage": rate,
            "weekly_percentage": w_rate,
            "history": history,
        })
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Analytics adherence error for %s: %s", user.get("user_id"), str(e), exc_info=True)
        if is_timeout_error(e):
            raise HTTPException(status_code=504, detail="Database query timed out while loading adherence data.")
        raise HTTPException(status_code=500, detail=f"Analytics error: {str(e)}")


@router.get("/trend", response_model=SuccessResponse[list])
@limiter.limit("60/minute")
async def get_trend(request: Request, patient_id: str = Query(None), user: dict = Depends(get_current_user)):
    try:
        uid = _resolve_uid(user, patient_id)
        d30 = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
        if uid is None:
            res = (
                supabase.table("adherence")
                .select("status, scheduled_utc")
                .gte("scheduled_utc", d30)
                .execute()
            )
        else:
            res = (
                supabase.table("adherence")
                .select("status, scheduled_utc")
                .eq("user_id", uid)
                .gte("scheduled_utc", d30)
                .execute()
            )
        return SuccessResponse(data=res.data or [])
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Analytics trend error for %s: %s", user.get("user_id"), str(e), exc_info=True)
        if is_timeout_error(e):
            raise HTTPException(status_code=504, detail="Database query timed out while loading trend data.")
        raise HTTPException(status_code=500, detail=f"Analytics error: {str(e)}")
