import asyncio
from playwright.async_api import async_playwright

async def login_page(browser, email, pw):
    ctx = await browser.new_context()
    page = await ctx.new_page()
    await page.goto('http://localhost:8080/index.html')
    await page.evaluate(f'''async () => {{
        const res = await fetch('http://localhost:8000/v1/auth/login', {{
            method: 'POST', headers: {{'Content-Type': 'application/json'}},
            body: JSON.stringify({{email: '{email}', password: '{pw}'}})
        }});
        const data = await res.json();
        if(data.data) sessionStorage.setItem('jwt', data.data.access_token);
    }}''')
    return page

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)

        pg = await login_page(browser, 'patient1@demo.adhera.app', 'Demo@1234')
        await pg.goto('http://localhost:8080/medicines.html')
        await pg.wait_for_load_state('networkidle')
        await asyncio.sleep(2)
        cards = await pg.locator('.cursor-pointer').all()
        if cards:
            await cards[0].click()
            await asyncio.sleep(1)
        await pg.screenshot(path='verify_medicines.png', full_page=True)
        print('OK medicines.html')

        pg2 = await login_page(browser, 'provider1@demo.adhera.app', 'Demo@1234')
        await pg2.goto('http://localhost:8080/provider-patient.html?id=06c48c79-10cd-42d0-8edc-67325c48e6e2')
        await pg2.wait_for_load_state('networkidle')
        await asyncio.sleep(2)
        await pg2.screenshot(path='verify_provider_patient.png', full_page=True)
        print('OK provider-patient overview')

        tabs = await pg2.locator('button:has-text("Feedback")').all()
        if tabs:
            await tabs[0].click()
            await asyncio.sleep(1)
        await pg2.screenshot(path='verify_provider_feedback.png', full_page=True)
        print('OK provider feedback')

        pg3 = await login_page(browser, 'admin@demo.adhera.app', 'Demo@1234')
        await pg3.goto('http://localhost:8080/admin-dashboard.html')
        await pg3.wait_for_load_state('networkidle')
        await asyncio.sleep(2)
        await pg3.screenshot(path='verify_admin_stats.png', full_page=True)
        print('OK admin stats')

        await pg3.fill('input[placeholder*="Search"]', 'Demo')
        await asyncio.sleep(1)
        results = await pg3.locator('.cursor-pointer:has-text("Demo Patient")').all()
        if results:
            await results[0].click()
            await asyncio.sleep(2)
        await pg3.screenshot(path='verify_admin_detail.png', full_page=True)
        print('OK admin user detail')

        await browser.close()
        print('ALL PASS')

asyncio.run(run())
