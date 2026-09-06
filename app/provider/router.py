import logging
from collections import defaultdict
from datetime import datetime, time, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Request

from app.auth.dependencies import get_current_user, require_role
from app.core.rate_limit import limiter
from app.core.responses import SuccessResponse
from app.db.supabase import supabase

logger = logging.getLogger("adhera.provider")
router = APIRouter()

RISK_THRESHOLDS = {
    "CRITICAL": 50,
    "HIGH": 70,
    "MODERATE": 85
}

@router.get("/dashboard", response_model=SuccessResponse[dict])
@limiter.limit("60/minute")
async def get_provider_dashboard(request: Request, user: dict = Depends(require_role("provider"))):
    try:
        assignments_res = supabase.table("assignments").select("patient_id").eq("provider_id", user["user_id"]).eq("status", "active").execute()
        assignments = assignments_res.data or []
        patient_ids = [a["patient_id"] for a in assignments]
        if not patient_ids:
            return SuccessResponse(data={
                "stats": {"avg_adherence": 0.0, "active_patients": 0, "critical_risk": 0},
                "patients": [],
                "alerts": [],
                "insight_flags": []
            })
        profiles_res = supabase.table("profiles").select("id, full_name, contact_number, date_of_birth, blood_group").in_("id", patient_ids).execute()
        profiles = {p["id"]: p for p in (profiles_res.data or [])}
        try:
            auth_users = supabase.auth.admin.list_users()
            email_map = {u.id: u.email for u in auth_users}
        except Exception:
            email_map = {}
        now = datetime.now(timezone.utc)
        d30 = (now - timedelta(days=30)).isoformat()
        d7 = (now - timedelta(days=7)).isoformat()
        adh_res = supabase.table("adherence").select("user_id, status, scheduled_utc").in_("user_id", patient_ids).gte("scheduled_utc", d30).execute()
        patient_adh = defaultdict(list)
        for r in (adh_res.data or []):
            patient_adh[r["user_id"]].append(r)
        def get_rate(data: list) -> float:
            t = len(data)
            tk = len([x for x in data if x['status'] == 'taken'])
            return round((tk / t * 100), 1) if t > 0 else 0.0

        # Batch query 1 — last_dose_taken per patient
        last_dose_res = supabase.table("adherence")\
            .select("user_id, scheduled_utc")\
            .in_("user_id", patient_ids)\
            .eq("status", "taken")\
            .order("scheduled_utc", desc=True).execute()
        last_dose_map = {}
        for r in (last_dose_res.data or []):
            uid = r["user_id"]
            if uid not in last_dose_map:
                last_dose_map[uid] = r["scheduled_utc"]

        # Batch query 2 — missed_today per patient
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
        today_end   = now.replace(hour=23, minute=59, second=59, microsecond=0).isoformat()
        missed_res = supabase.table("adherence")\
            .select("user_id")\
            .in_("user_id", patient_ids)\
            .eq("status", "missed")\
            .gte("scheduled_utc", today_start)\
            .lte("scheduled_utc", today_end).execute()
        missed_map: defaultdict[str, int] = defaultdict(int)
        for r in (missed_res.data or []):
            missed_map[r["user_id"]] += 1

        # Batch query 3 — next_medication per patient
        reminders_res = supabase.table("reminders").select("*, medicines(*)").in_("user_id", patient_ids).eq("is_active", True).execute()
        patient_reminders = defaultdict(list)
        for r in (reminders_res.data or []):
            patient_reminders[r["user_id"]].append(r)

        next_med_map = {}
        for pid in patient_ids:
            rems = patient_reminders.get(pid, [])
            upcoming_for_patient = []
            for r in rems:
                med = r.get("medicines")
                if not med or not med.get("is_active", True):
                    continue
                time_str = r.get("dose_time_utc")
                if not time_str:
                    continue
                try:
                    parts = time_str.split(":")
                    h = int(parts[0])
                    m = int(parts[1])
                    s = int(parts[2]) if len(parts) > 2 else 0
                except Exception:
                    continue

                for day_offset in [0, 1]:
                    d = now.date() + timedelta(days=day_offset)
                    occurrence = datetime.combine(d, time(h, m, s), tzinfo=timezone.utc)
                    if occurrence >= now:
                        rec_type = r.get("recurrence_type")
                        if rec_type == "daily":
                            pass
                        elif rec_type == "weekday":
                            params = r.get("recurrence_params") or []
                            if occurrence.isoweekday() not in params:
                                continue
                        elif rec_type == "alternate":
                            med_start_str = med.get("start_date")
                            if med_start_str:
                                try:
                                    med_start = datetime.strptime(med_start_str, "%Y-%m-%d").date()
                                    days_diff = (occurrence.date() - med_start).days
                                    if days_diff % 2 != 0:
                                        continue
                                except Exception:
                                    pass
                        else:
                            continue

                        upcoming_for_patient.append({
                            "name": med.get("name") or "Unknown",
                            "time": occurrence.isoformat()
                        })
            if upcoming_for_patient:
                upcoming_for_patient.sort(key=lambda x: x["time"])
                next_med_map[pid] = upcoming_for_patient[0]

        from app.core.utils import calculate_age
        patients_list = []
        weekly_percentages = []
        critical_risk_count = 0
        for pid in patient_ids:
            p = profiles.get(pid)
            if not p:
                continue
            p_copy = dict(p)
            p_copy["email"] = email_map.get(pid, "")
            p_copy["age"] = calculate_age(p_copy.get("date_of_birth"))
            user_adh = patient_adh.get(pid, [])
            w_data = [x for x in user_adh if x['scheduled_utc'] >= d7]
            weekly_percentage = get_rate(w_data) if w_data else (get_rate(user_adh) if user_adh else 80.0)
            weekly_percentages.append(weekly_percentage)

            # Risk Level constant derivation
            if weekly_percentage < RISK_THRESHOLDS["CRITICAL"]:
                risk_level = "critical"
            elif weekly_percentage < RISK_THRESHOLDS["HIGH"]:
                risk_level = "high"
            elif weekly_percentage < RISK_THRESHOLDS["MODERATE"]:
                risk_level = "moderate"
            else:
                risk_level = "low"

            if weekly_percentage < 70:
                critical_risk_count += 1

            patients_list.append({
                "patient_id": pid,
                "profiles": p_copy,
                "adherence": {"weekly_percentage": weekly_percentage},
                "risk_level": risk_level,
                "last_dose_taken": last_dose_map.get(pid),
                "missed_today": missed_map.get(pid, 0),
                "next_medication": next_med_map.get(pid)
            })
        avg_adherence = round(sum(weekly_percentages) / len(weekly_percentages), 1) if weekly_percentages else 0.0
        feedback_res = supabase.table("feedback").select("*").in_("user_id", patient_ids).gte("severity", 3).order("created_at", desc=True).limit(10).execute()
        feedback_rows = feedback_res.data or []
        feedback_user_ids = list({f["user_id"] for f in feedback_rows if f.get("user_id")})
        fb_profiles = {}
        if feedback_user_ids:
            fb_prof_res = supabase.table("profiles").select("id, full_name").in_("id", feedback_user_ids).execute()
            fb_profiles = {p["id"]: p.get("full_name") for p in (fb_prof_res.data or [])}

        alerts_list = []
        for f in feedback_rows:
            user_id = f.get("user_id")
            full_name = fb_profiles.get(user_id) or "Unknown Patient"
            alerts_list.append({
                "id": f.get("id"),
                "profiles": {"full_name": full_name},
                "severity": f.get("severity", 3),
                "description": f.get("description", ""),
                "created_at": f.get("created_at")
            })
        try:
            flags_res = supabase.table("patient_flags").select("*, profiles!patient_flags_user_id_fkey(full_name)").in_("user_id", patient_ids).is_("resolved_at", "null").order("severity", desc=True).limit(20).execute()
            insight_flags = []
            for fl in (flags_res.data or []):
                prof_data = fl.get("profiles") or {}
                insight_flags.append({
                    "id": fl.get("id"),
                    "flag_type": fl.get("flag_type"),
                    "severity": fl.get("severity"),
                    "details": fl.get("details", {}),
                    "detected_at": fl.get("detected_at"),
                    "full_name": prof_data.get("full_name", "Unknown Patient")
                })
        except Exception as flags_err:
            logger.warning("patient_flags query failed (table may not exist): %s", str(flags_err))
            insight_flags = []
        return SuccessResponse(data={
            "stats": {"avg_adherence": avg_adherence, "active_patients": len(patients_list), "critical_risk": critical_risk_count},
            "patients": patients_list,
            "alerts": alerts_list,
            "insight_flags": insight_flags
        })
    except Exception as e:
        logger.warning("Provider dashboard error for %s: %s", user.get("user_id"), str(e))
        raise HTTPException(status_code=500, detail=f"Provider dashboard error: {str(e)}")

@router.get("/patients", response_model=SuccessResponse[list])
@limiter.limit("60/minute")
async def list_patients(request: Request, user: dict = Depends(require_role("provider"))):
    assignments = supabase.table("assignments").select("patient_id").eq("provider_id", user["user_id"]).eq("status", "active").execute().data or []
    patient_ids = [a["patient_id"] for a in assignments]
    result: list[dict] = []
    if not patient_ids:
        return SuccessResponse(data=result)

    try:
        users = supabase.auth.admin.list_users()
        email_map = {u.id: u.email for u in users}
    except Exception:
        email_map = {}

    profiles_res = supabase.table("profiles").select("id, full_name, contact_number, date_of_birth, blood_group").in_("id", patient_ids).execute().data or []
    profiles_map = {p["id"]: p for p in profiles_res}

    from app.core.utils import calculate_age
    for a in assignments:
        pid = a["patient_id"]
        p = profiles_map.get(pid)
        if p:
            p_copy = dict(p)
            p_copy["email"] = email_map.get(pid, "")
            p_copy["age"] = calculate_age(p_copy.get("date_of_birth"))
            result.append({"patient_id": pid, "profiles": p_copy})
    return SuccessResponse(data=result)

@router.get("/patients/{id}", response_model=SuccessResponse[dict])
@limiter.limit("60/minute")
async def get_patient(request: Request, id: str, user: dict = Depends(require_role("provider"))):
    assignment = supabase.table("assignments").select("id").eq("provider_id", user["user_id"]).eq("patient_id", id).eq("status", "active").execute()
    if not assignment.data:
        raise HTTPException(status_code=403, detail="Not assigned to this patient")
    res = supabase.table("profiles").select("*").eq("id", id).execute()
    if not res.data:
        raise HTTPException(status_code=404, detail="Not found")
    profile = res.data[0]
    from app.core.utils import calculate_age
    profile["age"] = calculate_age(profile.get("date_of_birth"))
    try:
        u = supabase.auth.admin.get_user_by_id(id)
        profile["email"] = u.user.email
    except Exception:
        pass
    return SuccessResponse(data=profile)

@router.get("/patients/{id}/report", response_model=SuccessResponse[dict])
@limiter.limit("60/minute")
async def get_patient_report(request: Request, id: str, user: dict = Depends(require_role("provider"))):
    res = supabase.table("reports").select("*").eq("user_id", id).order("created_at", desc=True).limit(1).execute()
    return SuccessResponse(data=res.data[0] if res.data else {})

# ── Pending patient requests ──────────────────────────────────────────────────

@router.get("/pending-requests", response_model=SuccessResponse[list])
@limiter.limit("60/minute")
async def get_pending_requests(request: Request, user: dict = Depends(require_role("provider"))):
    result = supabase.table("assignments").select("*") \
        .eq("provider_id", user["user_id"]) \
        .eq("status", "pending") \
        .order("assigned_on", desc=True).execute()
    data = result.data or []
    patient_ids = [row["patient_id"] for row in data if row.get("patient_id")]
    if not patient_ids:
        for row in data:
            row["profiles"] = None
        return SuccessResponse(data=data)

    try:
        auth_users = supabase.auth.admin.list_users()
        email_map = {u.id: u.email for u in auth_users}
    except Exception:
        email_map = {}

    profiles_res = supabase.table("profiles").select(
        "id, full_name, contact_number, date_of_birth, blood_group"
    ).in_("id", patient_ids).execute().data or []
    profiles_map = {p["id"]: p for p in profiles_res}

    from app.core.utils import calculate_age
    for row in data:
        pid = row.get("patient_id")
        p = profiles_map.get(pid) if pid else None
        if p:
            p_copy = dict(p)
            p_copy["email"] = email_map.get(pid, "")
            p_copy["age"] = calculate_age(p_copy.get("date_of_birth"))
            row["profiles"] = p_copy
        else:
            row["profiles"] = None
    return SuccessResponse(data=data)

@router.patch("/requests/{patient_id}/accept")
@limiter.limit("30/minute")
async def accept_patient_request(request: Request, patient_id: str, user: dict = Depends(require_role("provider"))):
    supabase.table("assignments").update({
        "status": "active",
        "assigned_on": datetime.now(timezone.utc).isoformat()
    }).eq("patient_id", patient_id).eq("provider_id", user["user_id"]).eq("status", "pending").execute()
    return SuccessResponse(data={"accepted": True})

@router.patch("/requests/{patient_id}/decline")
@limiter.limit("30/minute")
async def decline_patient_request(request: Request, patient_id: str, user: dict = Depends(require_role("provider"))):
    supabase.table("assignments").update({
        "status": "declined"
    }).eq("patient_id", patient_id).eq("provider_id", user["user_id"]).eq("status", "pending").execute()
    return SuccessResponse(data={"declined": True})

@router.patch("/flags/{flag_id}/resolve")
@limiter.limit("30/minute")
async def resolve_patient_flag(request: Request, flag_id: str, user: dict = Depends(require_role("provider"))):
    # Fetch the flag to get its user_id
    flag_res = supabase.table("patient_flags").select("user_id, resolved_at").eq("id", flag_id).execute()
    if not flag_res.data:
        raise HTTPException(status_code=404, detail="Flag not found")
    flag = flag_res.data[0]
    if flag.get("resolved_at") is not None:
        raise HTTPException(status_code=409, detail="Flag already resolved")
    # Verify the flag's patient is assigned to this provider
    patient_id = flag["user_id"]
    assignment_res = supabase.table("assignments").select("id").eq("provider_id", user["user_id"]).eq("patient_id", patient_id).eq("status", "active").execute()
    if not assignment_res.data:
        raise HTTPException(status_code=403, detail="Not assigned to this patient")
    supabase.table("patient_flags").update({
        "resolved_at": datetime.now(timezone.utc).isoformat()
    }).eq("id", flag_id).execute()
    return SuccessResponse(data={"resolved": True})

# ── Patient self-service: my provider + search + request ──────────────────────

@router.get("/my-provider")
@limiter.limit("60/minute")
async def get_my_provider(request: Request, user: dict = Depends(get_current_user)):
    result = supabase.table("assignments").select("*").eq("patient_id", user["user_id"]).in_("status", ["active", "pending"]).order("assigned_on", desc=True).limit(1).execute()
    if result.data:
        row = result.data[0]
        provider_id = row.get("provider_id")
        if provider_id:
            try:
                prof = supabase.table("profiles").select("id, full_name, contact_number").eq("id", provider_id).single().execute()
                row["profiles"] = prof.data or {}
                u = supabase.auth.admin.get_user_by_id(provider_id)
                row["profiles"]["email"] = u.user.email
            except Exception:
                row.setdefault("profiles", {})
        return SuccessResponse(data={"assigned": row["status"] == "active", "pending": row["status"] == "pending", "assignment": row})
    return SuccessResponse(data={"assigned": False, "pending": False, "assignment": None})

@router.get("/search-providers")
@limiter.limit("60/minute")
async def search_providers(request: Request, query: str = "", user: dict = Depends(get_current_user)):
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
        pass
    return SuccessResponse(data=data)

@router.post("/request-provider")
@limiter.limit("10/minute")
async def request_provider(request: Request, payload: dict, user: dict = Depends(get_current_user)):
    provider_id = payload.get("provider_id")
    if not provider_id:
        raise HTTPException(400, "provider_id is required")
    existing = supabase.table("assignments").select("id, status").eq("patient_id", user["user_id"]).in_("status", ["active", "pending"]).execute().data
    if existing:
        status = existing[0]["status"]
        raise HTTPException(409, "You are already assigned to a provider" if status == "active" else "You already have a pending request")
    supabase.table("assignments").insert({
        "patient_id": user["user_id"],
        "provider_id": provider_id,
        "status": "pending",
        "assigned_on": datetime.now(timezone.utc).isoformat(),
    }).execute()
    return SuccessResponse(data={"requested": True})

@router.delete("/request-provider")
@limiter.limit("10/minute")
async def cancel_provider_request(request: Request, user: dict = Depends(get_current_user)):
    supabase.table("assignments").update({"status": "cancelled"}).eq("patient_id", user["user_id"]).eq("status", "pending").execute()
    return SuccessResponse(data={"cancelled": True})

