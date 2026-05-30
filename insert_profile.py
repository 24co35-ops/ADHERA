import os, dotenv
from supabase import create_client

dotenv.load_dotenv()
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
supabase = create_client(url, key)

users = supabase.auth.admin.list_users()
user_id = next((u.id for u in users if u.email == "backendtest@adhera.app"), None)
if user_id:
    supabase.table("profiles").upsert({
        "id": user_id,
        "full_name": "Backend Test",
        "role": "patient",
        "date_of_birth": "1990-01-01",
        "contact_number": "9999999999",
        "timezone": "Asia/Kolkata"
    }).execute()
    print(f"Inserted profile for {user_id}")
