import asyncio
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        
        # 1. Open Dashboard as Patient
        context_p = await browser.new_context()
        page_p = await context_p.new_page()
        # Mock sessionStorage
        await page_p.goto('http://localhost:8080/index.html')
        await page_p.evaluate('''
            async () => {
                const res = await fetch('http://localhost:8000/v1/auth/login', {
                    method: 'POST', headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({email: 'patient1@demo.adhera.app', password: 'Demo@1234'})
                });
                const data = await res.json();
                sessionStorage.setItem('jwt', data.data.access_token);
            }
        ''')
        await page_p.goto('http://localhost:8080/dashboard.html')
        await page_p.wait_for_load_state('networkidle')
        await asyncio.sleep(2)
        
        # 2. Open Provider Dashboard
        context_pr = await browser.new_context()
        page_pr = await context_pr.new_page()
        await page_pr.goto('http://localhost:8080/index.html')
        await page_pr.evaluate('''
            async () => {
                const res = await fetch('http://localhost:8000/v1/auth/login', {
                    method: 'POST', headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({email: 'provider1@demo.adhera.app', password: 'Demo@1234'})
                });
                const data = await res.json();
                sessionStorage.setItem('jwt', data.data.access_token);
            }
        ''')
        await page_pr.goto('http://localhost:8080/provider-dashboard.html')
        await page_pr.wait_for_load_state('networkidle')
        await asyncio.sleep(2)
        
        # Expand patient
        rows = await page_pr.locator('.cursor-pointer').all()
        if rows:
            await rows[0].click()
            await asyncio.sleep(1)
        
        await page_pr.screenshot(path='provider_expanded.png')
        print("Captured provider_expanded.png")

        # 3. Open Admin Dashboard
        context_a = await browser.new_context()
        page_a = await context_a.new_page()
        await page_a.goto('http://localhost:8080/index.html')
        await page_a.evaluate('''
            async () => {
                const res = await fetch('http://localhost:8000/v1/auth/login', {
                    method: 'POST', headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({email: 'admin@demo.adhera.app', password: 'Demo@1234'})
                });
                const data = await res.json();
                sessionStorage.setItem('jwt', data.data.access_token);
            }
        ''')
        await page_a.goto('http://localhost:8080/admin-dashboard.html')
        await page_a.wait_for_load_state('networkidle')
        await asyncio.sleep(2)
        
        # Search for Priya
        await page_a.fill('input[type="text"]', 'priya')
        await asyncio.sleep(1)
        
        await page_a.screenshot(path='admin_search.png')
        print("Captured admin_search.png")
        
        await browser.close()

asyncio.run(run())
