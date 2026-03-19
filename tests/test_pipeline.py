"""
tests/test_pipeline.py

LOCAL DEVELOPMENT — STEP BY STEP
Prerequisites:

Python 3.10+ with venv activated
Node.js 18+ for the frontend
.env file with GOOGLE_API_KEY and GROQ_API_KEY set

Step 1 — Download PDFs and scrape web data:
python -m phase1_ingestion.run_ingestion
Expected output: data/pdfs/ populated, data/unified_knowledge_base.json created
Step 2 — Embed into ChromaDB:
python -m phase2_rag.ingest
Expected output: chroma_db/ populated, ~60 documents ingested
Note: takes ~6 minutes on free Gemini tier due to rate limiting
Step 3 — Verify everything with tests:
python -m pytest tests/ -v
Expected output: all tests pass except live LLM test if GROQ_API_KEY absent
Step 4 — Start everything:
./start.sh
Backend:  http://localhost:8080/health → {"status":"ok"}
Frontend: http://localhost:3000
Manual test queries to verify end to end:
"What is the exit load for Groww Value Fund?"
"Who manages the Groww ELSS Tax Saver Fund?"
"What is the minimum SIP for Groww Nifty 50 Index Fund?"
"What is the NAV of SBI Bluechip Fund?"  ← must return scope block
"My PAN is ABCDE1234F"                   ← must return 400
=============================================================

Full local test suite for the Groww AI Fact Engine.
Run with: python -m pytest tests/ -v
"""

import os
import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# ============================================================
# PHASE 1 TESTS — Ingestion
# ============================================================

class TestPDFDownload:

    def test_all_pdf_files_exist(self):
        """All 8 PDFs (4 SIDs + 4 KIMs) must exist after download."""
        from phase1_ingestion.download_sid_kim import FUND_DOCUMENTS
        for fund in FUND_DOCUMENTS:
            for doc_type in ["SID", "KIM"]:
                path = Path(f"phase1_ingestion/data/pdfs/{fund['fund_slug']}/{doc_type}.pdf")
                assert path.exists(), f"Missing: {path}"

    def test_all_pdfs_above_minimum_size(self):
        """All PDFs must be larger than 10KB to be valid."""
        from phase1_ingestion.download_sid_kim import FUND_DOCUMENTS
        for fund in FUND_DOCUMENTS:
            for doc_type in ["SID", "KIM"]:
                path = Path(f"phase1_ingestion/data/pdfs/{fund['fund_slug']}/{doc_type}.pdf")
                if path.exists():
                    size_kb = path.stat().st_size / 1024
                    assert size_kb > 10, (
                        f"{path} is only {size_kb:.1f}KB — likely an error page"
                    )

    def test_all_sidecar_meta_files_exist(self):
        """Every PDF must have a sidecar _meta.json with source_url."""
        from phase1_ingestion.download_sid_kim import FUND_DOCUMENTS
        for fund in FUND_DOCUMENTS:
            for doc_type in ["SID", "KIM"]:
                meta_path = Path(
                    f"phase1_ingestion/data/pdfs/{fund['fund_slug']}/{doc_type}_meta.json"
                )
                assert meta_path.exists(), f"Missing sidecar: {meta_path}"
                with open(meta_path) as f:
                    meta = json.load(f)
                assert "source_url" in meta, f"No source_url in {meta_path}"
                assert meta["source_url"].startswith("https://"), (
                    f"Invalid source_url in {meta_path}"
                )

    def test_get_all_pdf_paths_returns_eight_entries(self):
        """get_all_pdf_paths() must return exactly 8 valid entries."""
        from phase1_ingestion.download_sid_kim import get_all_pdf_paths
        paths = get_all_pdf_paths()
        assert len(paths) == 8, (
            f"Expected 8 PDF entries, got {len(paths)}"
        )
        for entry in paths:
            assert "fund_slug" in entry
            assert "fund_name" in entry
            assert "doc_type" in entry
            assert "path" in entry
            assert Path(entry["path"]).exists()


class TestWebScraper:

    def test_unified_json_exists(self):
        """Unified knowledge base JSON must exist after scraping."""
        path = Path("phase1_ingestion/data/unified_knowledge_base.json")
        assert path.exists(), "phase1_ingestion/data/unified_knowledge_base.json not found"

    def test_unified_json_has_four_funds(self):
        """Unified JSON must contain all 4 funds."""
        with open("phase1_ingestion/data/unified_knowledge_base.json") as f:
            data = json.load(f)
        assert len(data) == 4, f"Expected 4 funds, got {len(data)}"

    def test_all_critical_fields_present(self):
        """Every fund entry must have all critical fields non-null."""
        critical_fields = [
            ("live_metrics", "nav"),
            ("live_metrics", "nav_date"),
            ("live_metrics", "fund_size_cr"),
            ("live_metrics", "expense_ratio_pct"),
            ("costs_and_taxation", "exit_load"),
            ("investment_limits", "min_sip"),
            ("identity", "investment_objective"),
            ("identity", "benchmark"),
            ("source_url",),
        ]
        with open("phase1_ingestion/data/unified_knowledge_base.json") as f:
            data = json.load(f)
        for fund in data:
            fund_name = fund.get("fund_name", "unknown")
            for field_path in critical_fields:
                value = fund
                for key in field_path:
                    assert isinstance(value, dict), (
                        f"{fund_name}: {field_path} path broken at {key}"
                    )
                    value = value.get(key)
                assert value is not None, (
                    f"{fund_name}: critical field {'.'.join(field_path)} is null"
                )

    def test_source_url_present_on_all_funds(self):
        """Every fund must have a valid source_url field."""
        with open("phase1_ingestion/data/unified_knowledge_base.json") as f:
            data = json.load(f)
        for fund in data:
            assert fund.get("source_url", "").startswith("https://groww.in"), (
                f"{fund.get('fund_name')}: missing or invalid source_url"
            )

    def test_document_links_present(self):
        """Every fund must have sid_pdf and kim_pdf URLs."""
        with open("phase1_ingestion/data/unified_knowledge_base.json") as f:
            data = json.load(f)
        for fund in data:
            links = fund.get("document_links", {})
            assert links.get("sid_pdf", "").startswith("https://"), (
                f"{fund.get('fund_name')}: missing sid_pdf link"
            )
            assert links.get("kim_pdf", "").startswith("https://"), (
                f"{fund.get('fund_name')}: missing kim_pdf link"
            )

    def test_holdings_scraped(self):
        """Every fund must have at least 1 holding scraped."""
        with open("phase1_ingestion/data/unified_knowledge_base.json") as f:
            data = json.load(f)
        for fund in data:
            stocks = fund.get("holdings", {}).get("stocks", [])
            assert len(stocks) > 0, (
                f"{fund.get('fund_name')}: no holdings scraped"
            )

    def test_fund_managers_scraped(self):
        """Every fund must have at least 1 fund manager."""
        with open("phase1_ingestion/data/unified_knowledge_base.json") as f:
            data = json.load(f)
        for fund in data:
            managers = fund.get("fund_managers", [])
            assert len(managers) > 0, (
                f"{fund.get('fund_name')}: no fund managers scraped"
            )


# ============================================================
# PHASE 2 TESTS — ChromaDB
# ============================================================

class TestChromaDB:

    @pytest.fixture(scope="class")
    def vectorstore(self):
        """Load the existing ChromaDB — do not re-embed."""
        import chromadb
        from langchain_chroma import Chroma
        from unittest.mock import MagicMock
        # Mock embeddings so this test never calls the Gemini API
        mock_embeddings = MagicMock()
        mock_embeddings.embed_documents = lambda texts: [[0.1] * 768] * len(texts)
        mock_embeddings.embed_query = lambda text: [0.1] * 768
        client = chromadb.PersistentClient(path="chroma_db/")
        return Chroma(
            client=client,
            collection_name="groww_funds",
            embedding_function=mock_embeddings
        )

    def test_chromadb_is_populated(self, vectorstore):
        """ChromaDB must have at least 40 documents after ingestion."""
        count = vectorstore._collection.count()
        assert count >= 40, (
            f"ChromaDB has only {count} documents — ingestion may have failed"
        )

    def test_all_fund_slugs_present(self, vectorstore):
        """All 4 fund slugs must be represented in ChromaDB metadata."""
        expected_slugs = {
            "nifty50_index", "value_fund",
            "aggressive_hybrid", "elss_tax_saver"
        }
        result = vectorstore._collection.get(include=["metadatas"])
        found_slugs = {
            m.get("fund_slug")
            for m in result["metadatas"]
            if m.get("fund_slug")
        }
        for slug in expected_slugs:
            assert slug in found_slugs, (
                f"fund_slug '{slug}' not found in ChromaDB"
            )

    def test_source_url_in_all_metadata(self, vectorstore):
        """Every ChromaDB document must have a source_url in metadata."""
        result = vectorstore._collection.get(include=["metadatas"])
        missing = [
            i for i, m in enumerate(result["metadatas"])
            if not m.get("source_url")
        ]
        assert len(missing) == 0, (
            f"{len(missing)} ChromaDB documents are missing source_url"
        )

    def test_both_pdf_and_web_sources_present(self, vectorstore):
        """ChromaDB must contain both PDF and Web source chunks."""
        result = vectorstore._collection.get(include=["metadatas"])
        sources = {m.get("source") for m in result["metadatas"]}
        assert "PDF" in sources, "No PDF chunks found in ChromaDB"
        assert "Web" in sources, "No Web chunks found in ChromaDB"

    def test_sid_and_kim_doc_types_present(self, vectorstore):
        """ChromaDB must contain both SID and KIM doc_type chunks."""
        result = vectorstore._collection.get(include=["metadatas"])
        doc_types = {m.get("doc_type") for m in result["metadatas"]}
        assert "SID" in doc_types, "No SID chunks found in ChromaDB"
        assert "KIM" in doc_types, "No KIM chunks found in ChromaDB"


# ============================================================
# PHASE 3 TESTS — Guardrails
# ============================================================

class TestGuardrails:

    def test_pii_pan_blocked(self):
        """Queries containing PAN numbers must be blocked."""
        from phase3_api.guardrails import contains_pii
        assert contains_pii("My PAN is ABCDE1234F") is True

    def test_pii_aadhaar_blocked(self):
        """Queries containing Aadhaar numbers must be blocked."""
        from phase3_api.guardrails import contains_pii
        assert contains_pii("My Aadhaar is 1234 5678 9012") is True

    def test_clean_query_not_blocked(self):
        """Normal fund queries must not be flagged as PII."""
        from phase3_api.guardrails import contains_pii
        assert contains_pii("What is the NAV of Groww Value Fund?") is False

    def test_in_scope_fund_query_passes(self):
        """Queries about the 4 funds must pass the scope check."""
        from phase3_api.guardrails import is_query_in_scope
        in_scope = [
            "What is the exit load for Groww Value Fund?",
            "Who is the fund manager of the ELSS fund?",
            "What is the NAV today?",
            "Show me the expense ratio",
            "What is the minimum SIP amount?",
        ]
        for query in in_scope:
            assert is_query_in_scope(query) is True, (
                f"Valid query incorrectly blocked: '{query}'"
            )

    def test_out_of_scope_query_blocked(self):
        """Queries about other funds or unrelated topics must be blocked."""
        from phase3_api.guardrails import is_query_in_scope
        out_of_scope = [
            "What is the NAV of SBI Bluechip Fund?",
            "Who won the cricket match yesterday?",
            "Write me a Python script",
            "What is the weather in Mumbai?",
        ]
        for query in out_of_scope:
            assert is_query_in_scope(query) is False, (
                f"Out-of-scope query incorrectly passed: '{query}'"
            )

    def test_system_prompt_contains_context_placeholder(self):
        """System prompt must contain {context} and {question} placeholders."""
        from phase3_api.guardrails import SYSTEM_PROMPT
        assert "{context}" in SYSTEM_PROMPT, (
            "SYSTEM_PROMPT is missing {context} placeholder"
        )
        assert "{question}" in SYSTEM_PROMPT, (
            "SYSTEM_PROMPT is missing {question} placeholder"
        )

    def test_system_prompt_contains_no_answer_phrase(self):
        """System prompt must contain the exact no-answer fallback phrase."""
        from phase3_api.guardrails import SYSTEM_PROMPT
        assert "I don't have that information in my knowledge base" in SYSTEM_PROMPT


# ============================================================
# PHASE 3 TESTS — FastAPI Endpoints
# ============================================================

class TestAPI:

    @pytest.fixture(scope="class")
    def client(self):
        from fastapi.testclient import TestClient
        from phase3_api.main import app
        return TestClient(app)

    def test_health_endpoint(self, client):
        """Health endpoint must return 200 with status ok."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"

    def test_pii_query_returns_400(self, client):
        """PAN in query must return HTTP 400."""
        response = client.post(
            "/api/chat",
            json={"query": "My PAN is ABCDE1234F, what is the NAV?"}
        )
        assert response.status_code == 400

    def test_out_of_scope_returns_scope_block(self, client):
        """Out-of-scope query must return gate_blocked=out_of_scope."""
        with patch("phase3_api.main.build_retriever") as mock_retriever:
            mock_obj = mock_retriever.return_value
            mock_obj.get_relevant_documents.return_value = []
            response = client.post(
                "/api/chat",
                json={"query": "What is the NAV of SBI Bluechip Fund?"}
            )
        # Collect SSE stream
        full = b"".join(response.iter_bytes())
        assert b"out_of_scope" in full

    def test_empty_query_returns_validation_message(self, client):
        """Empty query must return gate_blocked=empty_query."""
        response = client.post("/api/chat", json={"query": "  "})
        full = b"".join(response.iter_bytes())
        assert b"empty_query" in full

    def test_zero_retrieval_returns_not_in_kb(self, client):
        """Query with no matching chunks must return zero_retrieval block."""
        with patch("phase3_api.main.build_retriever") as mock_retriever:
            mock_obj = mock_retriever.return_value
            mock_obj.get_relevant_documents.return_value = []
            response = client.post(
                "/api/chat",
                json={"query": "What colour is the Groww logo?"}
            )
        full = b"".join(response.iter_bytes())
        assert b"zero_retrieval" in full

    @pytest.mark.skipif(
        not os.getenv("GROQ_API_KEY"),
        reason="GROQ_API_KEY not set — skipping live LLM test"
    )
    def test_valid_query_returns_answer_with_sources(self, client):
        """Valid in-scope query must return an answer with sources."""
        from langchain.schema import Document
        mock_doc = Document(
            page_content="The exit load for Groww Value Fund is Nil.",
            metadata={
                "fund_name": "Groww Value Fund Direct Growth",
                "fund_slug": "value_fund",
                "doc_type": "SID",
                "source": "PDF",
                "source_url": "https://assets-netstorage.growwmf.in/compliance_docs/Downloads/SID/SID_Groww%20Value%20Fund.pdf",
                "chunk_type": "investment_chunk",
                "page_number": 7
            }
        )
        with patch("phase3_api.main.build_retriever") as mock_retriever:
            mock_obj = mock_retriever.return_value
            mock_obj.get_relevant_documents.return_value = [mock_doc]
            response = client.post(
                "/api/chat",
                json={"query": "What is the exit load for Groww Value Fund?"}
            )
        full = b"".join(response.iter_bytes()).decode()
        assert "sources" in full
        assert "gate_blocked" in full
        # Answer must contain a citation
        assert "growwmf.in" in full or "Value Fund" in full
