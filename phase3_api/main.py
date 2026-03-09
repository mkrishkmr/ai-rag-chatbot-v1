import os
from typing import List
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

from phase1_ingestion.orchestrator import compile_fact_sheets
from phase2_rag.chroma_db import ingest_fact_sheet
from phase2_rag.retriever import retrieve_hybrid_context
from phase3_api.guardrails import detect_pii, get_system_prompt

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
    query: str
    history: List[ChatMessage] = []

@app.post("/api/sync")
async def trigger_sync():
    """Triggers the Playwright scraper and PDF parser, then ingests into Chroma. (Warning: Slow)"""
    try:
        await compile_fact_sheets()
        ingest_fact_sheet()
        return {"status": "success", "message": "Synced Groww Web & PDF data to ChromaDB."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/chat")
async def chat_endpoint(req: ChatRequest):
    if detect_pii(req.query):
        raise HTTPException(status_code=403, detail="PII Detected. Request blocked.")
    
    try:
        docs = retrieve_hybrid_context(req.query)
        context_str = "\n".join([f"Source: {d.metadata.get('source_url')}\nType: {d.metadata.get('document_type')}\nContent: {d.page_content}" for d in docs])
        
        system_prompt = get_system_prompt(context_str)
        
        # Build standard Langchain Groq chat payload
        from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
        from langchain_groq import ChatGroq
        
        messages = [SystemMessage(content=system_prompt)]
        for msg in req.history:
            if msg.role == "user":
                messages.append(HumanMessage(content=msg.content))
            else:
                messages.append(AIMessage(content=msg.content))
        messages.append(HumanMessage(content=req.query))
        
        chat = ChatGroq(model="llama-3.1-8b-instant", temperature=0, streaming=True)
        
        async def response_stream():
            async for chunk in chat.astream(messages):
                if chunk.content:
                    yield chunk.content
                    
        return StreamingResponse(response_stream(), media_type="text/event-stream")
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8080))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
