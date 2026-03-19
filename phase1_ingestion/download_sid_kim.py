import os
import json
import logging
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timezone

# Configure standard logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

FUND_DOCUMENTS = [
    {
        "fund_name": "Groww Nifty 50 Index Fund Direct Growth",
        "fund_slug": "nifty50_index",
        "documents": {
            "SID": "https://assets-netstorage.growwmf.in/compliance_docs/Downloads/SID/SID_Groww%20Nifty%2050%20Index%20Fund.pdf",
            "KIM": "https://assets-netstorage.growwmf.in/compliance_docs/Downloads/KIM/KIM_Groww%20Nifty%2050%20Index%20Fund.pdf",
        }
    },
    {
        "fund_name": "Groww Value Fund Direct Growth",
        "fund_slug": "value_fund",
        "documents": {
            "SID": "https://assets-netstorage.growwmf.in/compliance_docs/Downloads/SID/SID_Groww%20Value%20Fund.pdf",
            "KIM": "https://assets-netstorage.growwmf.in/compliance_docs/Downloads/KIM/KIM_Groww%20Value%20Fund.pdf",
        }
    },
    {
        "fund_name": "Groww Aggressive Hybrid Fund Direct Growth",
        "fund_slug": "aggressive_hybrid",
        "documents": {
            "SID": "https://assets-netstorage.growwmf.in/compliance_docs/Downloads/SID/SID_Groww%20Aggresive%20Hybrid%20Fund.pdf",
            "KIM": "https://assets-netstorage.growwmf.in/compliance_docs/Downloads/KIM/KIM_Groww%20Aggresive%20Hybrid%20Fund.pdf",
        }
    },
    {
        "fund_name": "Groww ELSS Tax Saver Fund Direct Growth",
        "fund_slug": "elss_tax_saver",
        "documents": {
            "SID": "https://assets-netstorage.growwmf.in/compliance_docs/Downloads/SID/SID_Groww%20ELSS%20Tax%20Saver%20Fund.pdf",
            "KIM": "https://assets-netstorage.growwmf.in/compliance_docs/Downloads/KIM/KIM_Groww%20ELSS%20Tax%20Saver%20Fund.pdf",
        }
    },
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Referer": "https://www.growwmf.in/downloads/sid"
}

BASE_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "pdfs")

# Store results for the end-of-run summary
download_results = []

def get_fallback_url(doc_type: str, fund_slug: str) -> str:
    """Attempts to scrape the official index pages if the CDN URL fails."""
    logger.warning(f"Attempting index-page fallback from growwmf.in for {fund_slug} {doc_type}")
    
    index_url = "https://www.growwmf.in/downloads/sid" if doc_type == "SID" else "https://www.growwmf.in/downloads/kim"
    
    # Keyword mapping based on the fund slugs to match <a href> text
    keyword_map = {
        "nifty50_index": "Nifty 50 Index Fund",
        "value_fund": "Value Fund",
        "aggressive_hybrid": "Aggresive Hybrid", # Preserve AMC typo
        "elss_tax_saver": "ELSS Tax Saver"
    }
    target_keyword = keyword_map.get(fund_slug, "")
    
    try:
        r = requests.get(index_url, headers=HEADERS, timeout=10)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, 'html.parser')
        
        for a_tag in soup.find_all('a', href=True):
            href = a_tag['href']
            text = a_tag.get_text()
            if href.lower().endswith('.pdf') and target_keyword.lower() in text.lower():
                logger.info(f"Fallback successful. Found URL: {href}")
                return href
                
        logger.error(f"Fallback failed. Could not find PDF link containing '{target_keyword}' on {index_url}")
        return ""
    except Exception as e:
        logger.error(f"Fallback failed with exception: {str(e)}")
        return ""

def download_file(url: str, save_path: str) -> bool:
    """Downloads a file in chunks. Returns True if successful."""
    try:
        r = requests.get(url, headers=HEADERS, stream=True, timeout=15)
        r.raise_for_status()
        
        with open(save_path, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        return True
    except requests.exceptions.RequestException as e:
        logger.error(f"Download error from {url}: {e}")
        return False

def write_metadata(meta_path: str, meta_data: dict):
    """Writes the sidecar JSON metadata file."""
    with open(meta_path, 'w', encoding='utf-8') as f:
        json.dump(meta_data, f, indent=2)

def process_document(fund_data: dict, doc_type: str, primary_url: str):
    """Handles the caching, downloading, integrity, and metadata writing for a specific document."""
    fund_slug = fund_data["fund_slug"]
    fund_name = fund_data["fund_name"]
    direction_dir = os.path.join(BASE_DATA_DIR, fund_slug)
    os.makedirs(direction_dir, exist_ok=True)
    
    file_path = os.path.join(direction_dir, f"{doc_type}.pdf")
    meta_path = os.path.join(direction_dir, f"{doc_type}_meta.json")
    
    # 1. CACHE CHECK
    if os.path.exists(file_path):
        size_bytes = os.path.getsize(file_path)
        if size_bytes > 50 * 1024:  # > 50KB
            logger.info(f"Already cached: {file_path}")
            download_results.append({
                "fund_slug": fund_slug,
                "doc_type": doc_type,
                "size_kb": size_bytes // 1024,
                "status": "cached"
            })
            return
            
    # 2. DOWNLOAD
    logger.info(f"Downloading {fund_slug} {doc_type} from {primary_url}...")
    success = download_file(primary_url, file_path)
    actual_url = primary_url
    
    # 3. FALLBACK (If primary fails)
    if not success:
        logger.warning(f"Primary CDN URL failed for {fund_slug} {doc_type}.")
        fallback_url = get_fallback_url(doc_type, fund_slug)
        if fallback_url:
            success = download_file(fallback_url, file_path)
            actual_url = fallback_url
            
    if not success:
        logger.error(f"Failed to download {fund_slug} {doc_type} from all sources.")
        if os.path.exists(file_path):
            os.remove(file_path)
        download_results.append({
            "fund_slug": fund_slug,
            "doc_type": doc_type,
            "size_kb": 0,
            "status": "FAILED"
        })
        return

    # 4. INTEGRITY CHECK
    size_bytes = os.path.getsize(file_path)
    if size_bytes < 10 * 1024:  # < 10KB
        logger.error(f"FAILED integrity check for {fund_slug} {doc_type} — file < 10KB, likely an HTML error page. Skipping.")
        os.remove(file_path)
        download_results.append({
            "fund_slug": fund_slug,
            "doc_type": doc_type,
            "size_kb": size_bytes // 1024,
            "status": "FAILED"
        })
        return
        
    # 5. METADATA SIDECAR
    size_kb = size_bytes // 1024
    meta_data = {
        "fund_name": fund_name,
        "fund_slug": fund_slug,
        "doc_type": doc_type,
        "source_url": actual_url,
        "downloaded_at": datetime.now(timezone.utc).isoformat(),
        "file_size_kb": size_kb,
        "url_source": "growwmf.in_official_cdn"
    }
    write_metadata(meta_path, meta_data)
    
    logger.info(f"Successfully downloaded {fund_slug} {doc_type} ({size_kb} KB)")
    download_results.append({
        "fund_slug": fund_slug,
        "doc_type": doc_type,
        "size_kb": size_kb,
        "status": "downloaded"
    })

def print_summary():
    """Prints a formatted summary table of the run."""
    print("\nPDF Download Summary")
    print("-" * 50)
    
    success_count = 0
    total_count = len(download_results)
    
    for res in download_results:
        slug = res["fund_slug"].ljust(20)
        doc = res["doc_type"].ljust(5)
        size = f"{res['size_kb']} KB".ljust(8)
        status = res["status"]
        
        if status == "FAILED":
            icon = "❌"
            print(f"{icon}  {slug}{doc}{size}{status}")
        else:
            icon = "✅"
            success_count += 1
            print(f"{icon}  {slug}{doc}{size}{status}")
            
    print(f"\n{success_count}/{total_count} files ready. {total_count - success_count} failures.")

def get_all_pdf_paths() -> list[dict]:
    """
    Returns a list of dicts for all successfully downloaded PDFs.
    Only includes entries where the file exists on disk and is > 10KB.
    """
    valid_pdfs = []
    for fund in FUND_DOCUMENTS:
        fund_slug = fund["fund_slug"]
        fund_name = fund["fund_name"]
        direction_dir = os.path.join(BASE_DATA_DIR, fund_slug)
        
        for doc_type in ["SID", "KIM"]:
            file_path = os.path.join(direction_dir, f"{doc_type}.pdf")
            if os.path.exists(file_path) and os.path.getsize(file_path) > 10 * 1024:
                valid_pdfs.append({
                    "fund_slug": fund_slug,
                    "fund_name": fund_name,
                    "doc_type": doc_type,
                    "path": file_path
                })
    return valid_pdfs

if __name__ == "__main__":
    logger.info("Starting CDN Download sync for SID and KIM PDFs...")
    for fund in FUND_DOCUMENTS:
        for doc_type, primary_url in fund["documents"].items():
            process_document(fund, doc_type, primary_url)
            
    print_summary()
