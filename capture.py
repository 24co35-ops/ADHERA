import asyncio
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        
        pages = ['index.html', 'register.html', 'dashboard.html', 'medicines.html', 'feedback.html', 'provider-dashboard.html', 'admin-dashboard.html']
        
        for p_name in pages:
            try:
                await page.goto(f'http://localhost:8080/{p_name}')
                await page.wait_for_load_state('networkidle')
                await asyncio.sleep(1)
                await page.screenshot(path=f'{p_name.replace(".html", "")}.png')
                print(f'Captured {p_name}')
            except Exception as e:
                print(f'Failed {p_name}: {e}')
        
        await browser.close()

asyncio.run(run())
