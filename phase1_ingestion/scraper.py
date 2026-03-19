import asyncio
import re
import os
import json
import logging
from datetime import datetime, timezone
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

logger = logging.getLogger(__name__)

GROWW_URLS = [
    "https://groww.in/mutual-funds/groww-nifty-50-index-fund-direct-growth",
    "https://groww.in/mutual-funds/groww-value-fund-direct-growth",
    "https://groww.in/mutual-funds/groww-aggressive-hybrid-fund-direct-growth",
    "https://groww.in/mutual-funds/groww-elss-tax-saver-fund-direct-growth"
]

def clean_text(text):
    """Cleanly extract and strip text, handling nulls."""
    if not text:
        return None
    if getattr(text, 'get_text', None):
        text = text.get_text(separator=' ', strip=True)
    text = re.sub(r'\s+', ' ', str(text)).strip()
    return text if text and text != "--" else None

def clean_numeric(text):
    """Strip currency symbols, commas, and percentage signs, returning a numeric string."""
    if not text or text == "--":
        return None
    # Remove everything except digits, decimal points, and minus signs
    cleaned = re.sub(r'[^\d.-]', '', str(text))
    return cleaned if cleaned else None

def extract_from_table_or_div(soup, keyword_regex):
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
            if "fee payable" in lower_text or "percentage of" in lower_text or "form of tax" in lower_text:
                continue
            if text not in results:
                results.append(clean_text(text))
    
    if not results:
        return None
        
    valid_results = [r for r in results if r]
    return valid_results[-1] if valid_results else None

def parse_html_to_schema(html: str, url: str) -> dict:
    """Parses the full Groww DOM into the strict JSON schema."""
    soup = BeautifulSoup(html, "html.parser")
    
    # Explicit mapping to match download_sid_kim.py exactly
    SLUG_MAP = {
        "groww-nifty-50-index-fund-direct-growth": "nifty50_index",
        "groww-value-fund-direct-growth": "value_fund",
        "groww-aggressive-hybrid-fund-direct-growth": "aggressive_hybrid",
        "groww-elss-tax-saver-fund-direct-growth": "elss_tax_saver"
    }
    url_key = url.split("/")[-1]
    fund_slug = SLUG_MAP.get(url_key, url_key.replace("-", "_"))
    
    # Pre-populate schema skeleton
    data = {
        "fund_name": None,
        "fund_slug": fund_slug.replace("-", "_"),
        "source_url": url,
        "scraped_at": datetime.now(timezone.utc).isoformat(),
        "identity": {},
        "live_metrics": {},
        "investment_limits": {},
        "returns": {
            "annualised": {},
            "category_average": {},
            "rank_in_category": {},
            "return_calculator_example": {}
        },
        "costs_and_taxation": {},
        "fund_managers": [],
        "holdings": {"total_count": 0, "stocks": []},
        "fund_house_details": {},
        "document_links": {}
    }
    
    def log_miss(field: str, reason: str):
        logger.warning(f"SCRAPE_MISS: {data['fund_slug']} — field: {field} — reason: {reason}")
    
    try:
        # --- Fund Name ---
        h1 = soup.find('h1')
        data["fund_name"] = clean_text(h1) if h1 else None
        
        # --- 2.1 Identity Block ---
        breadcrumbs = soup.find_all('div', class_=re.compile("breadcrumb", re.I))
        # Groww typically uses class 'tag82Text' or similar for the badges below H1
        badges_container = soup.find('div', class_=re.compile("tag82List|tagList", re.I))
        if badges_container:
            badges = badges_container.find_all('span')
            if len(badges) >= 3:
                data["identity"]["category"] = clean_text(badges[0])
                data["identity"]["sub_category"] = clean_text(badges[1])
                data["identity"]["risk_level"] = clean_text(badges[2])
        if not data["identity"].get("category"):
            # Fallback naive search by looking for elements matching specific keywords
            eq = soup.find(string=re.compile(r"^\s*Equity\s*$|^\s*Hybrid\s*$|^\s*Debt\s*$"))
            if eq: data["identity"]["category"] = clean_text(eq)

        data["identity"]["fund_house"] = extract_from_table_or_div(soup, r"^Fund house") or "Groww Mutual Fund"
        data["identity"]["amc_rank_india"] = extract_from_table_or_div(soup, r"^Rank")
        data["identity"]["launch_date"] = extract_from_table_or_div(soup, r"^Launch date")
        data["identity"]["benchmark"] = extract_from_table_or_div(soup, r"^Fund benchmark")
        data["identity"]["investment_objective"] = extract_from_table_or_div(soup, r"^Investment objective")
        
        # --- 2.2 Live Metrics ---
        # NAV
        nav_match = soup.find(string=re.compile(r"^\s*NAV:\s*$", re.IGNORECASE))
        if nav_match:
            nav_parent = nav_match.find_parent()
            nav_val = nav_parent.find_next_sibling() if nav_parent else None
            if nav_val:
                nav_text = clean_text(nav_val)
                # Nav text often looks like "₹9.24 13 Mar 2026"
                parts = nav_text.split(" ", 1)
                data["live_metrics"]["nav"] = clean_numeric(parts[0])
                if len(parts) > 1:
                    data["live_metrics"]["nav_date"] = parts[1].strip()
        if not data["live_metrics"].get("nav"):
            data["live_metrics"]["nav"] = clean_numeric(extract_from_table_or_div(soup, r"^NAV:"))
            
        data["live_metrics"]["fund_size_cr"] = clean_numeric(extract_from_table_or_div(soup, r"^Fund size"))
        data["live_metrics"]["expense_ratio_pct"] = clean_numeric(extract_from_table_or_div(soup, r"^Expense ratio"))
        
        # --- 2.3 Investment Limits ---
        data["investment_limits"]["min_first_investment"] = clean_numeric(extract_from_table_or_div(soup, r"^Min\. for 1st investment"))
        data["investment_limits"]["min_second_investment"] = clean_numeric(extract_from_table_or_div(soup, r"^Min\. for 2nd investment"))
        data["investment_limits"]["min_sip"] = clean_numeric(extract_from_table_or_div(soup, r"^Min\. for SIP"))
        
        # --- 2.4 Returns Table ---
        returns_table = soup.find('table')
        if returns_table:
            rows = returns_table.find_all('tr')
            for row in rows:
                cols = row.find_all('td')
                if not cols: continue
                row_label = clean_text(cols[0]).lower()
                
                # Assign to corresponding category based on label
                target = None
                if "fund returns" in row_label: target = data["returns"]["annualised"]
                elif "category average" in row_label: target = data["returns"]["category_average"]
                elif "rank" in row_label: target = data["returns"]["rank_in_category"]
                
                if target and len(cols) >= 5:
                    target["1M"] = clean_text(cols[1]) if clean_numeric(cols[1].get_text()) else None
                    target["3M"] = clean_text(cols[2]) if clean_numeric(cols[2].get_text()) else None
                    target["6M"] = clean_text(cols[3]) if clean_numeric(cols[3].get_text()) else None
                    target["all"] = clean_text(cols[4]) if clean_numeric(cols[4].get_text()) else None
        else:
            log_miss("returns", "Table not found")
            
        # --- 2.5 Return Calculator Example ---
        calc_div = soup.find(string=re.compile(r"Return Calculator", re.IGNORECASE))
        if calc_div:
            # We don't interact with it, we just scrape the default visible state
            target = data["returns"]["return_calculator_example"]
            try:
                target["type"] = "Monthly SIP" # Usually default
                target["monthly_investment"] = clean_numeric(extract_from_table_or_div(soup, r"Monthly Investment"))
                
                # Attempt to find period/totals from the output box
                total_inv_str = soup.find(string=re.compile(r"Total Investment", re.IGNORECASE))
                if total_inv_str:
                    vp = total_inv_str.find_parent().find_next_sibling()
                    if vp:
                        target["total_investment"] = clean_numeric(vp.get_text())
                
                wb_str = soup.find(string=re.compile(r"Would(\s+)?have\s+become|Would've become", re.IGNORECASE))
                if wb_str:
                    vp = wb_str.find_parent().find_next_sibling()
                    if vp:
                        # Split number and percent e.g "₹16,400 +2.51%"
                        wt = clean_text(vp)
                        parts = wt.split()
                        if len(parts) >= 1: target["would_become"] = clean_numeric(parts[0])
                        if len(parts) >= 2: target["historic_returns_pct"] = parts[-1]
                
            except Exception as e:
                log_miss("return_calculator_example", str(e))
                
        # --- 2.6 Costs and Taxation ---
        exit_str = extract_from_table_or_div(soup, r"^Exit load")
        if exit_str:
            data["costs_and_taxation"]["exit_load"] = exit_str
        
        # Stamp duty, dates, and taxes
        stamp_duty_ele = extract_from_table_or_div(soup, r"^Stamp duty")
        if stamp_duty_ele: data["costs_and_taxation"]["stamp_duty"] = stamp_duty_ele
        # Attempt finding full text sentences for taxes via preceding sibling or parent container logic
        tax_stcg_ele = soup.find(string=re.compile(r"Tax Implications", re.IGNORECASE))
        if tax_stcg_ele:
            # Usually unstructured list. We grab all text in the parent container
            container = tax_stcg_ele.find_parent('div').find_parent('div')
            if container:
                full_tax_text = clean_text(container).lower()
                data["costs_and_taxation"]["tax_stcg"] = "20% if redeemed within one year" if "20%" in full_tax_text else None
                data["costs_and_taxation"]["tax_ltcg"] = "12.5% on returns exceeding Rs 1.25 lakh in a financial year if redeemed after one year" if "12.5%" in full_tax_text else None

        # --- 2.7 Fund Managers ---
        fm_header = soup.find(string=re.compile(r"Fund Management", re.IGNORECASE))
        if fm_header:
            fm_section = fm_header.find_parent('div').find_parent('section') or fm_header.find_parent('div').find_parent('div')
            if fm_section:
                # Find all distinct manager cards (Groww wraps names in tags like <div class="val...">Name</div>)
                # Looking for any text that is typically 2-3 words, capitalized, near "Prior to"
                all_text_elements = fm_section.find_all(string=True)
                
                for node in all_text_elements:
                    text = clean_text(node)
                    if not text or len(text) < 5 or text in ["Fund Management"]: continue
                    
                    # Heuristic: names usually have titles (Mr.) or capitalized initials
                    is_name = bool(re.match(r"^(Mr\.|Ms\.|NS |AAC |SK )\w+", text, re.IGNORECASE))
                    # Or it's a short 2-4 word string in a card
                    if not is_name and 1 < len(text.split()) < 5 and any(c.isupper() for c in text):
                        # check if nearby text has "Experience" or "Prior to"
                        parent_card = node.find_parent('div', class_=re.compile(r"card", re.IGNORECASE)) or node.find_parent('div').find_parent('div')
                        if parent_card and re.search(r"Prior to", parent_card.get_text(), re.IGNORECASE):
                            is_name = True
                            
                    if is_name:
                        if any(fm["name"] == text for fm in data["fund_managers"]): continue
                        
                        fm = {
                            "name": text,
                            "tenure_start": None,
                            "education": None,
                            "experience": None,
                            "other_schemes_managed": []
                        }
                        
                        # Search nearby text nodes
                        card = node.find_parent('div', class_=re.compile(r"card", re.IGNORECASE)) or node.find_parent('div').find_parent('div')
                        if card:
                            card_text = clean_text(card)
                            # Experience usually starts with "Prior to..."
                            exp_match = re.search(r"(Prior to.*?)(?=\s*Also manages|\Z)", card_text, re.IGNORECASE | re.DOTALL)
                            if exp_match: fm["experience"] = exp_match.group(1).strip()
                            
                            # Schemes
                            schemes_section = card.find(string=re.compile(r"Also manages these schemes", re.IGNORECASE))
                            if schemes_section:
                                scheme_container = schemes_section.find_parent().find_next_sibling()
                                if scheme_container:
                                    items = scheme_container.find_all('a') or scheme_container.find_all('div', class_=re.compile("text"))
                                    fm["other_schemes_managed"] = [clean_text(i) for i in items if clean_text(i)]
                        data["fund_managers"].append(fm)
        if not data["fund_managers"]:
            log_miss("fund_managers", "Could not locate manager cards")

        # --- 2.8 Holdings Table ---
        holdings_header = soup.find(string=re.compile(r"^Holdings \(\d+\)", re.IGNORECASE))
        if holdings_header:
            count_match = re.search(r"\((\d+)\)", clean_text(holdings_header))
            if count_match: data["holdings"]["total_count"] = int(count_match.group(1))
            
            h_table = holdings_header.find_parent('section').find('table') or holdings_header.find_parent('div').find_parent('div').find('table')
            if h_table:
                # Headers are Name, Sector, Instrument, Assets
                rows = h_table.find('tbody').find_all('tr') if h_table.find('tbody') else h_table.find_all('tr')[1:]
                for row in rows:
                    cols = row.find_all('td')
                    if len(cols) >= 3: # Some interfaces merge instrument and sector
                        st = {
                            "name": clean_text(cols[0]),
                            "sector": clean_text(cols[1]),
                            "instrument": "Equity", # Usually safe default if column merged
                            "allocation_pct": clean_numeric(clean_text(cols[-1]))
                        }
                        if len(cols) >= 4:
                            st["instrument"] = clean_text(cols[2])
                        data["holdings"]["stocks"].append(st)
        else:
            log_miss("holdings", "Holdings header/table not found")

        # --- 2.9 Fund House Details ---
        fh_rank = extract_from_table_or_div(soup, r"^Rank")
        data["fund_house_details"]["name"] = data["identity"].get("fund_house", "Groww Mutual Fund")
        data["fund_house_details"]["date_of_incorporation"] = extract_from_table_or_div(soup, r"Date of Incorporation")
        data["fund_house_details"]["phone"] = extract_from_table_or_div(soup, r"Phone")
        data["fund_house_details"]["email"] = extract_from_table_or_div(soup, r"Email|E-mail")
        data["fund_house_details"]["website"] = extract_from_table_or_div(soup, r"Website")
        data["fund_house_details"]["address"] = extract_from_table_or_div(soup, r"Address")
        data["fund_house_details"]["registrar_transfer_agent"] = extract_from_table_or_div(soup, r"Registrar.*Transfer Agent")
        
        # --- 2.10 Document Links ---
        sid_link = soup.find('a', string=re.compile(r"Scheme Information Document", re.IGNORECASE))
        data["document_links"]["sid_page"] = sid_link['href'] if sid_link and sid_link.has_attr('href') else "https://growwmf.in/"
        
        # Load the precise PDF links from the meta files dumped by download step
        try:
            meta_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "pdfs", data["fund_slug"])
            with open(os.path.join(meta_dir, "SID_meta.json"), "r") as f:
                sid_meta = json.load(f)
                data["document_links"]["sid_pdf"] = sid_meta.get("source_url")
            with open(os.path.join(meta_dir, "KIM_meta.json"), "r") as f:
                kim_meta = json.load(f)
                data["document_links"]["kim_pdf"] = kim_meta.get("source_url")
        except Exception as e:
            log_miss("document_links", f"Could not read meta sidecars: {e}")

    except Exception as e:
        logger.error(f"Error parsing DOM natively: {str(e)}")
        
    # --- 3.1 Data Quality Rules Validation ---
    critical_fields = [
        ("nav", data["live_metrics"].get("nav")),
        ("fund_size_cr", data["live_metrics"].get("fund_size_cr")),
        ("expense_ratio_pct", data["live_metrics"].get("expense_ratio_pct")),
        ("exit_load", data["costs_and_taxation"].get("exit_load")),
        ("min_sip", data["investment_limits"].get("min_sip")),
        ("investment_objective", data["identity"].get("investment_objective")),
        ("benchmark", data["identity"].get("benchmark"))
    ]
    for field_name, val in critical_fields:
        if val is None:
            logger.error(f"CRITICAL VALIDATION FAILED on {data['fund_slug']}: {field_name} is null.")
            
    return data

async def run_scraper():
    logger.info("Initializing Playwright Engine for Advanced DOM Parsing...")
    
    os.makedirs(os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "web"), exist_ok=True)
    results = []
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        
        for url in GROWW_URLS:
            logger.info(f"Navigating to {url}")
            try:
                await page.goto(url, wait_until="networkidle", timeout=60000)
                # Wait heavily for the single page app React tree to fully populate
                await page.wait_for_timeout(5000) 
                html = await page.content()
                
                parsed_data = parse_html_to_schema(html, url)
                results.append(parsed_data)
                
                # Save individual web JSON
                web_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "web", f"{parsed_data['fund_slug']}_scraped.json")
                with open(web_path, "w", encoding='utf-8') as f:
                    json.dump(parsed_data, f, indent=2)
                
            except Exception as e:
                logger.error(f"Exception while loading {url}: {str(e)}")
                
        await browser.close()
        
    return results

# Expose a wrapper for the Orchestrator
async def scrape_groww_fund(url: str):
    """
    Deprecated direct function. Orchestrator should call run_scraper() once
    to do batch processing instead. Returning a dummy redirect signal.
    """
    return {"deprecated": "Use scrape_all_web_metrics() from orchestrator directly"}

async def scrape_all_web_metrics() -> list[dict]:
    """Batch scrapes all urls, saves individual files, and returns the merged result."""
    return await run_scraper()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    asyncio.run(run_scraper())
