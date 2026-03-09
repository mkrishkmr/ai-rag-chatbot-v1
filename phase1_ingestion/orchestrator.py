import asyncio
import json
import os
from datetime import datetime
from phase1_ingestion.scraper import scrape_groww_fund, GROWW_URLS
from phase1_ingestion.pdf_parser import PDF_SOURCES, extract_pdf_rules

async def compile_fact_sheets():
    print("🚀 Starting Verified Data Engine Orchestration...")
    
    # Run scrapers
    web_tasks = [scrape_groww_fund(url) for url in GROWW_URLS]
    web_results = await asyncio.gather(*web_tasks)
    
    # Combine data
    combined_knowledge = []
    
    for web_data in web_results:
        fund_slug = web_data.get('source_url', '').split('/')[-1]
        
        # Merge web data
        fact_sheet = {
            "metadata": {
                "source_url": web_data.get("source_url"),
                "last_updated": datetime.now().isoformat(),
                "document_type": "Hybrid Fact Sheet"
            },
            "metrics": web_data,
            "rules": {"notice": "PDF parsing mocked for non-existent dummy endpoints."}
        }
        combined_knowledge.append(fact_sheet)

    out_file = "scheme_fact_sheet.json"
    with open(out_file, "w") as f:
        json.dump(combined_knowledge, f, indent=2)
    
    print(f"✅ Created unified scheme facts at {os.path.abspath(out_file)}")

if __name__ == "__main__":
    asyncio.run(compile_fact_sheets())
