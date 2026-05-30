import requests
import uuid
import os, dotenv
from supabase import create_client

dotenv.load_dotenv()
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
supabase = create_client(url, key)

base = "http://localhost:8000/v1"
test_email = f"backendtest_{uuid.uuid4().hex[:8]}@adhera.app"

print(f"Testing with {test_email}")

# Health
r = requests.get(f"{base}/health")
print("HEALTH:", r.status_code, r.json())

# CORS preflight
r = requests.options(f"{base}/health", headers={
    "Origin": "http://localhost:8080",
    "Access-Control-Request-Method": "GET"
})
print("CORS:", r.status_code, r.headers.get("Access-Control-Allow-Origin"))

# Register
r = requests.post(f"{base}/auth/register", json={
    "email": test_email,
    "password": "Test@1234",
    "full_name": "Backend Test",
    "role": "patient",
    "date_of_birth": "1990-01-01",
    "contact_number": "9999999999",
    "timezone": "Asia/Kolkata",
    "disclaimer_accepted": True
})
try:
    print("REGISTER:", r.status_code, r.json())
except Exception:
    print("REGISTER:", r.status_code, r.text)

# Auto-confirm for login
users = supabase.auth.admin.list_users()
user_id = next((u.id for u in users if u.email == test_email), None)
if user_id:
    supabase.auth.admin.update_user_by_id(user_id, {"email_confirm": True})

# Login
r = requests.post(f"{base}/auth/login", json={
    "email": test_email,
    "password": "Test@1234"
})
print("LOGIN:", r.status_code)
try:
    token = r.json().get("data", {}).get("access_token")
    print("TOKEN:", "OK" if token else "MISSING")
except Exception:
    token = None
    print("TOKEN:", "MISSING (parse error)")

# Authenticated route
if token:
    r = requests.get(f"{base}/profile", headers={"Authorization": f"Bearer {token}"})
    try:
        print("PROFILE:", r.status_code, r.json())
    except Exception:
        print("PROFILE:", r.status_code, r.text)
