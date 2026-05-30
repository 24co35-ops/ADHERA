import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()
url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
supabase: Client = create_client(url, key)

tables = [
    "profiles", "assignments", "medicines", "reminders", 
    "adherence", "feedback", "emergency_contacts", "reports", 
    "audit_log", "disclaimer_acceptances", "operational_state", 
    "notification_retries", "system_events"
]

missing = []
present = []

for table in tables:
    try:
        supabase.table(table).select("*").limit(1).execute()
        present.append(table)
    except Exception as e:
        missing.append((table, str(e)))

print("PRESENT TABLES:", present)
if missing:
    print("MISSING TABLES:", missing)
else:
    print("ALL TABLES PRESENT")
