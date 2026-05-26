from fastapi import APIRouter, Depends
from app.db.supabase import supabase
from app.auth.dependencies import require_role

router = APIRouter()

@router.get("/dashboard")
async def get_provider_dashboard(user = Depends(require_role("provider"))):
    # 1. Fetch assigned patients
    assignments = supabase.table("assignments")\
        .select("patient_id, profiles(id, full_name, contact_number)")\
        .eq("provider_id", user["user_id"])\
        .eq("status", "active")\
        .execute()
    
    patient_ids = [a["patient_id"] for a in assignments.data]
    
    if not patient_ids:
        return {
            "stats": {"avg_adherence": 0, "active_patients": 0, "critical_risk": 0},
            "patients": [],
            "alerts": []
        }

    # 2. Fetch adherence data for these patients
    adherence_data = supabase.table("adherence")\
        .select("user_id, status")\
        .in_("user_id", patient_ids)\
        .execute()
    
    # 3. Fetch recent alerts (feedback/side effects)
    alerts = supabase.table("feedback")\
        .select("*, profiles(full_name)")\
        .in_("user_id", patient_ids)\
        .order("created_at", desc=True)\
        .limit(5)\
        .execute()

    # Calculate stats
    total_doses = len(adherence_data.data)
    taken_doses = len([d for d in adherence_data.data if d["status"] == "taken"])
    avg_adherence = (taken_doses / total_doses * 100) if total_doses > 0 else 0
    
    # Critical risk: patients with < 70% adherence (simplified)
    patient_stats = {}
    for d in adherence_data.data:
        uid = d["user_id"]
        if uid not in patient_stats:
            patient_stats[uid] = {"taken": 0, "total": 0}
        patient_stats[uid]["total"] += 1
        if d["status"] == "taken":
            patient_stats[uid]["taken"] += 1
            
    critical_risk = 0
    for uid, s in patient_stats.items():
        if (s["taken"] / s["total"]) < 0.7:
            critical_risk += 1

    return {
        "stats": {
            "avg_adherence": avg_adherence,
            "active_patients": len(patient_ids),
            "critical_risk": critical_risk
        },
        "patients": assignments.data,
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
