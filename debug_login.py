import asyncio
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        ctx = await browser.new_context()
        page = await ctx.new_page()
        errors = []
        page.on('console', lambda m: errors.append(f'{m.type}: {m.text}'))
        await page.goto('http://localhost:8080/index.html')
        await page.fill("input[type='email']", 'provider1@demo.adhera.app')
        await page.fill("input[type='password']", 'Demo@1234')
        await page.click("button:has-text('Login')")
        await asyncio.sleep(5)
        print(f'URL: {page.url}')
        for e in errors:
            print(f'  {e}')
        jwt = await page.evaluate('sessionStorage.getItem("jwt")')
        print(f'JWT stored: {"yes" if jwt else "no"}')
        await browser.close()

asyncio.run(run())
