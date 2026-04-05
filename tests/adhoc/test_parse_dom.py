import asyncio
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
import re
import json

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto("https://groww.in/mutual-funds/groww-value-fund-direct-growth", wait_until="networkidle", timeout=60000)
        await page.wait_for_timeout(3000)
        html = await page.content()
        await browser.close()
        
    soup = BeautifulSoup(html, "html.parser")
    fm_header = soup.find(string=re.compile(r"Fund Management", re.IGNORECASE))
    if fm_header:
        fm_section = fm_header.find_parent('div').find_parent('section') or fm_header.find_parent('div').find_parent('div')
        # print out the DOM of fm_section
        print(fm_section.prettify()[:2000])

asyncio.run(main())
