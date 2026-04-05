# Groww AI Fact Engine 💰🤖

A high-fidelity Retrieval-Augmented Generation (RAG) chatbot designed to provide strictly verified, factual data on Groww Mutual Funds. 

Built with **FastAPI**, **Next.js 14**, **Playwright**, and **ChromaDB**, and powered by **Google Gemini-3-Flash** and **Gemini Embeddings**.

---

## 🏗️ Technical Architecture

The application is structured into four specialized execution phases, optimized for data integrity and real-time freshness:

1. **Phase 1 (Knowledge Ingestion):** Uses **Playwright** to scrape dynamic metrics (NAV, AUM) and **PyMuPDF** to parse official SID/KIM PDFs for structural rules.
2. **Phase 2 (Hybrid Vector Store):** Implements a **Namespace Metadata Pattern** in ChromaDB. Every document chunk is tagged with a `fund_slug`, enabling filtered retrieval that eliminates "fund-mixing" hallucinations.
3. **Phase 3 (Intelligent API):** A FastAPI orchestration layer that features **Live Metrics Injection** (injecting real-time ground truth directly into prompts) and **Multi-Stage Guardrails** (blocking PII and Advisory queries).
4. **Phase 4 (Premium Discovery UI):** A refined Next.js interface utilizing **Glassmorphism** aesthetics, dynamic fund-specific theming, and interactive follow-up "Pulse Chips."

*(See [docs/architecture/ARCHITECTURE.md](docs/architecture/ARCHITECTURE.md) for the full technical data flow and Mermaid diagrams).*

---

## 📚 Source Data & Scope

The knowledge base is strictly partitioned to 4 official Groww funds:
*   **Groww Nifty 50 Index Fund** (Large-cap Index)
*   **Groww Value Fund** (Value Equity)
*   **Groww Aggressive Hybrid Fund** (Balanced Hybrid)
*   **Groww ELSS Tax Saver Fund** (Tax Saving Equity)

**Sources:** 16+ verified official public pages, including SIDs, KIMs, and live fund pages. (See [docs/SOURCES.md](docs/SOURCES.md) for the full list).

---

## 🔒 Security & Compliance

*   **PII Guardrails:** Automatic detection and blocking of Indian PAN and Aadhaar patterns.
*   **Zero-Advisory Logic:** Hard-coded refusal of investment advice, recommendations, or predictions.
*   **Factual Grounding:** Strict system prompts ensuring the model only answers based on provided context or real-time metrics.
*   **Observability:** All RAG interactions are logged to `traces.jsonl` (ignored in git) for transparent auditing. 
*   **Sample Q&A:** See [docs/SAMPLE_QA.md](docs/SAMPLE_QA.md) for verified examples.

---

## 🚀 Execution & Deployment

### LOCAL DEVELOPMENT
**Prerequisites:**
* Python 3.10+ & Node.js 18+
* `.env` file with `GOOGLE_API_KEY` and `GROQ_API_KEY`

**Step 1 — Download & Scrape:**
`python -m phase1_ingestion.run_ingestion`

**Step 2 — Vector Indexing:**
`python -m phase2_rag.ingest`

**Step 3 — Start Services:**
`./start.sh`
*   **Backend:** http://localhost:8080
*   **Frontend:** http://localhost:3000

---

## ⚠️ Disclaimer
This project is for educational purposes. The data is retrieved dynamically and may be subject to parsing delays. Always consult a SEBI-registered professional before investing.
