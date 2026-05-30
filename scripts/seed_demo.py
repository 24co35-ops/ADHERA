import os
import sys
import random
from datetime import datetime, timedelta, timezone

# Add parent directory to path to import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY")
    sys.exit(1)

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

USERS = [
    {"email": "patient1@demo.adhera.app", "password": "Password123!", "role": "patient", "name": "Priya (Demo Patient)"},
    {"email": "provider1@demo.adhera.app", "password": "Password123!", "role": "provider", "name": "Dr. Rahul (Demo Provider)"},
    {"email": "admin@demo.adhera.app", "password": "Password123!", "role": "admin", "name": "Neha (Demo Admin)"}
]

def seed():
    print("Starting demo seed...")
    user_ids = {}

    for u in USERS:
        try:
            res = supabase.auth.admin.create_user({
                "email": u["email"],
                "password": u["password"],
                "email_confirm": True,
                "user_metadata": {
                    "full_name": u["name"],
                    "role": u["role"],
                    "timezone": "UTC"
                }
            })
            uid = res.user.id
            user_ids[u["role"]] = uid
            print(f"Created {u['role']}: {u['email']}")
        except Exception as e:
            if "already exists" in str(e).lower() or "already registered" in str(e).lower():
                print(f"User {u['email']} exists, fetching ID...")
                # Unfortunately supabase.auth.admin.list_users() is the way to get them
                users = supabase.auth.admin.list_users()
                for existing_u in users:
                    if existing_u.email == u["email"]:
                        user_ids[u["role"]] = existing_u.id
                        break
            else:
                print(f"Error creating {u['email']}: {e}")
                
    patient_id = user_ids.get("patient")
    provider_id = user_ids.get("provider")

    if not patient_id or not provider_id:
        print("Missing patient or provider ID. Aborting.")
        return

    # Create assignment
    try:
        supabase.table("assignments").upsert({
            "patient_id": patient_id,
            "provider_id": provider_id,
            "status": "active"
        }).execute()
        print("Created assignment.")
    except Exception as e:
        print(f"Error assigning patient: {e}")

    # Create 3 medicines
    medicines = [
        {"name": "Metformin", "dosage_amount": 500, "dosage_unit": "mg", "route": "oral", "frequency_type": "daily", "start_date": "2025-01-01", "user_id": patient_id},
        {"name": "Lisinopril", "dosage_amount": 10, "dosage_unit": "mg", "route": "oral", "frequency_type": "daily", "start_date": "2025-01-01", "user_id": patient_id},
        {"name": "Atorvastatin", "dosage_amount": 20, "dosage_unit": "mg", "route": "oral", "frequency_type": "daily", "start_date": "2025-01-01", "user_id": patient_id}
    ]
    
    med_ids = []
    for med in medicines:
        res = supabase.table("medicines").insert(med).execute()
        med_ids.append(res.data[0]["id"])
        print(f"Created medicine: {med['name']}")

    # Create reminders
    reminders = [
        {"medicine_id": med_ids[0], "user_id": patient_id, "dose_label": "morning", "dose_time_utc": "08:00:00", "timezone": "UTC", "recurrence_type": "daily"},
        {"medicine_id": med_ids[1], "user_id": patient_id, "dose_label": "morning", "dose_time_utc": "08:00:00", "timezone": "UTC", "recurrence_type": "daily"},
        {"medicine_id": med_ids[2], "user_id": patient_id, "dose_label": "evening", "dose_time_utc": "20:00:00", "timezone": "UTC", "recurrence_type": "daily"}
    ]
    
    rem_ids = []
    for rem in reminders:
        try:
            res = supabase.table("reminders").insert(rem).execute()
            rem_ids.append(res.data[0]["id"])
            print(f"Created reminder for {rem['dose_label']}")
        except Exception as e:
            print(f"Error creating reminder: {e}")
            # Try fetching existing
            pass
            
    # Adherence history (30 days, ~72% taken)
    if not rem_ids:
        print("No reminders to track adherence.")
        return
        
    # Get rem_ids again just in case
    existing_rems = supabase.table("reminders").select("id").eq("user_id", patient_id).execute()
    rem_ids = [r["id"] for r in existing_rems.data]

    print("Generating adherence history...")
    now = datetime.now(timezone.utc)
    adherence_data = []
    
    for i in range(30):
        d = now - timedelta(days=i)
        for rid in rem_ids:
            status = "taken" if random.random() <= 0.72 else "missed"
            adherence_data.append({
                "reminder_id": rid,
                "user_id": patient_id,
                "scheduled_utc": d.isoformat(),
                "status": status,
                "outcome_utc": d.isoformat()
            })
    
    # Bulk insert adherence in chunks
    for i in range(0, len(adherence_data), 100):
        chunk = adherence_data[i:i+100]
        try:
            supabase.table("adherence").insert(chunk).execute()
        except Exception as e:
            pass # Ignore unique constraint violations if running multiple times
            
    print("Seed complete.")

if __name__ == "__main__":
    seed()
