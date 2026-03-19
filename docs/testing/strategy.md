# Testing Strategy

The Groww AI Fact Engine relies on automated integration testing built around `curl` requests specifically targeted at the `/api/chat` unified endpoint.

## Principles
- **End-to-End Blackbox Testing**: Validates the true final output returned by the SSE generator.
- **RAG Integrity**: Validates that LLM generations remain constrained to correct specific context bounds without hallucination.
- **Guardrail Priority**: Validates that `is_query_in_scope`, `is_advice_query`, and `detect_pii` fire perfectly before any costly retrieval or generation operations occur.

## Environments
Tests are executed manually against the local FastAPI test server running on `http://localhost:8080`.

## Scope Definitions
When tests refer to the "covered funds", they explicitly mean:
1. Groww Nifty 50 Index Fund Direct Growth
2. Groww Value Fund Direct Growth
3. Groww Aggressive Hybrid Fund Direct Growth
4. Groww ELSS Tax Saver Fund Direct Growth

See [test-cases.md](test-cases.md) for the actual scripts to run.
