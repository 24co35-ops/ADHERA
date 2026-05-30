import asyncio
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()

        console_errors = []
        network_errors = []

        page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)
        page.on("requestfailed", lambda req: network_errors.append(f"{req.url} {req.failure}"))
        page.on("response", lambda res: network_errors.append(f"{res.url} {res.status}") if res.status >= 400 else None)

        def reset():
            console_errors.clear()
            network_errors.clear()

        # index.html
        reset()
        await page.goto("http://localhost:8080/index.html")
        await page.wait_for_load_state("networkidle")
        await page.screenshot(path="index.png")
        print("index.html")
        print("Console errors:", console_errors)
        print("Network errors:", network_errors)

        # register.html
        reset()
        await page.goto("http://localhost:8080/register.html")
        await page.wait_for_load_state("networkidle")
        await page.screenshot(path="register.png")
        print("register.html")
        print("Console errors:", console_errors)
        print("Network errors:", network_errors)

        # dashboard.html
        reset()
        await page.goto("http://localhost:8080/dashboard.html")
        await page.wait_for_load_state("networkidle")
        await page.screenshot(path="dashboard.png")
        print("dashboard.html")
        print("URL:", page.url)
        print("Console errors:", console_errors)
        print("Network errors:", network_errors)

        await browser.close()

asyncio.run(run())
