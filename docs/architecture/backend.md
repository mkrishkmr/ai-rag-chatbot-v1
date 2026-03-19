# Backend Architecture

The backend is built using **FastAPI** to provide high-performance, asynchronous HTTP request handling. It sits in `/phase3_api` and links with `/phase2_rag`.

## Core Logic Pipeline (`main.py`)

1. **Endpoint**: `POST /api/chat`
2. **Pre-Processing Validation**:
    - **PII Guardrail**: Rejects inputs with 400 Bad Request if PANs or Aadhaar numbers are detected.
    - **Scope Gate**: Returns an immediate out-of-scope refusal if the query doesn't pertain to the 4 supported funds.
    - **Advice Gate**: Returns an advice refusal and redirection link if the user asks for investment recommendations.
3. **Query Expansion**:
    - **Pronoun Resolution**: Uses an auxiliary LLM call to replace words like "it" with the previously discussed fund.
    - **Fund Name Expansion**: Intercepts common partial names (e.g. "Nifty 50") and expands them to their official Groww name to improve exact-match retrieval in ChromaDB.
4. **Context Retrieval**:
    - Calls `retrieve_hybrid_context()` in `phase2_rag/retriever.py`.
    - Returns up to 12 heavily re-ranked chunks prioritizing WEB data for NAV inquiries.
5. **Streaming Generation**:
    - Constructs the dense `SYSTEM_PROMPT` imported from `guardrails.py`.
    - Passes context and user history to `ChatGroq`.
    - Uses an asynchronous generator to `yield` tokens as Server-Sent Events (SSE) back to the client.

## Guardrails (`guardrails.py`)
This file defines the strict instruction set for the LLM. It dictates that the model cannot:
- Make up information.
- Provide investment advice.
- Answer questions outside of the 4 specified funds.
- Output internal RAG terminology ("based on the context chunks").
- Output URLs inside the answer block.
- Output verbose SID boilerplate.
