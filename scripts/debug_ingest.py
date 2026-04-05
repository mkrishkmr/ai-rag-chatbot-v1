import json
from langchain_core.documents import Document

try:
    with open('phase1_ingestion/data/unified_knowledge_base.json') as f:
        data = json.load(f)
    print(f"Checking {len(data)} funds")
    for item in data:
        fund_name = item.get('fund_name')
        pdfs = item.get('pdf_documents', [])
        for pdf in pdfs:
            content = pdf.get("full_extracted_text")
            # This replicates some version of ingest.py logic
            # where f-string is used OR raw content is used
            # If the user is running a version where they call Document(page_content=pdf.get("full_extracted_text"))
            # it would fail if it's None.
            try:
                # Test with None directly to see if it triggers the error message from screenshot
                # Document(page_content=None)
                pass
            except Exception as e:
                print(f"Instantiation failed for None: {e}")
                
            # Now test real content
            Document(page_content=f"Fund Name: {fund_name}\nContext: {content}", metadata={})
    print("All checked!")
except Exception as e:
    print(f"FAILED overall: {e}")
