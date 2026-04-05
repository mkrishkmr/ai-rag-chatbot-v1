import asyncio
from phase1_ingestion.scraper import run_scraper, GROWW_URLS
import phase1_ingestion.scraper as scraper
import json

async def main():
    scraper.GROWW_URLS = ["https://groww.in/mutual-funds/groww-value-fund-direct-growth"]
    data = await run_scraper()
    for fm in data[0]["fund_managers"]:
        print("MGR:", fm["name"])

asyncio.run(main())
