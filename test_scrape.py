import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto("https://groww.in/mutual-funds/groww-nifty-50-index-fund-direct-growth", wait_until="networkidle")
        html = await page.content()
        with open("dump.html", "w") as f:
            f.write(html)
        await browser.close()

asyncio.run(main())
