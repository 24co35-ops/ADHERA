import os
import csv
import io
import httpx
from datetime import datetime, timezone
from collections import defaultdict, Counter
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import StreamingResponse
from app.db.supabase import supabase
from app.auth.dependencies import require_role
from app.core.responses import SuccessResponse
from app.admin.schemas import AssignmentCreate, AssignmentUpdate, UserUpdate, RejectBody
from app.services.audit import log_audit_action
from app.core.rate_limit import limiter

router = APIRouter()

# ── Platform Stats ────────────────────────────────────────────────────────────

@router.get("/stats")
@limiter.limit("60/minute")
async def get_platform_stats(request: Request, user: dict = Depends(require_role("admin"))):
    try:
        total_users = supabase.table("profiles").select("id", count="exact").execute().count or 0
    except Exception:
        total_users = 0
    try:
        active_providers = supabase.table("profiles").select("id", count="exact").eq("role", "provider").eq("is_active", True).execute().count or 0
    except Exception:
        active_providers = 0
    try:
        pending_providers = supabase.table("profiles").select("id", count="exact").eq("role", "provider").eq("is_active", False).execute().count or 0
    except Exception:
        pending_providers = 0
    try:
        total_medicines = supabase.table("medicines").select("id", count="exact").execute().count or 0
    except Exception:
        total_medicines = 0
    try:
        adherence_data = supabase.table("adherence").select("status").execute().data or []
        taken = sum(1 for r in adherence_data if r.get("status") == "taken")
        rate = round((taken / len(adherence_data)) * 100) if adherence_data else 0
    except Exception:
        rate = 0
    try:
        today = datetime.now(timezone.utc).date().isoformat()
        feedback_today = supabase.table("feedback").select("id", count="exact").gte("created_at", today).execute().count or 0
    except Exception:
        feedback_today = 0
    return SuccessResponse(data={
        "total_users": total_users,
        "active_providers": active_providers,
        "pending_providers": pending_providers,
        "total_medicines": total_medicines,
        "adherence_rate": rate,
        "feedback_today": feedback_today,
    })


# ── System Health ─────────────────────────────────────────────────────────────

@router.get("/health")
@limiter.limit("30/minute")
async def admin_health_check(request: Request, user: dict = Depends(require_role("admin"))):
    results: dict = {"timestamp": datetime.now(timezone.utc).isoformat()}
    try:
        supabase.table("profiles").select("id").limit(1).execute()
        results["database"] = "ok"
    except Exception:
        results["database"] = "error"
    vapid_key = os.environ.get("VAPID_PUBLIC_KEY", "")
    results["push_notifications"] = "ok" if vapid_key else "not_configured"
    resend_key = os.environ.get("RESEND_API_KEY", "")
    results["email_service"] = "ok" if resend_key else "not_configured"
    results["environment"] = os.environ.get("ENVIRONMENT", "unknown")
    return SuccessResponse(data=results)


# ── Critical Feedback ─────────────────────────────────────────────────────────

@router.get("/critical-feedback")
@limiter.limit("60/minute")
async def get_critical_feedback(request: Request, user: dict = Depends(require_role("admin"))):
    try:
        result = supabase.table("feedback").select("*, profiles(full_name, email)").gte("severity", 3).order("created_at", desc=True).execute()
        data = result.data or []
        # Filter unreviewed if column exists
        try:
            unreviewed = [r for r in data if not r.get("admin_reviewed", False)]
        except Exception:
            unreviewed = data
    except Exception:
        unreviewed = []
    return SuccessResponse(data=unreviewed)


@router.patch("/feedback/{feedback_id}/review")
@limiter.limit("60/minute")
async def mark_feedback_reviewed(request: Request, feedback_id: str, user: dict = Depends(require_role("admin"))):
    try:
        supabase.table("feedback").update({"admin_reviewed": True}).eq("id", feedback_id).execute()
    except Exception:
        pass
    return SuccessResponse(data={"reviewed": True})


# ── Analytics ─────────────────────────────────────────────────────────────────

@router.get("/analytics/adherence-trend")
@limiter.limit("30/minute")
async def adherence_trend(request: Request, user: dict = Depends(require_role("admin"))):
    try:
        result = supabase.table("adherence").select("status, created_at").order("created_at").execute()
        daily: dict = defaultdict(lambda: {"taken": 0, "total": 0})
        for r in (result.data or []):
            day = (r.get("created_at") or "")[:10]
            if day:
                daily[day]["total"] += 1
                if r.get("status") == "taken":
                    daily[day]["taken"] += 1
        trend = [
            {"date": d, "rate": round(v["taken"] / v["total"] * 100) if v["total"] > 0 else 0}
            for d, v in sorted(daily.items())[-30:]
        ]
    except Exception:
        trend = []
    return SuccessResponse(data=trend)


@router.get("/analytics/top-side-effects")
@limiter.limit("30/minute")
async def top_side_effects(request: Request, user: dict = Depends(require_role("admin"))):
    try:
        result = supabase.table("feedback").select("side_effect_type").execute()
        counts = Counter(r.get("side_effect_type") or "Unknown" for r in (result.data or []))
        top10 = [{"effect": k, "count": v} for k, v in counts.most_common(10)]
    except Exception:
        top10 = []
    return SuccessResponse(data=top10)


@router.get("/analytics/daily-active-users")
@limiter.limit("30/minute")
async def daily_active_users(request: Request, user: dict = Depends(require_role("admin"))):
    try:
        result = supabase.table("adherence").select("patient_id, created_at").order("created_at").execute()
        daily: dict = defaultdict(set)
        for r in (result.data or []):
            day = (r.get("created_at") or "")[:10]
            pid = r.get("patient_id")
            if day and pid:
                daily[day].add(pid)
        dau = [{"date": d, "users": len(uids)} for d, uids in sorted(daily.items())[-30:]]
    except Exception:
        dau = []
    return SuccessResponse(data=dau)


@router.get("/analytics/missed-medicines")
@limiter.limit("30/minute")
async def missed_medicines(request: Request, user: dict = Depends(require_role("admin"))):
    try:
        result = supabase.table("adherence").select("medicine_id, status, medicines(name)").eq("status", "missed").execute()
        counts: dict = defaultdict(lambda: {"name": "", "count": 0})
        for r in (result.data or []):
            mid = r.get("medicine_id") or "unknown"
            counts[mid]["name"] = (r.get("medicines") or {}).get("name", mid)
            counts[mid]["count"] += 1
        top = sorted(counts.values(), key=lambda x: x["count"], reverse=True)[:10]
    except Exception:
        top = []
    return SuccessResponse(data=top)


# ── Data Export ───────────────────────────────────────────────────────────────

@router.get("/export")
@limiter.limit("10/minute")
async def admin_export(request: Request, report: str = "adherence", user: dict = Depends(require_role("admin"))):
    output = io.StringIO()
    writer = csv.writer(output)
    if report == "adherence":
        data = supabase.table("adherence").select("*, profiles(full_name), medicines(name)").execute().data or []
        writer.writerow(["patient_name", "medicine_name", "status", "date"])
        for r in data:
            writer.writerow([
                (r.get("profiles") or {}).get("full_name", ""),
                (r.get("medicines") or {}).get("name", ""),
                r.get("status", ""),
                (r.get("created_at") or "")[:10],
            ])
    elif report == "feedback":
        data = supabase.table("feedback").select("*, profiles(full_name)").execute().data or []
        writer.writerow(["patient_name", "severity", "description", "date"])
        for r in data:
            writer.writerow([
                (r.get("profiles") or {}).get("full_name", ""),
                r.get("severity", ""),
                r.get("description", ""),
                (r.get("created_at") or "")[:10],
            ])
    elif report == "users":
        data = supabase.table("profiles").select("full_name, email, role, is_active, created_at").execute().data or []
        writer.writerow(["full_name", "email", "role", "status", "joined"])
        for r in data:
            writer.writerow([
                r.get("full_name"), r.get("email"), r.get("role"),
                "active" if r.get("is_active") else "inactive",
                (r.get("created_at") or "")[:10],
            ])
    else:
        raise HTTPException(400, "Invalid report type. Use: adherence, feedback, users")
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=adhera_{report}_report.csv"},
    )


# ── Broadcast Announcement ────────────────────────────────────────────────────

@router.post("/broadcast")
@limiter.limit("5/minute")
async def broadcast_announcement(request: Request, payload: dict, user: dict = Depends(require_role("admin"))):
    message = (payload.get("message") or "").strip()
    target = payload.get("target", "all")
    if not message:
        raise HTTPException(400, "Message is required")
    query = supabase.table("profiles").select("id, full_name")
    if target == "patients":
        query = query.eq("role", "patient")
    elif target == "providers":
        query = query.eq("role", "provider")
    users_data = query.execute().data or []
    # Get emails from auth
    try:
        auth_users = supabase.auth.admin.list_users()
        email_map = {u.id: u.email for u in auth_users}
    except Exception:
        email_map = {}
    resend_key = os.environ.get("RESEND_API_KEY")
    sent = 0
    if resend_key:
        for u_row in users_data:
            email = email_map.get(u_row.get("id") or "")
            if not email:
                continue
            try:
                httpx.post(
                    "https://api.resend.com/emails",
                    headers={"Authorization": f"Bearer {resend_key}", "Content-Type": "application/json"},
                    json={
                        "from": "Adhera <24co35@aitdgoa.edu.in>",
                        "to": email,
                        "subject": "Announcement from Adhera",
                        "text": message,
                    },
                    timeout=5,
                )
                sent += 1
            except Exception:
                pass
    return SuccessResponse(data={"sent": sent, "message": f"Announcement sent to {sent} users"})


# ── User Management ───────────────────────────────────────────────────────────

@router.get("/users", response_model=SuccessResponse[list])
@limiter.limit("60/minute")
async def list_users(
    request: Request,
    role: str = Query("all"),
    status: str = Query("all"),
    search: str = Query(""),
    user: dict = Depends(require_role("admin")),
):
    q = supabase.table("profiles").select("*")
    if role != "all":
        q = q.eq("role", role)
    if status == "active":
        q = q.eq("is_active", True)
    elif status in ("pending", "inactive", "suspended"):
        q = q.eq("is_active", False)
    if search:
        q = q.ilike("full_name", f"%{search}%")
    res = q.order("created_at", desc=True).execute()
    from app.core.utils import calculate_age
    for p in res.data:
        p["age"] = calculate_age(p.get("date_of_birth"))
    try:
        auth_users = supabase.auth.admin.list_users()
        email_map = {u.id: u.email for u in auth_users}
        for p in res.data:
            p["email"] = email_map.get(p["id"])
    except Exception:
        pass
    return SuccessResponse(data=res.data)


@router.get("/users/{id}", response_model=SuccessResponse[dict])
@limiter.limit("60/minute")
async def get_user(request: Request, id: str, user: dict = Depends(require_role("admin"))):
    res = supabase.table("profiles").select("*").eq("id", id).execute()
    if not res.data:
        raise HTTPException(404, "Not found")
    profile = res.data[0]
    from app.core.utils import calculate_age
    profile["age"] = calculate_age(profile.get("date_of_birth"))
    try:
        u = supabase.auth.admin.get_user_by_id(id)
        profile["email"] = u.user.email
    except Exception:
        pass
    return SuccessResponse(data=profile)


@router.patch("/users/{id}", response_model=SuccessResponse[dict])
@limiter.limit("60/minute")
async def update_user(request: Request, id: str, payload: UserUpdate, user: dict = Depends(require_role("admin"))):
    data = payload.model_dump(exclude_unset=True)
    if not data:
        raise HTTPException(400, "No fields to update")
    res = supabase.table("profiles").update(data).eq("id", id).execute()
    log_audit_action("ADMIN_USER_UPDATE", user["user_id"], {"target": id})
    return SuccessResponse(data=res.data[0])


@router.patch("/users/{id}/suspend")
@limiter.limit("60/minute")
async def suspend_user(request: Request, id: str, user: dict = Depends(require_role("admin"))):
    supabase.table("profiles").update({"is_active": False}).eq("id", id).execute()
    log_audit_action("USER_SUSPENDED", user["user_id"], {"target": id})
    return SuccessResponse(data={"suspended": True})


@router.patch("/users/{id}/reactivate")
@limiter.limit("60/minute")
async def reactivate_user(request: Request, id: str, user: dict = Depends(require_role("admin"))):
    supabase.table("profiles").update({"is_active": True}).eq("id", id).execute()
    log_audit_action("USER_REACTIVATED", user["user_id"], {"target": id})
    return SuccessResponse(data={"reactivated": True})


@router.patch("/users/{id}/role")
@limiter.limit("30/minute")
async def change_user_role(request: Request, id: str, payload: dict, user: dict = Depends(require_role("admin"))):
    new_role = payload.get("role")
    if new_role not in ["patient", "provider", "admin"]:
        raise HTTPException(400, "Invalid role. Must be: patient, provider, admin")
    supabase.table("profiles").update({"role": new_role}).eq("id", id).execute()
    log_audit_action("USER_ROLE_CHANGED", user["user_id"], {"target": id, "new_role": new_role})
    return SuccessResponse(data={"role": new_role})


@router.post("/users/{id}/approve", response_model=SuccessResponse[dict])
@limiter.limit("60/minute")
async def approve_user(request: Request, id: str, user: dict = Depends(require_role("admin"))):
    res = supabase.table("profiles").update({"is_active": True}).eq("id", id).execute()
    if not res.data:
        raise HTTPException(404, "User not found")
    log_audit_action("USER_APPROVED", user["user_id"], {"target": id})
    return SuccessResponse(data=res.data[0])


@router.post("/users/{id}/reject", response_model=SuccessResponse[dict])
@limiter.limit("60/minute")
async def reject_user(request: Request, id: str, body: RejectBody, user: dict = Depends(require_role("admin"))):
    if not body.reason.strip():
        raise HTTPException(400, "Rejection reason is required")
    res = supabase.table("profiles").update({"is_active": False}).eq("id", id).execute()
    if not res.data:
        raise HTTPException(404, "User not found")
    log_audit_action("USER_REJECTED", user["user_id"], {"target": id, "reason": body.reason})
    return SuccessResponse(data=res.data[0])


# ── Provider Approval (legacy aliases) ───────────────────────────────────────

@router.get("/providers/pending", response_model=SuccessResponse[list])
@limiter.limit("60/minute")
async def pending_providers(request: Request, user: dict = Depends(require_role("admin"))):
    res = supabase.table("profiles").select("*").eq("role", "provider").eq("is_active", False).execute()
    try:
        auth_users = supabase.auth.admin.list_users()
        email_map = {u.id: u.email for u in auth_users}
        for p in res.data:
            p["email"] = email_map.get(p["id"])
    except Exception:
        pass
    return SuccessResponse(data=res.data)


@router.post("/providers/{id}/approve", response_model=SuccessResponse[dict])
@limiter.limit("60/minute")
async def approve_provider_legacy(request: Request, id: str, user: dict = Depends(require_role("admin"))):
    return await approve_user(request, id, user)


@router.post("/providers/{id}/reject", response_model=SuccessResponse[dict])
@limiter.limit("60/minute")
async def reject_provider_legacy(request: Request, id: str, user: dict = Depends(require_role("admin"))):
    return await reject_user(request, id, RejectBody(reason="Legacy reject"), user)


# ── Assignments ───────────────────────────────────────────────────────────────

@router.get("/assignments", response_model=SuccessResponse[list])
@limiter.limit("60/minute")
async def list_assignments(request: Request, user: dict = Depends(require_role("admin"))):
    res = supabase.table("assignments").select("*").execute()
    return SuccessResponse(data=res.data)

@router.get("/providers-list", response_model=SuccessResponse[list])
@limiter.limit("60/minute")
async def get_admin_providers_list(request: Request, user: dict = Depends(require_role("admin"))):
    try:
        providers = supabase.table("profiles").select("*").eq("role", "provider").order("created_at", desc=True).execute().data or []
        try:
            auth_users = supabase.auth.admin.list_users()
            email_map = {u.id: u.email for u in auth_users}
        except Exception:
            email_map = {}
        assignments = supabase.table("assignments").select("id, patient_id, provider_id, status").eq("status", "active").execute().data or []
        provider_assignments = defaultdict(list)
        patient_ids = [a["patient_id"] for a in assignments]
        patients_profiles = {}
        if patient_ids:
            p_res = supabase.table("profiles").select("id, full_name").in_("id", patient_ids).execute().data or []
            patients_profiles = {p["id"]: p["full_name"] for p in p_res}
        for a in assignments:
            pid = a["patient_id"]
            prov_id = a["provider_id"]
            patient_name = patients_profiles.get(pid, "Unknown")
            patient_email = email_map.get(pid, "")
            provider_assignments[prov_id].append({
                "patient_id": pid,
                "full_name": patient_name,
                "email": patient_email,
                "assignment_id": a["id"]
            })
        result = []
        for p in providers:
            prov_id = p["id"]
            assigned_list = provider_assignments[prov_id]
            result.append({
                "id": prov_id,
                "full_name": p.get("full_name"),
                "email": email_map.get(prov_id, ""),
                "is_active": p.get("is_active"),
                "created_at": p.get("created_at"),
                "assigned_patients": assigned_list,
                "patient_count": len(assigned_list)
            })
        return SuccessResponse(data=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/patients-list", response_model=SuccessResponse[list])
@limiter.limit("60/minute")
async def get_admin_patients_list(request: Request, user: dict = Depends(require_role("admin"))):
    try:
        patients = supabase.table("profiles").select("*").eq("role", "patient").order("created_at", desc=True).execute().data or []
        try:
            auth_users = supabase.auth.admin.list_users()
            email_map = {u.id: u.email for u in auth_users}
        except Exception:
            email_map = {}
        assignments = supabase.table("assignments").select("patient_id, provider_id").eq("status", "active").execute().data or []
        assigned_map = {a["patient_id"]: a["provider_id"] for a in assignments}
        provider_ids = list(set(assigned_map.values()))
        providers_profiles = {}
        if provider_ids:
            prov_res = supabase.table("profiles").select("id, full_name").in_("id", provider_ids).execute().data or []
            providers_profiles = {p["id"]: p["full_name"] for p in prov_res}
        result = []
        for p in patients:
            pid = p["id"]
            prov_id = assigned_map.get(pid)
            prov_name = providers_profiles.get(prov_id) if prov_id else "Unassigned"
            result.append({
                "id": pid,
                "full_name": p.get("full_name"),
                "email": email_map.get(pid, ""),
                "is_active": p.get("is_active"),
                "created_at": p.get("created_at"),
                "assigned_provider": prov_name,
                "provider_id": prov_id
            })
        return SuccessResponse(data=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/pending-patient-requests", response_model=SuccessResponse[list])
@limiter.limit("60/minute")
async def get_admin_pending_patient_requests(request: Request, user: dict = Depends(require_role("admin"))):
    try:
        res = supabase.table("assignments").select("*").eq("status", "pending").eq("initiated_by", "patient").execute().data or []
        if not res:
            return SuccessResponse(data=[])
        user_ids = list(set([r["patient_id"] for r in res] + [r["provider_id"] for r in res]))
        profiles = {}
        if user_ids:
            p_res = supabase.table("profiles").select("id, full_name").in_("id", user_ids).execute().data or []
            profiles = {p["id"]: p["full_name"] for p in p_res}
        try:
            auth_users = supabase.auth.admin.list_users()
            email_map = {u.id: u.email for u in auth_users}
        except Exception:
            email_map = {}
        result = []
        for r in res:
            pid = r["patient_id"]
            prov_id = r["provider_id"]
            result.append({
                "assignment_id": r["id"],
                "patient_id": pid,
                "patient_name": profiles.get(pid, "Unknown"),
                "patient_email": email_map.get(pid, ""),
                "requested_provider_name": profiles.get(prov_id, "Unknown"),
                "provider_email": email_map.get(prov_id, ""),
                "requested_on": r["assigned_on"] or r["created_at"]
            })
        return SuccessResponse(data=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/pending-provider-requests", response_model=SuccessResponse[list])
@limiter.limit("60/minute")
async def get_admin_pending_provider_requests(request: Request, user: dict = Depends(require_role("admin"))):
    try:
        res = supabase.table("assignments").select("*").eq("status", "pending").eq("initiated_by", "provider").execute().data or []
        if not res:
            return SuccessResponse(data=[])
        user_ids = list(set([r["patient_id"] for r in res] + [r["provider_id"] for r in res]))
        profiles = {}
        if user_ids:
            p_res = supabase.table("profiles").select("id, full_name").in_("id", user_ids).execute().data or []
            profiles = {p["id"]: p["full_name"] for p in p_res}
        try:
            auth_users = supabase.auth.admin.list_users()
            email_map = {u.id: u.email for u in auth_users}
        except Exception:
            email_map = {}
        result = []
        for r in res:
            pid = r["patient_id"]
            prov_id = r["provider_id"]
            result.append({
                "assignment_id": r["id"],
                "patient_id": pid,
                "patient_name": profiles.get(pid, "Unknown"),
                "patient_email": email_map.get(pid, ""),
                "provider_name": profiles.get(prov_id, "Unknown"),
                "provider_email": email_map.get(prov_id, ""),
                "requested_on": r["assigned_on"] or r["created_at"]
            })
        return SuccessResponse(data=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/all-assignments", response_model=SuccessResponse[list])
@limiter.limit("60/minute")
async def get_admin_all_assignments(request: Request, user: dict = Depends(require_role("admin"))):
    try:
        res = supabase.table("assignments").select("*").eq("status", "active").execute().data or []
        if not res:
            return SuccessResponse(data=[])
        user_ids = list(set([r["patient_id"] for r in res] + [r["provider_id"] for r in res]))
        profiles = {}
        if user_ids:
            p_res = supabase.table("profiles").select("id, full_name").in_("id", user_ids).execute().data or []
            profiles = {p["id"]: p["full_name"] for p in p_res}
        try:
            auth_users = supabase.auth.admin.list_users()
            email_map = {u.id: u.email for u in auth_users}
        except Exception:
            email_map = {}
        result = []
        for r in res:
            pid = r["patient_id"]
            prov_id = r["provider_id"]
            initiated = r.get("initiated_by", "patient")
            assigned_by = "Admin" if initiated == "admin" else "Self"
            result.append({
                "assignment_id": r["id"],
                "patient_name": profiles.get(pid, "Unknown"),
                "patient_email": email_map.get(pid, ""),
                "provider_name": profiles.get(prov_id, "Unknown"),
                "provider_email": email_map.get(prov_id, ""),
                "assigned_on": r["assigned_on"] or r["created_at"],
                "assigned_by": assigned_by
            })
        return SuccessResponse(data=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/assignments", response_model=SuccessResponse[dict])
@limiter.limit("60/minute")
async def admin_create_assignment(request: Request, payload: dict, user: dict = Depends(require_role("admin"))):
    try:
        patient_id = payload.get("patient_id")
        provider_id = payload.get("provider_id")
        if not patient_id or not provider_id:
            raise HTTPException(400, "patient_id and provider_id are required")
        existing = supabase.table("assignments").select("id").eq("patient_id", patient_id).eq("status", "active").execute().data
        if existing:
            raise HTTPException(409, "Patient is already assigned to a provider")
        supabase.table("assignments").insert({
            "patient_id": patient_id,
            "provider_id": provider_id,
            "status": "active",
            "initiated_by": "admin",
            "assigned_on": datetime.now(timezone.utc).isoformat(),
        }).execute()
        log_audit_action("ADMIN_ASSIGNMENT_CREATE", user["user_id"], {"patient": patient_id, "provider": provider_id})
        return SuccessResponse(data={"message": "Assignment created successfully"})
    except HTTPException:
        raise
    except Exception as e:
        err_msg = str(e)
        if "duplicate key" in err_msg or "unique constraint" in err_msg:
            raise HTTPException(status_code=409, detail="Duplicate key violation: assignment already exists.")
        raise HTTPException(status_code=500, detail=err_msg)

@router.patch("/assignments/{assignment_id}/approve", response_model=SuccessResponse[dict])
@limiter.limit("60/minute")
async def admin_approve_assignment(request: Request, assignment_id: str, user: dict = Depends(require_role("admin"))):
    try:
        res = supabase.table("assignments").update({
            "status": "active",
            "updated_at": datetime.now(timezone.utc).isoformat()
        }).eq("id", assignment_id).execute().data
        if not res:
            raise HTTPException(404, "Assignment not found")
        log_audit_action("ADMIN_ASSIGNMENT_APPROVE", user["user_id"], {"assignment_id": assignment_id})
        return SuccessResponse(data={"message": "Assignment approved successfully"})
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.patch("/assignments/{assignment_id}/reject", response_model=SuccessResponse[dict])
@limiter.limit("60/minute")
async def admin_reject_assignment(request: Request, assignment_id: str, user: dict = Depends(require_role("admin"))):
    try:
        res = supabase.table("assignments").update({
            "status": "declined",
            "updated_at": datetime.now(timezone.utc).isoformat()
        }).eq("id", assignment_id).execute().data
        if not res:
            raise HTTPException(404, "Assignment not found")
        log_audit_action("ADMIN_ASSIGNMENT_REJECT", user["user_id"], {"assignment_id": assignment_id})
        return SuccessResponse(data={"message": "Assignment rejected successfully"})
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/assignments/{assignment_id}", response_model=SuccessResponse[dict])
@limiter.limit("60/minute")
async def admin_delete_assignment(request: Request, assignment_id: str, user: dict = Depends(require_role("admin"))):
    try:
        res = supabase.table("assignments").update({
            "status": "removed",
            "updated_at": datetime.now(timezone.utc).isoformat()
        }).eq("id", assignment_id).execute().data
        if not res:
            raise HTTPException(404, "Assignment not found")
        log_audit_action("ADMIN_ASSIGNMENT_REMOVE", user["user_id"], {"assignment_id": assignment_id})
        return SuccessResponse(data={"message": "Assignment removed successfully"})
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.patch("/assignments/{id}", response_model=SuccessResponse[dict])
@limiter.limit("60/minute")
async def update_assignment(request: Request, id: str, payload: AssignmentUpdate, user: dict = Depends(require_role("admin"))):
    res = supabase.table("assignments").update(payload.model_dump()).eq("id", id).execute()
    log_audit_action("ADMIN_ASSIGNMENT_UPDATE", user["user_id"], {"target": id})
    return SuccessResponse(data=res.data[0])

@router.get("/providers-with-patients")
@limiter.limit("30/minute")
async def get_providers_with_patients(request: Request, user: dict = Depends(require_role("admin"))):
    providers = supabase.table("profiles").select("id, full_name, is_active, role").eq("role", "provider").execute().data or []
    try:
        auth_users = supabase.auth.admin.list_users()
        email_map = {u.id: u.email for u in auth_users}
    except Exception:
        email_map = {}
    for p in providers:
        p["email"] = email_map.get(p["id"], "")
        assignments = supabase.table("assignments").select(
            "patient_id, profiles!assignments_patient_id_fkey(id, full_name)"
        ).eq("provider_id", p["id"]).eq("status", "active").execute().data or []
        for a in assignments:
            pid = (a.get("profiles") or {}).get("id") or a.get("patient_id")
            if pid and a.get("profiles"):
                a["profiles"]["email"] = email_map.get(pid, "")
        p["assigned_patients"] = assignments
        p["patient_count"] = len(assignments)
    return SuccessResponse(data=providers)

@router.get("/unassigned-patients")
@limiter.limit("30/minute")
async def get_unassigned_patients(request: Request, user: dict = Depends(require_role("admin"))):
    all_patients = supabase.table("profiles").select("id, full_name").eq("role", "patient").execute().data or []
    assigned_ids = [r["patient_id"] for r in supabase.table("assignments").select("patient_id").eq("status", "active").execute().data or []]
    unassigned = [p for p in all_patients if p["id"] not in assigned_ids]
    try:
        auth_users = supabase.auth.admin.list_users()
        email_map = {u.id: u.email for u in auth_users}
        for p in unassigned:
            p["email"] = email_map.get(p["id"], "")
    except Exception:
        pass
    return SuccessResponse(data=unassigned)


