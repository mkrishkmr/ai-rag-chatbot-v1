# Groww AI Fact Engine

Groww AI Fact Engine is a RAG-based (Retrieval-Augmented Generation) chatbot designed to answer strict factual queries about 4 specific Groww mutual fund schemes. It employs rigorous guardrails to ensure responses are accurate, compliant, and strictly factual.

## Key Features

- **Strict Factual Retrieval**: Answers are generated *exclusively* from scraped web data and official PDF documents (SID/KIM).
- **PII Guardrails**: Automatically detects and blocks PAN/Aadhaar data in user inputs.
- **Advice Refusal**: Politely declines requests for investment advice, stock predictions, or fund comparisons.
- **Contextual Awareness**: Resolves pronouns like "it" and "that" using conversation history.
- **Streaming Responses**: Uses Server-Sent Events (SSE) for real-time answer rendering.
- **Citation Cards**: Transparently displays the exact source document or webpage URL used to answer the query.

## Supported Funds

1. Groww Nifty 50 Index Fund Direct Growth
2. Groww Value Fund Direct Growth
3. Groww Aggressive Hybrid Fund Direct Growth
4. Groww ELSS Tax Saver Fund Direct Growth

## Tech Stack

- **Frontend**: Next.js 14, React, TailwindCSS, Glassmorphism UI
- **Backend API**: FastAPI, Python 3.9+
- **RAG/LLM Interfacing**: LangChain, Groq (llama-3.1-8b-instant)
- **Vector Database**: ChromaDB
- **Embeddings**: Google Gemini (`gemini-embedding-001`)
- **Ingestion**: Playwright (web scraping), PyMuPDF (PDF parsing)

## Directory Structure

```text
.
├── phase1_ingestion/   # Scrapers and PDF parsers
├── phase2_rag/         # Vector DB insertion and Retriever logic
├── phase3_api/         # FastAPI backend, PII handling, Guardrails
├── frontend/           # Next.js UI
└── docs/               # System documentation
```

## Documentation

- [Architecture Overview](architecture/overview.md)
- [API Documentation](api/overview.md)
- [User Journeys](user-journeys/factual-query.md)
- [Testing Strategy](testing/strategy.md)
- [Architecture Decision Records (ADRs)](decisions/2026-03-01-why-chromadb.md)

## Deployment

- **Frontend**: Deploys to Vercel.
- **Backend**: Deploys to Render.
- See [Infrastructure Docs](architecture/infra.md) for deployment procedures.
