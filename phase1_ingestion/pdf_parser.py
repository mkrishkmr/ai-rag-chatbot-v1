import os
import fitz  # PyMuPDF
import re

from phase1_ingestion.download_sid_kim import get_all_pdf_paths

def parse_pdf(path: str, fund_name: str, fund_slug: str, doc_type: str) -> dict:
    """Uses PyMuPDF to extract text from a PDF, looking for lock-in and exit load rules."""
    print(f"📄 Parsing {doc_type} for {fund_name}")
    try:
        doc = fitz.open(path)
        full_text = ""
        for page in doc:
            full_text += page.get_text()
            
        # Very basic regex extractions for demonstration
        lock_in = re.search(r"((?i)lock-in\s+period[^\.]+)", full_text)
        exit_load = re.search(r"((?i)exit\s+load[^\.]+)", full_text)

        return {
            "fund_name": fund_name,
            "fund_slug": fund_slug,
            "document_type": doc_type,
            "source": "PDF",
            "url_source": "growwmf.in_official_cdn",
            "extracted_rules": {
                "lock_in": lock_in.group(1).strip() if lock_in else "Not found/None",
                "exit_load": exit_load.group(1).strip() if exit_load else "Not found/None"
            },
            "raw_text_length": len(full_text),
            "full_extracted_text": full_text
        }
    except Exception as e:
        print(f"❌ Failed to parse PDF {path}: {e}")
        return {"error": str(e), "fund_slug": fund_slug, "doc_type": doc_type}

def parse_all_pdfs() -> list[dict]:
    pdf_list = get_all_pdf_paths()
    results = []
    for entry in pdf_list:
        parsed_data = parse_pdf(
            path=entry["path"],
            fund_name=entry["fund_name"],
            fund_slug=entry["fund_slug"],
            doc_type=entry["doc_type"]
        )
        results.append(parsed_data)
    return results

if __name__ == "__main__":
    print("Testing PyMuPDF parsing logic on live downloaded PDFs...")
    results = parse_all_pdfs()
    print(f"Successfully parsed {len(results)} PDFs.")
