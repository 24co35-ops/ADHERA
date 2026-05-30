import os, sys
print(sys.executable)

from dotenv import load_dotenv
load_dotenv()
secret = os.environ.get("SUPABASE_JWT_SECRET")

import requests
r = requests.post("http://localhost:8000/v1/auth/login", json={
    "email": "backendtest@adhera.app",
    "password": "Test@1234"
})
token = r.json().get("data", {}).get("access_token")
print("TOKEN:", token[:20] if token else "MISSING")

try:
    from jose import jwt
    payload = jwt.decode(token, secret, algorithms=["HS256"], audience="authenticated")
    print("JOSE PAYLOAD:", payload)
except Exception as e:
    print("JOSE DECODE ERROR:", repr(e))

try:
    import jwt as pyjwt
    payload2 = pyjwt.decode(token, secret, algorithms=["HS256"], audience="authenticated")
    print("PYJWT PAYLOAD:", payload2)
except Exception as e:
    print("PYJWT DECODE ERROR:", repr(e))
