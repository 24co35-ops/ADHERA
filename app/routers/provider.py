from fastapi import APIRouter, Depends
from app.db.supabase import supabase
from app.auth.dependencies import require_role

router = APIRouter()

@router.get("/dashboard")
async def get_provider_dashboard(user = Depends(require_role("provider"))):
    # 1. Fetch assigned patients
    assignments = supabase.table("assignments")\
        .select("patient_id, profiles(id, full_name, email, contact_number)")\
        .eq("provider_id", user["user_id"])\
        .eq("status", "active")\
        .execute()
    
    patients = [a["profiles"] for a in assignments.data]
    patient_ids = [p["id"] for p in patients]
    
    if not patient_ids:
        return {
            "stats": {"avg_adherence": 0, "active_patients": 0, "critical_risk": 0},
            "patients": [],
            "alerts": []
        }

    # 2. Fetch adherence summary (daily stats)
    # Fetch data from the last 7 days for risk analysis
    week_ago = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
    adherence_data = supabase.table("adherence")\
        .select("user_id, status")\
        .in_("user_id", patient_ids)\
        .gte("scheduled_utc", week_ago)\
        .execute()
    
    # 3. Fetch recent side-effect alerts (ADH-FR-42)
    alerts = supabase.table("feedback")\
        .select("*, profiles(full_name), medicines(name)")\
        .in_("user_id", patient_ids)\
        .order("created_at", desc=True)\
        .limit(10)\
        .execute()

    # Process stats
    patient_stats = {pid: {"taken": 0, "total": 0} for pid in patient_ids}
    for d in adherence_data.data:
        uid = d["user_id"]
        patient_stats[uid]["total"] += 1
        if d["status"] == "taken":
            patient_stats[uid]["taken"] += 1
            
    critical_risk_count = 0
    total_taken = 0
    total_scheduled = 0
    
    for pid, s in patient_stats.items():
        total_taken += s["taken"]
        total_scheduled += s["total"]
        rate = (s["taken"] / s["total"]) if s["total"] > 0 else 1.0
        if rate < 0.7:
            critical_risk_count += 1

    avg_adherence = (total_taken / total_scheduled * 100) if total_scheduled > 0 else 0

    return {
        "stats": {
            "avg_adherence": round(avg_adherence, 1),
            "active_patients": len(patient_ids),
            "critical_risk": critical_risk_count
        },
        "patients": patients,
        "alerts": alerts.data
    }

@router.get("/patients")
async def get_patients(user = Depends(require_role("provider"))):
    # Fetch patients assigned to this provider
    response = supabase.table("assignments")\
        .select("profiles(full_name, contact_number)")\
        .eq("provider_id", user["user_id"])\
        .eq("status", "active")\
        .execute()
    return response.data
