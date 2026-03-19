# Database Architecture

The Groww AI Fact Engine uses **ChromaDB** as an embedded persistent vector store, located in the root `/chroma_db` directory.

## Embedding Model
We use **Google Gemini Embeddings** (`gemini-embedding-001`) via `langchain-google-genai`. This converts all ingested text into floating-point vectors for similarity search.

## Data Sources

The 1644 existing documents comprise two primary sources:
1. **Groww Web Scrapes**: Live data (such as NAV, Fund Size) extracted using Playwright scripts. Stored initially as JSON.
2. **Regulatory PDFs**: Scheme Information Documents (SID) and Key Information Memorandums (KIM) containing official rules (Exit Loads, Lock-ins, Investment Objectives). Parsed via PyMuPDF.

## Indexing Strategy
Chunks are broken down using semantic splitters. To ensure optimal retrieval:
- **Metadata**: Every chunk includes crucial metadata fields:
  - `fund_name`: e.g., "Groww Nifty 50 Index Fund Direct Growth"
  - `doc_type`: "Web" or "PDF"
  - `source_url`: URL of the original webpage or PDF asset.

## Query Strategies
- The backend evaluates the user's query against typical keywords.
- Questions regarding live figures (NAV, AUM/Fund Size, Expense Ratio) aggressively filter and rank `Web` chunks to the top.
- Questions regarding regulations (Lock-in, Exit Loads) prioritize `PDF` chunks.
- The `k` value is currently set to 12.
