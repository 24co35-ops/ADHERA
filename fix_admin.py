import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()
sb = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SERVICE_ROLE_KEY"])

print("Fixing admin account...")

# 1. Check if admin exists in auth
users_resp = sb.auth.admin.list_users()
admin_user = None
for u in users_resp:
    if u.email == "admin@demo.adhera.app":
        admin_user = u
        break

admin_user_id = None
if not admin_user:
    print("Creating admin in auth...")
    res = sb.auth.admin.create_user({
        "email": "admin@demo.adhera.app",
        "password": "Admin@1234",
        "email_confirm": True
    })
    admin_user_id = res.user.id
else:
    print("Admin exists in auth. Resetting password...")
    admin_user_id = admin_user.id
    sb.auth.admin.update_user_by_id(admin_user_id, {"password": "Admin@1234"})

# 2. Check profile row
profiles_resp = sb.table("profiles").select("*").eq("id", admin_user_id).execute()
if not profiles_resp.data:
    print("Creating admin profile row...")
    sb.table("profiles").insert({
        "id": admin_user_id,
        "full_name": "Demo Admin",
        "role": "admin",
        "is_active": True,
        "timezone": "Asia/Kolkata"
    }).execute()
else:
    print("Admin profile row exists.")
    sb.table("profiles").update({"is_active": True, "role": "admin"}).eq("id", admin_user_id).execute()

# Verify
import requests
r = requests.post("http://localhost:8000/v1/auth/login", json={"email": "admin@demo.adhera.app", "password": "Admin@1234"})
print(f"Login Verify: {r.status_code} {r.json()}")
