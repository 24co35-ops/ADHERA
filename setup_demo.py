import os, dotenv
from supabase import create_client

dotenv.load_dotenv()
supabase = create_client(os.environ['SUPABASE_URL'], os.environ['SUPABASE_SERVICE_ROLE_KEY'])

users_to_create = [
    ("patient1@demo.adhera.app", "patient", "Demo Patient 1"),
    ("provider1@demo.adhera.app", "provider", "Demo Provider 1"),
    ("admin@demo.adhera.app", "admin", "Demo Admin")
]

for email, role, name in users_to_create:
    try:
        # Check if exists
        users = supabase.auth.admin.list_users()
        u = next((u for u in users if u.email == email), None)
        if not u:
            print(f"Creating {email}...")
            res = supabase.auth.admin.create_user({
                "email": email,
                "password": "Demo@1234",
                "email_confirm": True,
                "user_metadata": {"role": role}
            })
            uid = res.user.id
            print(f"Inserting profile for {uid}...")
            supabase.table("profiles").insert({
                "id": uid,
                "full_name": name,
                "role": role,
            }).execute()
        else:
            print(f"{email} already exists. Setting confirm and metadata...")
            supabase.auth.admin.update_user_by_id(u.id, {"email_confirm": True, "user_metadata": {"role": role}})
            # upsert profile
            supabase.table("profiles").upsert({
                "id": u.id,
                "full_name": name,
                "role": role,
            }).execute()
    except Exception as e:
        print(f"Error for {email}: {e}")

print("Demo users setup complete.")
