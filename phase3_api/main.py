import os
import json
from typing import List
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

from phase1_ingestion.run_ingestion import compile_fact_sheets
from phase2_rag.ingest import ingest_fact_sheet
from phase2_rag.retriever import retrieve_hybrid_context
from phase3_api.guardrails import detect_pii, get_system_prompt, is_query_in_scope, is_advice_query

class _DummyRetriever:
    def get_relevant_documents(self, query):
        return retrieve_hybrid_context(query)

def build_retriever():
    return _DummyRetriever()

load_dotenv()

app = FastAPI(
    title="Groww Facts API",
    description="Factual RAG for Groww Mutual Funds with Guardrails."
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatMessage(BaseModel):
    role: str
    content: str
    
class ChatRequest(BaseModel):
    query: str = ""
    question: str = ""  # For compatibility
    history: List[ChatMessage] = []

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.post("/api/sync")
async def trigger_sync():
    """Triggers the Playwright scraper and PDF parser, then ingests into Chroma. (Warning: Slow)"""
    try:
        await compile_fact_sheets()
        ingest_fact_sheet()
        return {"status": "success", "message": "Synced Groww Web & PDF data to ChromaDB."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def resolve_pronouns(query: str, history: List[ChatMessage]) -> str:
    """
    If query contains pronouns and no specific fund name, resolve them 
    using the last mention in history.
    """
    PRONOUNS = ["it", "the fund", "this fund", "that fund", "its"]
    FUNDS = [
        "Groww Nifty 50 Index Fund", 
        "Groww Value Fund", 
        "Groww Aggressive Hybrid Fund", 
        "Groww ELSS Tax Saver Fund"
    ]
    
    q_lower = query.lower()
    has_pronoun = any(p in q_lower for p in PRONOUNS)
    has_fund = any(f.lower() in q_lower for f in FUNDS)
    
    if has_pronoun and not has_fund:
        # Scan history backwards for a fund name
        for msg in reversed(history):
            for fund in FUNDS:
                if fund.lower() in msg.content.lower():
                    # Rewrite query with the fund name
                    return f"{query} (specifically for {fund} Direct Growth)"
    
    return query

def expand_fund_name(query: str) -> str:
    replacements = {
        "nifty 50 index fund": "Groww Nifty 50 Index Fund Direct Growth",
        "nifty 50": "Groww Nifty 50 Index Fund Direct Growth",
        "value fund": "Groww Value Fund Direct Growth",
        "aggressive hybrid fund": "Groww Aggressive Hybrid Fund Direct Growth",
        "aggressive hybrid": "Groww Aggressive Hybrid Fund Direct Growth",
        "elss tax saver fund": "Groww ELSS Tax Saver Fund Direct Growth",
        "elss fund": "Groww ELSS Tax Saver Fund Direct Growth",
        "tax saver": "Groww ELSS Tax Saver Fund Direct Growth",
        "elss": "Groww ELSS Tax Saver Fund Direct Growth",
    }
    query_lower = query.lower()
    for short, full in replacements.items():
        if short in query_lower:
            query = query_lower.replace(short, full)
            break
    return query

@app.post("/api/chat")
async def chat_endpoint(req: ChatRequest):
    raw_query = (req.query or req.question).strip()
    query = resolve_pronouns(raw_query, req.history)
    query = expand_fund_name(query)
    if not query or len(query) < 3:
        return StreamingResponse(
            iter([json.dumps({
                "answer": "Please enter a valid question.",
                "sources": [],
                "gate_blocked": "empty_query"
            }) + "\n"]),
            media_type="text/event-stream"
        )
        
    if detect_pii(query):
        raise HTTPException(status_code=400, detail="PII Detected. Request blocked.")

    # GATE 3B — Advice query check (Prioritize advice refusal over scope)
    if is_advice_query(query):
        return StreamingResponse(
            iter([json.dumps({
                "answer": "I can provide facts only, not investment advice. For help evaluating mutual funds, visit [AMFI Investor Education] (https://www.amfiindia.com/investor-corner/knowledge-center).",
                "sources": [],
                "response_type": "refusal",
                "gate_blocked": "advice_query"
            }) + "\n"]),
            media_type="text/event-stream"
        )

    # GATE 3 — Scope check
    if not is_query_in_scope(query):
        return StreamingResponse(
            iter([json.dumps({
                "answer": "I only have information about Groww Nifty 50 Index Fund, Groww Value Fund, Groww Aggressive Hybrid Fund, and Groww ELSS Tax Saver Fund.",
                "sources": [],
                "response_type": "refusal",
                "gate_blocked": "out_of_scope"
            }) + "\n"]),
            media_type="text/event-stream"
        )
    
    # GATE 4 — Zero-retrieval check
    try:
        docs = build_retriever().get_relevant_documents(query)
        if not docs:
            return StreamingResponse(
                iter([json.dumps({
                    "answer": "I don't have that information in my knowledge base. Try asking about NAV, expense ratio, or holdings of Groww funds.",
                    "sources": [],
                    "response_type": "refusal",
                    "gate_blocked": "zero_retrieval"
                }) + "\n"]),
                media_type="text/event-stream"
            )

        # BUG 2 FIX: Deduplicate retrieved docs by (source, fund_name) metadata tuple
        # Keep only the first occurrence of each unique (source, fund_name) pair
        unique_docs = []
        seen_pairs = set()
        for d in docs:
            pair = (d.metadata.get("source"), d.metadata.get("fund_name"))
            if pair not in seen_pairs:
                unique_docs.append(d)
                seen_pairs.add(pair)
        docs = unique_docs

        context_str = "\n".join([f"Source: {d.metadata.get('source_url') or None}\nType: {d.metadata.get('document_type')}\nContent: {d.page_content}" for d in docs])
        
        system_prompt = get_system_prompt(context_str)
        
        from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
        from langchain_groq import ChatGroq
        
        # Injected BEFORE instructions as requested for better priority
        messages = []
        for msg in req.history:
            if msg.role == "user":
                messages.append(HumanMessage(content=msg.content))
            else:
                messages.append(AIMessage(content=msg.content))
        
        messages.append(SystemMessage(content=system_prompt))
        messages.append(HumanMessage(content=query))
        
        chat = ChatGroq(model="llama-3.1-8b-instant", temperature=0, streaming=True)
        
        async def response_stream():
            accumulated_text = ""
            is_refusal = False
            async for chunk in chat.astream(messages):
                if chunk.content:
                    accumulated_text += chunk.content
                    # Rule 4 prefix detection - use a shorter more robust substring
                    if "not investment advice" in accumulated_text and not is_refusal:
                        is_refusal = True
                    yield json.dumps({"answer": chunk.content}) + "\n"
                    
            seen = set()
            unique_sources = []
            if not is_refusal:
                for d in docs:
                    url = d.metadata.get("source_url") or None
                    if url:
                        key = (url, d.metadata.get("fund_name"))
                        if key not in seen:
                            seen.add(key)
                            unique_sources.append({
                                "source_url": url,
                                "fund_name": d.metadata.get("fund_name"),
                                "doc_type": d.metadata.get("document_type")
                            })
            sources_to_return = unique_sources
            
            yield json.dumps({
                "sources": [] if is_refusal else sources_to_return[:3],
                "response_type": "refusal" if is_refusal else "answer",
                "gate_blocked": "advice_query" if is_refusal else None
            }) + "\n"
                    
        return StreamingResponse(response_stream(), media_type="text/event-stream")
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8080))
    # Use the app object directly to avoid import issues
    uvicorn.run(app, host="0.0.0.0", port=port)
