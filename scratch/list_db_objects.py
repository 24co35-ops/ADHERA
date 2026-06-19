import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()
url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
supabase: Client = create_client(url, key)

try:
    # Query database objects using public tables or RPC
    # Since we can't run raw SQL, let's see if we can do an RPC call or read from postgrest /
    # Wait, postgrest exposes all tables/views in the schema cache.
    # Let's inspect the OpenAPI schema of postgrest!
    import requests
    res = requests.get(url)
    print("PostgREST status:", res.status_code)
    # Let's fetch postgrest root /
    headers = {"apikey": key, "Authorization": f"Bearer {key}"}
    res_root = requests.get(f"{url}/", headers=headers)
    print("PostgREST root keys:", list(res_root.json().get("paths", {}).keys()) if res_root.status_code == 200 else "Error")
except Exception as e:
    print("Error:", e)
