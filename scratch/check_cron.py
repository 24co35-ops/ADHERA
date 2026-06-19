import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()
url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
supabase: Client = create_client(url, key)

try:
    # Query cron.job using raw sql if possible viarpc or postgres, 
    # but wait, supabase client does not support raw sql directly unless we do an RPC.
    # Let's see if there is an RPC we can use, or let's look at public.operational_state
    # to see how it is populated. Let's see if there are any database triggers.
    res = supabase.table("reminders").select("*").limit(1).execute()
    print("Reminders table columns:", res.data[0].keys() if res.data else "No data")
except Exception as e:
    print("Error:", e)
