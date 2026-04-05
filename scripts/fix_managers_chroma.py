import os
import json
import logging
from langchain_core.documents import Document
from phase2_rag.chroma_db import get_vector_store
from phase2_rag.ingest import ingest
import hashlib

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(message)s')

vectorstore = get_vector_store()

# Find and delete existing manager chunks
try:
    results = vectorstore._collection.get(where={"chunk_type": "manager_chunk"})
    if results["ids"]:
        logging.info(f"Deleting {len(results['ids'])} old manager chunks")
        vectorstore._collection.delete(ids=results["ids"])
except Exception as e:
    logging.info(f"Warning during delete: {e}")

# Read unified JSON
with open("phase1_ingestion/data/unified_knowledge_base.json", "r") as f:
    data = json.load(f)

# Extract only manager chunks
docs = []
for item in data:
    fund_name = item.get("fund_name", "Unknown Fund")
    fund_slug = item.get("fund_slug", "unknown")
    source_url = item.get("source_url", "")
    scraped_at = item.get("scraped_at", "")
    
    managers = item.get("fund_managers", [])
    for fm in managers:
        content_str = json.dumps(fm, indent=2)
        meta = {
            "source": "Web",
            "document_type": "Web",
            "fund_slug": fund_slug,
            "fund_name": fund_name,
            "source_url": source_url,
            "scraped_at": scraped_at,
            "chunk_type": "manager_chunk"
        }
        
        doc = Document(
            page_content=f"Fund Name: {fund_name}\nSection: manager_chunk\n{content_str}",
            metadata=meta
        )
        
        # Consistent hash
        content_hash = hashlib.sha256(doc.page_content.encode()).hexdigest()[:6]
        doc.metadata["doc_id"] = f"{fund_slug}_manager_chunk_web_{content_hash}"
        docs.append(doc)

# Embed
logging.info(f"Embedding {len(docs)} new manager chunks...")
ingest(docs, vectorstore)
logging.info("Done fixing managers!")
