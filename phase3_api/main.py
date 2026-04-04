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
from phase2_rag.chroma_db import get_vector_store
from phase3_api.guardrails import detect_pii, get_system_prompt, is_query_in_scope, is_advice_query

class _DummyRetriever:
    def get_relevant_documents(self, query, fund_slug=None):
        return retrieve_hybrid_context(query, fund_slug=fund_slug)

def build_retriever():
    return _DummyRetriever()

# Load live metrics once at startup
LIVE_METRICS_PATH = "phase3_api/live_metrics.json"
live_metrics_data = {}
if os.path.exists(LIVE_METRICS_PATH):
    try:
        with open(LIVE_METRICS_PATH, "r") as f:
            live_metrics_data = json.load(f)
    except Exception as e:
        print(f"⚠️ Failed to load live metrics: {e}")

def get_fund_slug(query: str) -> str:
    """Detects which fund the user is asking about to enable metadata filtering."""
    q = query.lower()
    if any(k in q for k in ["nifty 50", "nifty50", "index"]): return "nifty50_index"
    if "value" in q: return "value_fund"
    if "hybrid" in q: return "aggressive_hybrid"
    if "elss" in q or "tax saver" in q: return "elss_tax_saver"
    return None

def log_trace(query: str, standalone: str, fund_slug: str, docs: list, answer: str):
    """Logs the RAG trace to a local JSONL file for observability."""
    from datetime import datetime
    trace = {
        "timestamp": datetime.now().isoformat(),
        "query": query,
        "standalone_query": standalone,
        "detected_fund": fund_slug,
        "retrieved_sources": [d.metadata.get("source_url") for d in docs],
        "answer": answer
    }
    try:
        with open("traces.jsonl", "a") as f:
            f.write(json.dumps(trace) + "\n")
    except Exception as e:
        print(f"⚠️ Failed to log trace: {e}")

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY environment variable is not set")
if not GOOGLE_API_KEY:
    raise ValueError("GOOGLE_API_KEY environment variable is not set")

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

@app.get("/api/kb")
def get_knowledge_base():
    try:
        store = get_vector_store()
        collection = store._collection
        results = collection.get(include=["metadatas"])
        metadatas = results.get("metadatas", [])
        
        kb_tree = {}
        for md in metadatas:
            if not md: continue
            fund_name = md.get("fund_name")
            doc_type = md.get("document_type") or md.get("doc_type")
            if fund_name and doc_type:
                fn = fund_name.replace("Groww ", "").replace(" Direct Growth", "").strip()
                dt = "Live Data" if doc_type.lower() == "web" else doc_type
                if fn not in kb_tree:
                    kb_tree[fn] = set()
                kb_tree[fn].add(dt)
        return {k: list(v) for k, v in kb_tree.items()}
    except Exception as e:
        return {
            "Nifty 50 Index Fund": ["Live Data", "SID", "KIM"],
            "Value Fund": ["Live Data", "SID", "KIM"],
            "Aggressive Hybrid Fund": ["Live Data", "SID", "KIM"],
            "ELSS Tax Saver Fund": ["Live Data", "SID", "KIM"]
        }

def condense_query(query: str, history: List[ChatMessage]) -> str:
    """
    Rewrites the user's latest query into a standalone question based 
    on the chat history.
    """
    if not history:
        return query
        
    history_str = "\n".join([f"{m.role}: {m.content}" for m in history])
    
    prompt = f"""Given the following conversation and a follow-up question, rephrase the follow-up question to be a standalone question. 
It MUST be specific about the mutual fund name if mentioned in the history.
DO NOT add any conversational filler. Just the standalone question.

Conversation History:
{history_str}

Follow-up Question: {query}

Standalone Question:"""

    try:
        from langchain_groq import ChatGroq
        condenser = ChatGroq(model="llama-3.1-8b-instant", temperature=0)
        response = condenser.invoke(prompt)
        standalone = response.content.strip()
        return standalone if standalone else query
    except Exception:
        return query

@app.post("/api/chat")
async def chat_endpoint(req: ChatRequest):
    query = (req.query or req.question).strip()
    standalone_query = condense_query(query, req.history)
    fund_slug = get_fund_slug(standalone_query)
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
    
    # GATE 4 — Zero-retrieval check using CONDENSED query
    try:
        docs = build_retriever().get_relevant_documents(standalone_query, fund_slug=fund_slug)
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
        unique_docs = []
        seen_pairs = set()
        for d in docs:
            # Pydantic 2.x Guard: Final safety check for None contents
            if not d or not isinstance(d.page_content, str):
                continue
            pair = (d.metadata.get("source"), d.metadata.get("fund_name"))
            if pair not in seen_pairs:
                unique_docs.append(d)
                seen_pairs.add(pair)
        docs = unique_docs

        context_str = "\n".join([f"Source: {d.metadata.get('source_url') or None}\nType: {d.metadata.get('document_type')}\nContent: {d.page_content}" for d in docs])
        
        # Inject live metrics for the specific fund if detected
        live_context = "No specific live metrics for this query."
        if fund_slug and fund_slug in live_metrics_data:
            m = live_metrics_data[fund_slug]
            live_context = f"Fund: {m['fund_name']}\nNAV: {m['nav']} (as of {m['nav_date']})\nFund Size: {m['fund_size_cr']} Cr\nExpense Ratio: {m['expense_ratio_pct']}%"
        
        system_prompt = get_system_prompt(context_str, live_metrics=live_context)
        
        from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
        from langchain_google_genai import ChatGoogleGenerativeAI
        
        # Injected BEFORE instructions as requested for better priority
        messages = []
        for msg in req.history:
            if msg.role == "user":
                messages.append(HumanMessage(content=msg.content))
            else:
                messages.append(AIMessage(content=msg.content))
        
        messages.append(SystemMessage(content=system_prompt))
        messages.append(HumanMessage(content=query))
        
        # Switched to Flash for cost-effectiveness and speed
        chat = ChatGoogleGenerativeAI(model="gemini-3-flash-preview", temperature=0, streaming=True)
        
        async def response_stream():
            accumulated_text = ""
            is_refusal = False
            
            yielded_length = 0
            
            async for chunk in chat.astream(messages):
                if chunk.content:
                    accumulated_text += chunk.content
                    
                    # Advice refusal detection
                    if "not investment advice" in accumulated_text.lower() and not is_refusal:
                        is_refusal = True
                    
                    # STRICT TAG CHECK: If [ANSWER] is missing, do not leak raw preamble text.
                    start_idx = accumulated_text.find("[ANSWER]")
                    if start_idx != -1:
                        start_idx += len("[ANSWER]")
                    else:
                        # If still potentially waiting for tag, hold back
                        if len(accumulated_text) < 50:
                            continue
                        # If tag is definitely missing after 50 chars, default to index 0 
                        # but we prioritize forcing the model to fix this.
                        start_idx = 0
                        
                    end_idx = accumulated_text.find("[/ANSWER]", start_idx)
                    if end_idx == -1:
                        end_idx = accumulated_text.find("[SOURCE_SUMMARIES]", start_idx)
                    if end_idx == -1:
                        end_idx = len(accumulated_text)
                        
                    # Hold back partial tokens to prevent leaking unclosed brackets
                    last_bracket = accumulated_text.rfind("[", start_idx, end_idx)
                    if last_bracket != -1 and accumulated_text.find("]", last_bracket) == -1:
                        end_idx = last_bracket
                            
                    answer_text = accumulated_text[start_idx:end_idx].replace("[ANSWER]", "").replace("[SOURCE_SUMMARIES]", "").replace("[NEXT_STEPS]", "").lstrip()
                    new_text = answer_text[yielded_length:]
                    if new_text:
                        yield json.dumps({"answer": new_text}) + "\n"
                        yielded_length += len(new_text)

            # At the end of the stream, extract exact buffers using regex
            import re
            answer_buffer = ""
            summaries_buffer = ""
            next_steps_buffer = ""
            
            ans_match = re.search(r"\[ANSWER\](.*?)\[/ANSWER\]", accumulated_text, re.DOTALL)
            if ans_match: 
                answer_buffer = ans_match.group(1).strip()
            
            sum_match = re.search(r"\[SOURCE_SUMMARIES\](.*?)\[/SOURCE_SUMMARIES\]", accumulated_text, re.DOTALL)
            if sum_match: 
                summaries_buffer = sum_match.group(1).strip()
            
            next_match = re.search(r"\[NEXT_STEPS\](.*?)\[/NEXT_STEPS\]", accumulated_text, re.DOTALL)
            if next_match: 
                next_steps_buffer = next_match.group(1).strip()

            # Handle the case where tags are completely missing or broken
            if not answer_buffer and accumulated_text:
                # Use a clean version of the text if no tags were matched
                clean_output = re.sub(r"\[/?(ANSWER|SOURCE_SUMMARIES|NEXT_STEPS)\]", "", accumulated_text).strip()
                answer_buffer = clean_output
                # If we didn't stream yet, yield the entire clean text now
                if yielded_length == 0:
                    yield json.dumps({"answer": answer_buffer}) + "\n"

            # Parse buffers into lists
            def parse_list(text):
                return [line.strip("- ").strip() for line in text.strip().split("\n") if line.strip()]

            final_summaries = parse_list(summaries_buffer)
            final_next_steps = parse_list(next_steps_buffer)
            
            # Map summaries back to sources
            seen = set()
            unique_sources = []
            if not is_refusal:
                # We'll use the LLM-generated summaries to enrich the source list
                # If LLM gave 2 summaries and we have 2 docs, we pair them.
                for i, d in enumerate(docs):
                    url = d.metadata.get("source_url") or None
                    if url:
                        key = (url, d.metadata.get("fund_name"))
                        if key not in seen:
                            seen.add(key)
                            summary = final_summaries[len(unique_sources)] if len(unique_sources) < len(final_summaries) else ""
                            unique_sources.append({
                                "source_url": url,
                                "fund_name": d.metadata.get("fund_name"),
                                "doc_type": d.metadata.get("document_type"),
                                "snippet": summary or (d.page_content[:150] + "...")
                            })
            
            # Log trace to disk
            log_trace(query, standalone_query, fund_slug, docs, answer_buffer)
            
            yield json.dumps({
                "sources": [] if is_refusal else unique_sources[:3],
                "follow_ups": [] if is_refusal else final_next_steps[:3],
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
