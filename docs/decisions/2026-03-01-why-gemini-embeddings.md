# Architecture Decision Record: Gemini Embeddings

## Context
To load our 1644 chunks of Groww mutual fund data into ChromaDB, the raw text needed to be converted into multidimensional floating-point arrays (vectors) that reliably score dense similarities during a user's `POST /api/chat` request.

## Alternatives Considered
- **OpenAI `text-embedding-3-small`**: Very popular, cost-effective.
- **HuggingFace `all-MiniLM-L6-v2`**: Local, free.
- **Google Gemini `gemini-embedding-001`**: Modern dense embedding model from Google.

## Decision
We selected **Google Gemini `gemini-embedding-001`**.

## Justification
- **Semantic Nuance**: Financial metrics and phrases (e.g. "Net Asset Value", "Exit Load") require a model with deep semantic context. Gemini's embeddings show superior out-of-the-box cluster differentiation for FinTech terms.
- **Ecosystem Integration**: The `@langchain/google-genai` package offered a direct, seamless method for passing chunks through the API and straight into the local Chroma instance.
