import os, dotenv
from supabase import create_client

dotenv.load_dotenv()
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
supabase = create_client(url, key)

users = supabase.auth.admin.list_users()
for u in users:
    if u.email == "backendtest@adhera.app" and not getattr(u, 'email_confirmed_at', None):
        supabase.auth.admin.update_user_by_id(u.id, {"email_confirm": True})
        print(f"Confirmed {u.email}")
