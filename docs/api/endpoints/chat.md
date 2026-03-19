# POST /api/chat

This is the primary endpoint for interacting with the RAG pipeline. It accepts a user's question and an optional conversation history, processes it through multiple guardrails, executes context retrieval, and streams back an answer using SSE.

## Request

**Content-Type**: `application/json`

### Payload Schema

```json
{
  "question": "What is the NAV of Nifty 50?",
  "history": [
    {
      "role": "user",
      "content": "Tell me about Nifty 50"
    },
    {
      "role": "assistant",
      "content": "Groww Nifty 50 Index Fund Direct Growth is an equity mutual fund..."
    }
  ]
}
```

- `question` (string, required): The user's input string.
- `history` (array of objects, optional): Previous messages in the conversation to assist with pronoun resolution (e.g. interpreting "what is **its** NAV?").

## Response

**Content-Type**: `text/event-stream`

The response streams as Server-Sent Events containing JSON objects.

### Stream Schema

**1. Text Generation Stream**
While the LLM is generating, chunks are sent containing the `answer` token:
```json
{"answer": "The"}
{"answer": " Net"}
{"answer": " Asset"}
{"answer": " Value"}
{"answer": " ("}
{"answer": "NAV"}
{"answer": ")"}
{"answer": " is"}
{"answer": " \u20b9"}
{"answer": "9"}
{"answer": "."}
{"answer": "49"}
{"answer": "."}
```

**2. Final Metadata Chunk**
Once the LLM stops returning tokens, a final chunk containing sources and metadata is sent:
```json
{
  "sources": [
    {
      "source_url": "https://groww.in/mutual-funds/groww-nifty-50-index-fund-direct-growth",
      "fund_name": "Groww Nifty 50 Index Fund Direct Growth",
      "doc_type": "Web"
    }
  ],
  "response_type": "answer",
  "gate_blocked": null
}
```

### Response Variants

If the query is blocked by a guardrail, the system returns an immediate refusal and does not invoke the LLM. Read more about block conditions in [Errors & Guardrails](../errors.md).
