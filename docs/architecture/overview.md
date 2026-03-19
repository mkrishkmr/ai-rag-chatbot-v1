# Architecture Overview

The Groww AI Fact Engine follows a microservice architecture with a separated frontend and backend. The backend manages the RAG pipeline, taking queries, searching the vector database, and streaming LLM responses.

## System Diagram

```mermaid
sequenceDiagram
    participant User
    participant Frontend (Next.js)
    participant Backend (FastAPI)
    participant Guardrails
    participant ChromaDB
    participant Groq (LLM)
    
    User->>Frontend (Next.js): "What is the NAV of Nifty 50?"
    Frontend (Next.js)->>Backend (FastAPI): POST /api/chat
    
    activate Backend (FastAPI)
    Backend (FastAPI)->>Guardrails: PII Check
    Guardrails-->>Backend (FastAPI): OK
    
    Backend (FastAPI)->>Guardrails: Scope Check
    Guardrails-->>Backend (FastAPI): OK
    
    Backend (FastAPI)->>Guardrails: Advice Refusal Check
    Guardrails-->>Backend (FastAPI): OK
    
    Backend (FastAPI)->>Backend (FastAPI): Resolve Pronouns & Expand Fund Name
    
    Backend (FastAPI)->>ChromaDB: Retrieve chunks for query
    activate ChromaDB
    ChromaDB-->>Backend (FastAPI): Top K chunks (Web & PDF)
    deactivate ChromaDB
    
    Backend (FastAPI)->>Backend (FastAPI): Re-rank priority chunks
    
    Backend (FastAPI)->>Groq (LLM): Stream generate with context + rules
    activate Groq (LLM)
    Groq (LLM)-->>Backend (FastAPI): Stream tokens
    deactivate Groq (LLM)
    
    Backend (FastAPI)-->>Frontend (Next.js): SSE Stream Sequence
    deactivate Backend (FastAPI)
    
    Frontend (Next.js)-->>User: UI Renders Stream + Source Cards
```

## Component Summary

1. **Frontend**: Manages user input, chat history UI, Server-Sent Events parsing, and source card rendering. 
2. **Backend**: Validates queries, maintains conversation memory, controls context extraction, and manages generation.
3. **Database**: Persistent local ChromaDB containing 1644 chunks from 4 mutual funds. Embeddings are generated ahead of time using Google Gemini capabilities.
