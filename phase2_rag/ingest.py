import time
import logging
from math import ceil
import os
import sys
import json
from dotenv import load_dotenv
from langchain_core.documents import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter

load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("groww.ingest")

if not os.getenv("GOOGLE_API_KEY") or not os.getenv("GROQ_API_KEY"):
    logger.error("ERROR: GOOGLE_API_KEY and GROQ_API_KEY must be set in .env")
    sys.exit(1)

from phase2_rag.chroma_db import get_vector_store

# -------------------------------------------------------
# TUNING CONSTANTS
# Free tier:  BATCH_SIZE=5,  BATCH_DELAY=15  (~mins for 60 docs)
# Paid tier:  BATCH_SIZE=20, BATCH_DELAY=2
# DO NOT set BATCH_DELAY to 0 or remove it — this causes 429 loops
# DO NOT add a hard cap on document count — embed all documents
# -------------------------------------------------------
BATCH_SIZE = 5
BATCH_DELAY = 15

def ingest(documents: list, vectorstore):
    """
    Ingests all LangChain Document objects into ChromaDB.

    IMPORTANT: embeds ALL documents passed in. Do not truncate,
    sample, or cap the document list. The total chunk count depends
    on actual PDF and web content volume and will vary per run.

    Protections:
    1. BATCH_DELAY between every batch prevents 429 rate limit errors
    2. Exponential backoff (30s->60s->120s) handles transient 429s
    3. Deterministic IDs enable resume — already-embedded docs skipped
    """

    # --- Resume: skip already-embedded docs ---
    try:
        existing_ids = set(
            vectorstore._collection.get(include=[])["ids"]
        )
        if existing_ids:
            logger.info(
                f"Resuming: {len(existing_ids)} docs already in "
                f"ChromaDB — skipping these"
            )
    except Exception:
        existing_ids = set()

    # --- Assign deterministic IDs, filter to pending only ---
    pending = []
    for doc in documents:
        doc_id = (
            f"{doc.metadata.get('fund_slug', 'x')}_"
            f"{doc.metadata.get('chunk_type', 'chunk')}_"
            f"{doc.metadata.get('source', 'web')}_"
            f"{abs(hash(doc.page_content)) % 999999}"
        )
        if doc_id not in existing_ids:
            doc.metadata["doc_id"] = doc_id
            pending.append((doc_id, doc))

    if not pending:
        logger.info("All documents already in ChromaDB. Nothing to do.")
        return []

    total_batches = ceil(len(pending) / BATCH_SIZE)
    eta_minutes = ceil(total_batches * BATCH_DELAY / 60)
    logger.info(
        f"Embedding {len(pending)} documents in {total_batches} "
        f"batches. ETA: ~{eta_minutes} minutes. "
        f"Do not interrupt — use Ctrl+C only to pause, then re-run "
        f"to resume from where it stopped."
    )

    failed_batches = []

    for i in range(total_batches):
        batch = pending[i * BATCH_SIZE : (i + 1) * BATCH_SIZE]
        ids   = [b[0] for b in batch]
        docs  = [b[1] for b in batch]

        retry_waits = [0, 30, 60, 120]
        success = False

        for attempt, wait in enumerate(retry_waits):
            try:
                if wait > 0:
                    logger.warning(
                        f"Batch {i+1}/{total_batches}: 429 hit — "
                        f"waiting {wait}s (retry {attempt})"
                    )
                    time.sleep(wait)

                vectorstore.add_documents(docs, ids=ids)
                logger.info(
                    f"Batch {i+1}/{total_batches} done "
                    f"({min((i+1)*BATCH_SIZE, len(pending))}"
                    f"/{len(pending)} docs)"
                )
                success = True
                break

            except Exception as e:
                is_rate_limit = any(
                    t in str(e).lower() for t in [
                        "429", "rate limit", "quota",
                        "resource exhausted", "too many requests"
                    ]
                )
                if not is_rate_limit or attempt == len(retry_waits) - 1:
                    logger.error(
                        f"Batch {i+1}/{total_batches} failed "
                        f"permanently: {e}"
                    )
                    failed_batches.append(i + 1)
                    break

        # Always wait between batches — never skip this
        if i < total_batches - 1:
            time.sleep(BATCH_DELAY)

    # Summary
    succeeded = total_batches - len(failed_batches)
    logger.info("=" * 55)
    logger.info(
        f"Done: {succeeded}/{total_batches} batches succeeded. "
        f"{len(pending) - len(failed_batches) * BATCH_SIZE} docs embedded."
    )
    if failed_batches:
        logger.error(
            f"Failed batches: {failed_batches}. "
            f"Re-run python -m phase2_rag.ingest to resume — "
            f"completed batches will be skipped automatically."
        )
    logger.info("=" * 55)
    return failed_batches


def ingest_fact_sheet(json_path: str = "phase1_ingestion/data/unified_knowledge_base.json"):
    """Reads the generated JSON and ingests it into ChromaDB with semantic chunk metadata."""
    if not os.path.exists(json_path):
        logger.error(f"❌ Unified knowledge base {json_path} not found. Run Scraping first.")
        return

    with open(json_path, "r") as f:
        data = json.load(f)

    docs = []
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1200,
        chunk_overlap=200,
        length_function=len
    )
    
    for item in data:
        fund_name = item.get("fund_name", "Unknown Fund")
        fund_slug = item.get("fund_slug", "unknown")
        source_url = item.get("source_url", "")
        scraped_at = item.get("scraped_at", "")
        
        base_meta = {
            "source": "Web",
            "document_type": "Web",  # Unified key
            "fund_slug": fund_slug,
            "fund_name": fund_name,
            "source_url": source_url,
            "scraped_at": scraped_at
        }
        
        def add_chunk(chunk_name, content_str):
            if not content_str.strip(): return
            meta = base_meta.copy()
            meta["chunk_type"] = chunk_name
            docs.append(Document(page_content=f"Fund Name: {fund_name}\nSection: {chunk_name}\n{content_str}", metadata=meta))

        # 1. Identity Chunk
        id_text = json.dumps(item.get("identity", {}), indent=2) + "\n" + json.dumps(item.get("live_metrics", {}), indent=2)
        add_chunk("identity_chunk", id_text)
        
        # 2. Investment Chunk
        inv_text = json.dumps(item.get("investment_limits", {}), indent=2) + "\n" + json.dumps(item.get("costs_and_taxation", {}), indent=2)
        add_chunk("investment_chunk", inv_text)
        
        # 3. Returns Chunk
        add_chunk("returns_chunk", json.dumps(item.get("returns", {}), indent=2))
        
        # 4. Managers Chunk (One per manager)
        managers = item.get("fund_managers", [])
        for fm in managers:
            add_chunk("manager_chunk", json.dumps(fm, indent=2))
            
        # 5. Holdings Chunk (Blocks of 10)
        holdings = item.get("holdings", {}).get("stocks", [])
        for i in range(0, len(holdings), 10):
            block = holdings[i:i+10]
            add_chunk("holdings_chunk", json.dumps(block, indent=2))
            
        # 6. Fund House Chunk
        add_chunk("fund_house_chunk", json.dumps(item.get("fund_house_details", {}), indent=2))
        
        # 7. Documents Chunk
        add_chunk("documents_chunk", json.dumps(item.get("document_links", {}), indent=2))
        
        # Ingest the actual parsed PDFs (SID and KIM)
        pdf_documents = item.get("pdf_documents", [])
        for pdf in pdf_documents:
            pdf_doc_type = pdf.get("document_type", "SID")
            
            from pathlib import Path
            # Read source_url from sidecar meta.json
            meta_path = Path(f"phase1_ingestion/data/pdfs/{fund_slug}/{pdf_doc_type}_meta.json")
            source_url_sidecar = None
            if meta_path.exists():
                with open(meta_path) as meta_f:
                    meta = json.load(meta_f)
                    source_url_sidecar = meta.get("source_url")

            pdf_text = f"Fund Name: {pdf['fund_name']}\nDocument: {pdf_doc_type}\n"
            pdf_text += pdf.get("full_extracted_text", "")
            
            # Chunk the massive PDF text
            pdf_chunks = text_splitter.split_text(pdf_text)
            
            for i, chunk in enumerate(pdf_chunks):
                pdf_doc = Document(
                    page_content=f"Fund Name: {fund_name}\nContext: {chunk}",
                    metadata={
                        "source": "PDF",
                        "document_type": "PDF", # Unified key
                        "fund_slug": fund_slug,
                        "fund_name": pdf['fund_name'],
                        "page_number": i + 1,
                        "source_url": source_url_sidecar,
                        "chunk_type": f"{pdf_doc_type}_chunk"
                    }
                )
                docs.append(pdf_doc)

    vector_store = get_vector_store()
    logger.info(f"🚀 Passing {len(docs)} semantic chunks to the ingest loop...")
    ingest(docs, vector_store)
    logger.info("✅ Finished ingest_fact_sheet phase.")

if __name__ == "__main__":
    logger.info("Starting Phase 2 RAG Ingestion...")
    ingest_fact_sheet()
    logger.info("Phase 2 complete.")
