import asyncio
import re
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

GROWW_URLS = [
    "https://groww.in/mutual-funds/groww-nifty-50-index-fund-direct-growth",
    "https://groww.in/mutual-funds/groww-value-fund-direct-growth",
    "https://groww.in/mutual-funds/groww-aggressive-hybrid-fund-direct-growth",
    "https://groww.in/mutual-funds/groww-elss-tax-saver-fund-direct-growth"
]

def clean_text(element):
    """Helper to cleanly extract text from a BeautifulSoup element."""
    if not element:
        return None
    text = element.get_text(separator=' ', strip=True)
    # Remove excessive spaces
    text = re.sub(r'\s+', ' ', text)
    return text

async def scrape_groww_fund(url: str) -> dict:
    """Scrapes specific factual data points from a Groww mutual fund page."""
    print(f"🔍 Scraping Advanced Facts: {url}")
    data = {
        "source_url": url,
        "fund_name": url.split("/")[-1].replace("-", " ").title(),
        "document_type": "Web API / Summary",
        "scraped_fields": {}
    }
    
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
            )
            page = await context.new_page()
            
            # Navigate and explicitly wait for the NAV or core components to render
            await page.goto(url, wait_until="networkidle", timeout=60000)
            await page.wait_for_timeout(3000) 
            
            html = await page.content()
            await browser.close()
            
            soup = BeautifulSoup(html, "html.parser")
            
            # --- 1. Header Facts ---
            # Attempt to find the main H1 or title area
            h1 = soup.find('h1')
            if h1:
                data["scraped_fields"]["Scheme Name"] = clean_text(h1)
            
            # We search for textual markers because strict CSS classes rotate often
            all_text_blocks = soup.find_all(string=True)
            full_text = " ".join([t.strip() for t in all_text_blocks if t.strip()])
            data["raw_text_length"] = len(full_text)

            def extract_from_table_or_div(keyword_regex):
                """Finds the keyword and attempts to find the associated value in a nearby element."""
                matches = soup.find_all(string=re.compile(keyword_regex, re.IGNORECASE))
                results = []
                for elem in matches:
                    if elem.parent.name in ['script', 'style']: continue
                    
                    parent = elem.find_parent()
                    if not parent: continue
                    
                    text = None
                    # 1. Check next sibling of the parent
                    next_sibling = parent.find_next_sibling()
                    if next_sibling:
                        text = clean_text(next_sibling)
                        
                    # 2. Check a broader parent if nested layout
                    if not text:
                        grandparent = parent.find_parent()
                        if grandparent:
                            next_gp_sibling = grandparent.find_next_sibling()
                            if next_gp_sibling:
                                text = clean_text(next_gp_sibling)
                                
                    if text:
                        lower_text = text.lower()
                        # Exclude dictionary definitions from hover popups
                        if "fee payable" in lower_text or "percentage of" in lower_text or "form of tax" in lower_text:
                            continue
                        if text not in results:
                            results.append(text)
                
                if not results:
                    return "Not Found"
                    
                # Prefer actual readable values over "--" placeholders
                valid_results = [r for r in results if r != "--" and len(r) > 1]
                if valid_results:
                    return valid_results[-1]
                return results[-1]

            # --- 2. Details & Stats ---
            data["scraped_fields"]["NAV"] = extract_from_table_or_div(r"^NAV:")
            data["scraped_fields"]["Expense Ratio"] = extract_from_table_or_div(r"^Expense ratio")
            data["scraped_fields"]["Exit Load"] = extract_from_table_or_div(r"^Exit load")
            data["scraped_fields"]["Fund Size"] = extract_from_table_or_div(r"^Fund size")
            data["scraped_fields"]["Benchmark"] = extract_from_table_or_div(r"^Fund benchmark")
            
            # --- 3. Investment Thresholds ---
            data["scraped_fields"]["Min. SIP Investment"] = extract_from_table_or_div(r"^Min\. for SIP")
            data["scraped_fields"]["Min. Lumpsum"] = extract_from_table_or_div(r"^Min\. for 1st investment")
            
            # By parsing the huge text blob with LangChain later, 
            # we also pass the full text as fallback so the LLM can find anything else
            data["full_scraped_text_fallback"] = full_text[:5000] # Limit to avoid bloat
            
            return data
            
    except Exception as e:
        print(f"❌ Failed to scrape {url}: {e}")
        return {"source_url": url, "error": str(e)}

async def main():
    results = []
    for url in GROWW_URLS:
        res = await scrape_groww_fund(url)
        results.append(res)
    
    import json
    with open("groww_advanced_scraped.json", "w") as f:
        json.dump(results, f, indent=2)
    print("✅ Completed Advanced Web Scraping.")

if __name__ == "__main__":
    asyncio.run(main())
