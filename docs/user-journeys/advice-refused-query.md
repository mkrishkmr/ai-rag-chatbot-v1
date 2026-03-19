# User Journey: Advice Refused Query

This journey outlines how the Fact Engine prevents liability and maintains its strict compliance guidelines by refusing to answer advisory questions.

## Scenario
A user attempts to ask the model to evaluate a fund's potential future value or recommend a purchase.

**User Input:**
> *"Is the Groww ELSS Tax Saver a good investment right now? Should I buy?"*

## Flow Execution

1. **Frontend Request**
   The Next.js client posts the query.

2. **Backend Guardrails (Advice Check)**
   - **PII Check**: Clean, returns False.
   - **Scope Check**: The term "elss tax saver" exists. Returns True.
   - **Advice Check**: The query contains the protected substring "should i buy" and "good investment". `is_advice_query(query)` returns True.

3. **Short-Circuit Refusal**
   Instead of pulling data from ChromaDB or passing the query to Groq, the FastAPI handler intercepts the execution loop. It constructs an immediate refusal based on a hardcoded string.
   
4. **Mock SSE Stream**
   To keep the frontend UX consistent, the backend streams the hardcoded reply exactly as if it were an LLM generation:
   ```json
   {"answer": "I can provide facts only, not investment advice. For help evaluating mutual funds, visit [AMFI Investor Education] (https://www.amfiindia.com/investor-corner/knowledge-center)."}
   {"sources": [], "response_type": "refusal", "gate_blocked": "advice_query"}
   ```

5. **Frontend Display**
   The frontend renders the standard reply. Because `msg.response_type === "refusal"`, the frontend suppresses any UI attempts to render citation cards (since `msg.sources` is an empty array).
