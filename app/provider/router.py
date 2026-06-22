from fastapi import APIRouter, Depends, HTTPException, Request
from datetime import datetime, timezone, timedelta
from collections import defaultdict
from app.db.supabase import supabase
from app.auth.dependencies import require_role, get_current_user
from app.core.responses import SuccessResponse
from app.core.rate_limit import limiter

router = APIRouter()

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
                "alerts": []
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
        from app.core.utils import calculate_age
        patients_list = []
        weekly_percentages = []
        critical_risk_count = 0
        for pid in patient_ids:
            p = profiles.get(pid)
            if not p: continue
            p_copy = dict(p)
            p_copy["email"] = email_map.get(pid, "")
            p_copy["age"] = calculate_age(p_copy.get("date_of_birth"))
            user_adh = patient_adh.get(pid, [])
            w_data = [x for x in user_adh if x['scheduled_utc'] >= d7]
            weekly_percentage = get_rate(w_data) if w_data else (get_rate(user_adh) if user_adh else 80.0)
            weekly_percentages.append(weekly_percentage)
            if weekly_percentage < 70:
                critical_risk_count += 1
            patients_list.append({
                "patient_id": pid,
                "profiles": p_copy,
                "adherence": {"weekly_percentage": weekly_percentage}
            })
        avg_adherence = round(sum(weekly_percentages) / len(weekly_percentages), 1) if weekly_percentages else 0.0
        feedback_res = supabase.table("feedback").select("*, profiles(full_name)").in_("user_id", patient_ids).gte("severity", 3).order("created_at", desc=True).limit(10).execute()
        alerts_list = []
        for f in (feedback_res.data or []):
            prof_data = f.get("profiles") or {}
            alerts_list.append({
                "id": f.get("id"),
                "profiles": {"full_name": prof_data.get("full_name", "Unknown Patient")},
                "severity": f.get("severity", 3),
                "description": f.get("description", ""),
                "created_at": f.get("created_at")
            })
        return SuccessResponse(data={
            "stats": {"avg_adherence": avg_adherence, "active_patients": len(patients_list), "critical_risk": critical_risk_count},
            "patients": patients_list,
            "alerts": alerts_list
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/patients", response_model=SuccessResponse[list])
@limiter.limit("60/minute")
async def list_patients(request: Request, user: dict = Depends(require_role("provider"))):
    assignments = supabase.table("assignments").select("patient_id").eq("provider_id", user["user_id"]).eq("status", "active").execute()
    result = []
    try:
        users = supabase.auth.admin.list_users()
        email_map = {u.id: u.email for u in users}
    except Exception:
        email_map = {}
    from app.core.utils import calculate_age
    for a in assignments.data:
        prof = supabase.table("profiles").select("full_name, contact_number, date_of_birth, blood_group").eq("id", a["patient_id"]).execute()
        if prof.data:
            p = prof.data[0]
            p["email"] = email_map.get(a["patient_id"])
            p["age"] = calculate_age(p.get("date_of_birth"))
            result.append({"patient_id": a["patient_id"], "profiles": p})
    return SuccessResponse(data=result)

@router.get("/patients/{id}", response_model=SuccessResponse[dict])
@limiter.limit("60/minute")
async def get_patient(request: Request, id: str, user: dict = Depends(require_role("provider"))):
    res = supabase.table("profiles").select("*").eq("id", id).execute()
    if not res.data: raise HTTPException(status_code=404, detail="Not found")
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
    try:
        auth_users = supabase.auth.admin.list_users()
        email_map = {u.id: u.email for u in auth_users}
    except Exception:
        email_map = {}
    from app.core.utils import calculate_age
    for row in data:
        pid = row.get("patient_id")
        if pid:
            prof = supabase.table("profiles").select(
                "id, full_name, contact_number, date_of_birth, blood_group"
            ).eq("id", pid).execute()
            if prof.data:
                p = prof.data[0]
                p["email"] = email_map.get(pid)
                p["age"] = calculate_age(p.get("date_of_birth"))
                row["profiles"] = p
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

# ── Patient self-service: my provider + search + request ──────────────────────

@router.get("/my-provider")
@limiter.limit("60/minute")
async def get_my_provider(request: Request, user: dict = Depends(get_current_user)):
    result = supabase.table("assignments").select(
        "*, profiles!assignments_provider_id_fkey(id, full_name, contact_number)"
    ).eq("patient_id", user["user_id"]).in_("status", ["active", "pending"]).order("assigned_on", desc=True).limit(1).execute()
    if result.data:
        row = result.data[0]
        try:
            pid = (row.get("profiles") or {}).get("id") or row.get("provider_id")
            if pid:
                u = supabase.auth.admin.get_user_by_id(pid)
                if row.get("profiles"):
                    row["profiles"]["email"] = u.user.email
        except Exception:
            pass
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

