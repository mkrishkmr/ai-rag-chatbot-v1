import asyncio
import json
import os
import subprocess
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

from phase1_ingestion.scraper import scrape_all_web_metrics
from phase1_ingestion.pdf_parser import parse_all_pdfs

async def compile_fact_sheets():
    logger.info("🚀 Starting Verified Data Engine Orchestration...")
    
    # 1. Trigger PDF Download Logic using subprocess to ensure it processes clean
    logger.info("📦 Step 1: Downloading & Caching SID and KIM PDFs...")
    subprocess.run(["python", "-m", "phase1_ingestion.download_sid_kim"], check=True)
    
    # 2. Run Playwright scrapers
    logger.info("🌐 Step 2: Scraping comprehensive live Web Metrics...")
    web_results = await scrape_all_web_metrics()
    
    # Map web data by slug
    web_data_map = {res.get('fund_slug', ''): res for res in web_results if res}
    
    # 3. Parse downloaded PDFs
    logger.info("📄 Step 3: Parsing text from all downloaded PDFs...")
    pdf_results = parse_all_pdfs()
    
    # Map pdf data by slug -> list of pdf doc dicts
    pdf_data_map = {}
    for pdf in pdf_results:
        slug = pdf.get("fund_slug")
        if slug not in pdf_data_map:
            pdf_data_map[slug] = []
        pdf_data_map[slug].append(pdf)
    
    # 4. Combine data
    logger.info("🔗 Step 4: Assembling Unified Fact Sheets...")
    unified_knowledge_base = []
    
    # We use web data slugs as the base
    for fund_slug, web_data in web_data_map.items():
        pdf_docs = pdf_data_map.get(fund_slug, [])
        
        # Attach pdf documents to the root of the comprehensive web schema
        web_data["pdf_documents"] = pdf_docs
        unified_knowledge_base.append(web_data)

    out_file = "phase1_ingestion/data/unified_knowledge_base.json"
    with open(out_file, "w") as f:
        json.dump(unified_knowledge_base, f, indent=2)
    
    logger.info(f"✅ Created unified scheme facts at {os.path.abspath(out_file)}")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    asyncio.run(compile_fact_sheets())
