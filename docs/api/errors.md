# Errors & Guardrails

The Fact Engine API handles errors and out-of-bounds queries through HTTP status codes and strict JSON schema responses.

## HTTP 400 Bad Request (PII Block)

If the user includes a pattern matching a PAN card or an Aadhaar number, the API immediately throws an HTTP 400 error. The request never reaches the database or the LLM.

**Example Request:**
```json
{
  "question": "My PAN is ABCDE1234F, can I invest?"
}
```

**Example Response (Status 400):**
```json
{
  "detail": "PII Detected. Request blocked."
}
```

## SSE Stream Refusals

If the query passes the PII check but violates other functional strictures, the API returns a 200 OK along with an execution stream that represents a refusal rather than an LLM generation. 

### 1. Out of Scope

If the query does not contain keywords relating to the 4 covered Groww funds, the API yields a hardcoded refusal.

**Example Request:**
```json
{
  "question": "What is the weather in Bangalore today?"
}
```

**Example Stream:**
```json
{"answer": "I only have information about Groww Nifty 50 Index Fund, Groww Value Fund, Groww Aggressive Hybrid Fund, and Groww ELSS Tax Saver Fund."}
{"sources": [], "response_type": "refusal", "gate_blocked": "out_of_scope"}
```

### 2. Advice Refusal

If the query asks for investment predictions, recommendations, or comparisons, the API yields a hardcoded refusal.

**Example Request:**
```json
{
  "question": "Should I invest my bonus in the Value Fund?"
}
```

**Example Stream:**
```json
{"answer": "I can provide facts only, not investment advice. For help evaluating mutual funds, visit [AMFI Investor Education] (https://www.amfiindia.com/investor-corner/knowledge-center)."}
{"sources": [], "response_type": "refusal", "gate_blocked": "advice_query"}
```
