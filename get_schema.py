import os, dotenv, requests
dotenv.load_dotenv()
url = os.environ['SUPABASE_URL']
key = os.environ['SUPABASE_SERVICE_ROLE_KEY']
r = requests.get(f"{url}/rest/v1/", headers={'apikey': key})
schemas = r.json().get('definitions', r.json().get('components', {}).get('schemas', {}))
print("Audit log properties:", schemas.get('audit_log', {}).get('properties', {}).keys())
