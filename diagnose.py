import requests
import os
import asyncio
from dotenv import load_dotenv
from supabase import create_client
from playwright.async_api import async_playwright

load_dotenv()

print("STEP 3 \u2014 Check backend is running:")
try:
    r = requests.get('http://localhost:8000/v1/health')
    print(f"{r.status_code} {r.json()}")
except Exception as e:
    print(f"Connection refused: {e}")

print("\nSTEP 4 \u2014 Check frontend is running:")
try:
    r = requests.get('http://localhost:8080/index.html')
    print(f"{r.status_code}")
except Exception as e:
    print(f"Connection refused: {e}")

print("\nSTEP 5 \u2014 Test all three logins directly against backend:")
base = "http://localhost:8000/v1"
accounts = [
    ("patient1@demo.adhera.app", "Demo@1234"),
    ("provider1@demo.adhera.app", "Demo@1234"),
    ("admin@demo.adhera.app", "Admin@1234"),
]
for email, pw in accounts:
    try:
        r = requests.post(f"{base}/auth/login", json={"email": email, "password": pw})
        print(f"{email}: {r.status_code} {r.text[:200]}")
    except Exception as e:
        print(f"{email}: Connection refused: {e}")

print("\nSTEP 6 \u2014 Check profiles table for demo accounts:")
try:
    sb = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SERVICE_ROLE_KEY"])
    rows = sb.table("profiles").select("email, full_name, role, is_active, is_approved").execute()
    for r in rows.data:
        print(r)
except Exception as e:
    print(f"Failed to query profiles: {e}")

print("\nSTEP 7 \u2014 Show browser console errors:")
async def capture_browser_errors():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        errors = []
        page.on('console', lambda m: errors.append(f'{m.type}: {m.text}'))
        
        await page.goto('http://localhost:8080/index.html')
        await page.fill("input[type='email']", 'patient1@demo.adhera.app')
        await page.fill("input[type='password']", 'Demo@1234')
        await page.click("button:has-text('Login')")
        
        await asyncio.sleep(3)
        await page.screenshot(path='console_error_screenshot.png')
        
        for e in errors:
            print(f'  {e}')
            
        await browser.close()

asyncio.run(capture_browser_errors())
print("DONE")
