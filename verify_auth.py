import requests, json, time
base = 'http://localhost:8000/v1'

def login(e, p):
    r = requests.post(f'{base}/auth/login', json={'email': e, 'password': p})
    d = r.json()
    if r.status_code == 200 and d.get('data'):
        return d['data']['access_token'], 200
    return d, r.status_code

# Admin login
at, _ = login('admin@demo.adhera.app', 'Demo@1234')

# Fix Ashwith
r = requests.get(f'{base}/admin/users', headers={'Authorization': f'Bearer {at}'})
users = r.json()['data']
for u in users:
    if 'ashwith' in (u.get('full_name','') or '').lower():
        print(f"BEFORE: {u['full_name']} is_active={u['is_active']}")
        r2 = requests.post(f'{base}/admin/users/{u["id"]}/approve', headers={'Authorization': f'Bearer {at}'})
        print(f"AFTER: is_active={r2.json()['data']['is_active']}")

# Verify patient login works
print("\n--- Patient login ---")
tok, code = login('patient1@demo.adhera.app', 'Demo@1234')
print(f"Status: {code}, {'TOKEN' if code==200 else tok}")

# Verify pending provider filter
print("\n--- Pending providers ---")
r = requests.get(f'{base}/admin/users?role=provider&status=pending', headers={'Authorization': f'Bearer {at}'})
print(f"Count: {len(r.json()['data'])}")

# Verify admin register blocked
print("\n--- Admin self-register ---")
r = requests.post(f'{base}/auth/register', json={'email':'test_admin@test.com','password':'Test@1234','full_name':'Test Admin','role':'admin','timezone':'UTC'})
print(f"Status: {r.status_code} (expect 403)")

print("\nDONE")
