import requests, json

base = 'http://localhost:8000/v1'

def login(email, pw):
    r = requests.post(f'{base}/auth/login', json={'email': email, 'password': pw})
    return r.json().get('data', {}).get('access_token')

def get(token, path):
    r = requests.get(f'{base}{path}', headers={'Authorization': f'Bearer {token}'})
    return r.status_code, r.json()

# Patient
pt = login('patient1@demo.adhera.app', 'Demo@1234')
ph = {'Authorization': f'Bearer {pt}'}

print("=== PATIENT ===")
for path in ['/medicines/', '/feedback/', '/analytics/dashboard', '/analytics/trend', '/analytics/adherence']:
    sc, data = get(pt, path)
    print(f"{path}: {sc}")
    if path == '/medicines/' and sc == 200 and data.get('data'):
        mid = data['data'][0]['id']
        sc2, data2 = get(pt, f'/medicines/{mid}/reminders')
        print(f"  /medicines/{mid}/reminders: {sc2} -> {json.dumps(data2)[:200]}")

# Provider
pv = login('provider1@demo.adhera.app', 'Demo@1234')
print("\n=== PROVIDER ===")
sc, pdata = get(pv, '/provider/patients')
print(f"/provider/patients: {sc}")
pid = None
if sc == 200 and pdata.get('data'):
    pid = pdata['data'][0]['patient_id']
    for path in [f'/provider/patients/{pid}',
                 f'/feedback/?patient_id={pid}',
                 f'/analytics/dashboard?patient_id={pid}',
                 f'/analytics/trend?patient_id={pid}',
                 f'/analytics/adherence?patient_id={pid}']:
        sc2, d2 = get(pv, path)
        print(f"{path}: {sc2}")

# Admin
at = login('admin@demo.adhera.app', 'Demo@1234')
print("\n=== ADMIN ===")
if pid:
    for path in [f'/feedback/?patient_id={pid}',
                 f'/analytics/dashboard?patient_id={pid}',
                 f'/analytics/trend?patient_id={pid}']:
        sc2, d2 = get(at, path)
        print(f"{path}: {sc2}")
