# User Journey: Factual Metric Query

This journey details the lifecycle of a valid factual query traversing the Groww AI Fact Engine.

## Scenario
A user asks the frontend for the specific Net Asset Value of a mutual fund using its short name.

**User Input:** 
> *"What is the NAV of Nifty 50?"*

## Flow Execution

1. **Frontend Request**
   The Next.js client posts the query:
   ```json
   { "question": "What is the NAV of Nifty 50?", "history": [] }
   ```

2. **Backend Guardrails**
   - **PII Check**: `pan_pattern` and `aadhaar_pattern` yield False.
   - **Scope Check**: "nifty 50" matches a known `_SCOPE_KEYWORD`. Returns True.
   - **Advice Check**: No advisory phrases detected ("predict", "should i"). Returns False.

3. **Query Expansion**
   The backend applies a fast substring replacement:
   "nifty 50" is upgraded to "Groww Nifty 50 Index Fund Direct Growth" in the query string. This ensures ChromaDB perfectly matches the dense chunks which all include the official name.

4. **Document Retrieval (Hybrid RAG)**
   The backend queries ChromaDB.
   - **Keyword Trigger**: The query contains the word "nav". This matches the web-priority routing.
   - **Reranking**: The retriever returns `k=12` chunks and forces chunks with `doc_type: "Web"` to the top of the array, ensuring the live NAV figure (not a static PDF boilerplate) forms the core context.

5. **LLM Generation & SSE Stream**
   The backend invokes Groq holding the system prompt instructions against the retrieved chunks.
   - As `llama-3.1-8b-instant` predicts tokens, the FastAPI generator yields them.
   - **Rule Application**: The LLM outputs "The Net Asset Value is ₹9.49" and intentionally avoids placing a URL in the text due to `RULE 14`.
   
6. **Frontend Display**
   The Next.js client rapidly renders the tokens as they arrive. Upon receiving the final metadata JSON block containing the sources, it runs a deduplicator function (matching URLs and Fund names) and renders the verified source citation link below the chat bubble.
