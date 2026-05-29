import csv
import io
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from app.db.supabase import supabase, supabase_admin
from app.auth.dependencies import get_current_user

router = APIRouter()

def calculate_rate(data):
    total = len(data)
    taken = len([x for x in data if x['status'] == 'taken'])
    return round((taken / total * 100), 1) if total > 0 else 0

@router.post("/export/csv")
async def export_adherence_csv(user = Depends(get_current_user)):
    """
    ADH-FR-43: Export data to CSV and upload to Supabase Storage.
    Returns a signed URL for download.
    """
    # 1. Fetch data
    adh_res = supabase.table("adherence")\
        .select("status, scheduled_utc, outcome_utc, reminders(dose_label, medicines(name))")\
        .eq("user_id", user["user_id"])\
        .order("scheduled_utc", desc=True)\
        .execute()
    
    if not adh_res.data:
        raise HTTPException(status_code=404, detail="No adherence data found to export")

    # 2. Generate CSV in memory
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Medicine", "Label", "Scheduled Time (UTC)", "Status", "Outcome Time (UTC)"])
    
    for row in adh_res.data:
        medicine = row["reminders"]["medicines"]["name"]
        label = row["reminders"]["dose_label"]
        writer.writerow([
            medicine,
            label,
            row["scheduled_utc"],
            row["status"],
            row["outcome_utc"]
        ])
    
    csv_content = output.getvalue().encode('utf-8')
    
    # 3. Upload to Supabase Storage
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_path = f"{user['user_id']}/adherence_report_{timestamp}.csv"
    
    # Check if storage client is available (supabase_admin has service role for bucket access)
    if not supabase_admin:
        raise HTTPException(status_code=503, detail="Storage service unavailable: SUPABASE_SERVICE_ROLE_KEY not configured")

    try:
        # Note: Bucket 'reports' must exist and have RLS or be private
        storage_res = supabase_admin.storage.from_("reports").upload(
            path=file_path,
            file=csv_content,
            file_options={"content-type": "text/csv"}
        )
        
        # 4. Generate Signed URL (valid for 15 minutes)
        signed_url = supabase_admin.storage.from_("reports").create_signed_url(file_path, 900)
        return {"download_url": signed_url["signedUrl"]}
        
    except Exception as e:
        print(f"Storage Error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to upload report: {str(e)}")

@router.get("/dashboard")
async def get_dashboard_data(user = Depends(get_current_user)):
    now = datetime.now(timezone.utc)
    
    # 1. Fetch adherence records for different periods
    week_ago = (now - timedelta(days=7)).isoformat()
    month_ago = (now - timedelta(days=30)).isoformat()
    
    all_adh = supabase.table("adherence").select("status, scheduled_utc").eq("user_id", user["user_id"]).execute()
    
    # Filter periods
    week_data = [x for x in all_adh.data if x['scheduled_utc'] >= week_ago]
    month_data = [x for x in all_adh.data if x['scheduled_utc'] >= month_ago]
    
    # 2. Fetch 3 most recent feedback entries (ADH-FR-39)
    feedback = supabase.table("feedback").select("*").eq("user_id", user["user_id"]).order("created_at", desc=True).limit(3).execute()
    
    # 3. Calculate rates
    week_rate = calculate_rate(week_data)
    month_rate = calculate_rate(month_data)
    
    return {
        "weekly_adherence": week_rate,
        "monthly_adherence": month_rate,
        "weekly_warning": week_rate < 70.0, # ADH-FR-38
        "recent_feedback": feedback.data,
        "total_doses_month": len(month_data)
    }

@router.get("/trend")
async def get_adherence_trend(user = Depends(get_current_user)):
    # Fetch last 14 days of data for trend
    fortnight_ago = (datetime.now(timezone.utc) - timedelta(days=14)).isoformat()
    
    response = supabase.table("adherence")\
        .select("status, scheduled_utc")\
        .eq("user_id", user["user_id"])\
        .gte("scheduled_utc", fortnight_ago)\
        .order("scheduled_utc", desc=False)\
        .execute()
    
    trend = {}
    for entry in response.data:
        date = entry["scheduled_utc"][:10]
        if date not in trend:
            trend[date] = {"taken": 0, "total": 0}
        trend[date]["total"] += 1
        if entry["status"] == "taken":
            trend[date]["taken"] += 1
            
    result = []
    # Fill in dates for the last 14 days
    for i in range(13, -1, -1):
        d = (datetime.now(timezone.utc) - timedelta(days=i)).date().isoformat()
        stats = trend.get(d, {"taken": 0, "total": 0})
        result.append({
            "date": d,
            "rate": round((stats["taken"] / stats["total"] * 100), 1) if stats["total"] > 0 else 0
        })
        
    return result
