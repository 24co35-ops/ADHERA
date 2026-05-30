import os
from dotenv import load_dotenv
from supabase import create_client
load_dotenv()
sb = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SERVICE_ROLE_KEY"])
try:
    res = sb.auth.sign_in_with_password({"email": "patient1@demo.adhera.app", "password": "Demo@1234"})
    print("Login success:", res.session.access_token[:10])
except Exception as e:
    print("Login failed:", e)
