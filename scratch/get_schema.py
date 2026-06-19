import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()
url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
supabase: Client = create_client(url, key)

try:
    # Query view definition or check if operational_state is a view/table
    res = supabase.rpc("get_view_definition", {"view_name": "operational_state"}).execute()
    print("RPC Result:", res.data)
except Exception as e:
    print("RPC get_view_definition failed:", e)

try:
    # Let's inspect using raw SQL if we can, but Supabase doesn't allow arbitrary SQL via Client unless there is an RPC.
    # Let's see if we can read the view definition from postgres catalog by calling a custom function if one exists, 
    # or just fetching data from pg_views if possible? But table() only works on tables/views, not system catalogs unless exposed.
    # Let's try to query pg_catalog pg_views via table if RLS/permissions permit (usually service role can do a lot)
    res = supabase.table("operational_state").select("*").limit(1).execute()
    print("Data:", res.data)
except Exception as e:
    print("Query operational_state failed:", e)
