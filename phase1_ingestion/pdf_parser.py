import os
import fitz  # PyMuPDF
import re

# Temporary local PDF testing URLs/Paths
PDF_SOURCES = {
    "Groww Nifty 50 Index": {"sid": "https://groww.in/documents/nifty_50_index/sid.pdf"},
    "Groww Value Fund": {"sid": "https://groww.in/documents/value_fund/sid.pdf"},
    "Groww Aggressive Hybrid": {"sid": "https://groww.in/documents/hybrid/sid.pdf"},
    "Groww ELSS Tax Saver": {"sid": "https://groww.in/documents/elss/sid.pdf"}
}

def download_pdf(url: str, save_path: str):
    import requests
    try:
        if not os.path.exists(save_path):
            print(f"📥 Downloading PDF from {url}...")
            r = requests.get(url, stream=True)
            if r.status_code == 200:
                with open(save_path, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=1024):
                        f.write(chunk)
                return True
            else:
                print(f"⚠️ Failed to download, status: {r.status_code}")
                return False
        return True
    except Exception as e:
        print(f"❌ Download error: {e}")
        return False

def extract_pdf_rules(pdf_path: str, fund_name: str) -> dict:
    """Uses PyMuPDF to extract text from a PDF, looking for lock-in and exit load rules."""
    print(f"📄 Parsing PDF for {fund_name}")
    try:
        doc = fitz.open(pdf_path)
        full_text = ""
        for page in doc:
            full_text += page.get_text()
            
        # Very basic regex extractions for demonstration
        lock_in = re.search(r"((?i)lock-in\s+period[^\.]+)", full_text)
        exit_load = re.search(r"((?i)exit\s+load[^\.]+)", full_text)

        return {
            "fund_name": fund_name,
            "document_type": "PDF SID/KIM",
            "extracted_rules": {
                "lock_in": lock_in.group(1).strip() if lock_in else "Not found/None",
                "exit_load": exit_load.group(1).strip() if exit_load else "Not found/None"
            },
            "raw_text_length": len(full_text)
        }
    except Exception as e:
        print(f"❌ Failed to parse PDF {pdf_path}: {e}")
        return {"error": str(e)}

if __name__ == "__main__":
    # Test block
    print("Testing PyMuPDF parsing logic...")
