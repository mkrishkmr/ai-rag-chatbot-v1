# Changelog

All notable changes to the Groww AI Fact Engine project will be documented in this file.

## [1.0.0] - 2026-03-20

### Added
- **RAG Engine Backend**: FastAPI backend integrating LangChain, Groq, and ChromaDB.
- **Frontend UI**: Next.js 14 frontend featuring a glassmorphism design and Server-Sent Events (SSE) for streaming text.
- **Strict Guardrails**: PII detector, financial advice blocker, and scope gate for handling queries outside the 4 Groww funds.
- **Pronoun Resolution**: In-memory message history tracking and LLM-based query rewriting to maintain conversation context.
- **Hybrid Retrieval Strategy**: Dynamically adjusts retrieval queries to prioritize Web data (for live metrics) or PDF data (for static rules).
- **Automated Data Ingestion**: Playwright-based web scraper and PyMuPDF-based PDF ingestion pipeline.
- **Source Deduplication**: Logic to ensure unique reference cards are displayed per source/URL.
- **Natural Language formatting**: `guardrails.py` instructions to prevent the model from leaking internal RAG mechanisms ("context chunks", "retrieved context") or URLs in the primary response text.
