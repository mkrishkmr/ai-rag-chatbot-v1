# Groww Mutual Fund RAG Chatbot

This project contains the complete 4-phase factual RAG architecture designed for Render and Vercel.

## Features
1. **Phase 1: Ingestion & Verified Data Engine** (`phase1_ingestion/`)
   - Uses Playwright to asynchronously scrape dynamic metrics (NAV, Expense Ratios) from Groww URLs.
   - Uses PyMuPDF to parse rules from official SID/KIM PDFs.
2. **Phase 2: RAG & Hybrid Knowledge Base** (`phase2_rag/`)
   - Embeds findings into a local ChromaDB instance using LangChain and OpenAI `text-embedding-3-small`.
   - Utilizes Hybrid Retrieval routing to prioritize web documents for metrics and PDF documents for rules based on the user's query intent.
3. **Phase 3: Facts-Only API & Guardrails** (`phase3_api/`)
   - A FastAPI backend providing streaming chat endpoints.
   - Contains a strict Regex PII filter (blocks PAN and Aadhaar) and a system prompt forbidding investment advice.
4. **Phase 4: World-Class 'Glassmorphism' UI** (`phase4_frontend/`)
   - A Next.js dashboard featuring a dark FinTech aesthetic, frosted glass cards, Trust Indicators, and Quick Ask chips.

## Local Setup & Testing

### 1. Environment Variables
Rename `.env.example` to `.env` in the root directory and add your keys:
```
OPENAI_API_KEY=your_actual_key
```

### 2. Install Dependencies
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
playwright install chromium --with-deps
```

### 3. Run the Backend (FastAPI)
```bash
uvicorn phase3_api.main:app --host 0.0.0.0 --port 8080 --reload
```
*Note: Before chatting, hit the `/api/sync` endpoint using cURL or Postman to scrape and ingest the initial data into ChromaDB!*

### 4. Run the Frontend (Next.js)
In a new terminal:
```bash
cd phase4_frontend
npm install
npm run dev
```
Open `http://localhost:3000` to interact with the Glassmorphism UI.
