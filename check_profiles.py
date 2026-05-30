import requests, json
base = 'http://localhost:8000/v1'
def login(e,p):
    r = requests.post(f'{base}/auth/login', json={'email':e,'password':p})
    return r.json().get('data',{}).get('access_token')
at = login('admin@demo.adhera.app','Demo@1234')
r = requests.get(f'{base}/admin/users', headers={'Authorization':f'Bearer {at}'})
users = r.json().get('data',[])
if users:
    print("COLUMNS:", list(users[0].keys()))
    for u in users:
        print(f"  {u.get('full_name','?'):30s} role={u.get('role','?'):10s} is_active={u.get('is_active','?')} is_approved={u.get('is_approved','?')} status={u.get('status','?')} email={u.get('email','?')}")
