import requests

base = "http://localhost:8000/v1"

# Login
r = requests.post(f"{base}/auth/login", json={
    "email": "backendtest@adhera.app",
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
