import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()
url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
supabase: Client = create_client(url, key)

try:
    # Let's inspect operational_state columns and try to find if there is an existing cron job
    res = supabase.table("operational_state").select("*").limit(1).execute()
    print("operational_state columns:", res.data[0].keys() if res.data else "No data / empty")
except Exception as e:
    print("Error:", e)
