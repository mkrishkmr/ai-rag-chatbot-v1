# Groww AI Fact Engine 💰🤖

A complete, end-to-end Retrieval-Augmented Generation (RAG) chatbot designed exclusively to provide strict, verified facts on Groww Mutual Funds. 

Built with **FastAPI**, **Next.js**, **Playwright**, and **ChromaDB**, and powered by **Groq** (`llama-3.1-8b-instant`) and **Google Gemini** embeddings.

---

## 🏗️ Architecture

The application is structured into four distinct execution phases:

1. **Phase 1 (Ingestion):** Playwright dynamically scrapes real-time mutual fund metrics (NAV, AUM, Expense Ratio) from Groww, while PyMuPDF parses the raw SID/KIM PDFs for hard rules (Exit Loads, Lock-ins).
2. **Phase 2 (RAG & Knowledge Base):** The extracted data is unified, chunked, and embedded into local ChromaDB vectors using Gemini's `models/gemini-embedding-001`.
3. **Phase 3 (Facts-Only API):** A FastAPI server exposes `/api/chat` with strict regex-based PII Guardrails (blocking PAN/Aadhaar) and strict LLM system prompts against giving financial advice.
4. **Phase 4 (Glassmorphism Next.js UI):** A polished React app utilizing TailwindCSS for frosted-glass aesthetics, streaming Server-Sent Events from the backend.

*(See `ARCHITECTURE.md` for the full technical data flow).*

---

## 📚 Source Data

This knowledge base is strictly partitioned to factual details mapped from these official 4 funds on Groww:
- **Groww Nifty 50 Index Fund Direct Growth**
- **Groww Value Fund Direct Growth**
- **Groww Aggressive Hybrid Fund Direct Growth**
- **Groww ELSS Tax Saver Fund Direct Growth**

### Sample Q&A

**Q: What is the Exit Load for the Value Fund?**
> A: The exit load for Groww Value Fund Direct Growth is 0.005% (from July 1st, 2020) as a stamp duty on investment. [View Source]

**Q: How do the NAVs compare?**
> A: The Groww Nifty 50 Index Fund has an NAV of ₹10.23, while the Groww ELSS Tax Saver Fund has an NAV of ₹12.45. [View Source]

**Q: What is the minimum SIP for each fund?**
> A: 
> * Groww Value Fund Direct Growth: ₹500
> * Groww Aggressive Hybrid Fund Direct Growth: ₹500
> * Groww ELSS Tax Saver Fund Direct Growth: ₹500

---

## ⚠️ Disclaimer

This application is built for educational and technical demonstration purposes only. The LLM is actively instructed **not to provide investment advice**. Always perform independent research or consult a SEBI-registered advisory professional before making financial investments. The data shown here is retrieved dynamically from web properties and may be subject to parsing inaccuracies. 

---

## 🚀 Execution & Deployment

### LOCAL DEVELOPMENT — STEP BY STEP
**Prerequisites:**
* Python 3.10+ with venv activated
* Node.js 18+ for the frontend
* `.env` file with `GOOGLE_API_KEY` and `GROQ_API_KEY` set

**Step 1 — Download PDFs and scrape web data:**
`python -m phase1_ingestion.run_ingestion`
_Expected output: `data/pdfs/` populated, `data/unified_knowledge_base.json` created_

**Step 2 — Embed into ChromaDB:**
`python -m phase2_rag.ingest`
_Expected output: `chroma_db/` populated, ~60 documents ingested_
_Note: takes ~6 minutes on free Gemini tier due to rate limiting_

**Step 3 — Verify everything with tests:**
`python -m pytest tests/ -v`
_Expected output: all tests pass except live LLM test if GROQ_API_KEY absent_

**Step 4 — Start everything:**
`./start.sh`
* Backend:  http://localhost:8080/health → `{"status":"ok"}`
* Frontend: http://localhost:3000

**Manual test queries to verify end to end:**
* "What is the exit load for Groww Value Fund?"
* "Who manages the Groww ELSS Tax Saver Fund?"
* "What is the minimum SIP for Groww Nifty 50 Index Fund?"
* "What is the NAV of SBI Bluechip Fund?"  ← must return scope block
* "My PAN is ABCDE1234F"                   ← must return 400

---
*For Cloud Deployment, refer to the step-by-step CI/CD guides in `DEPLOYMENT.md` for seamless routing to Render (Backend) and Vercel (Frontend).*
