# Architecture Decision Record: ChromaDB

## Context
The Groww AI Fact Engine requires a vector database to store and semantically retrieve context chunks regarding 4 specific mutual funds (1644 pre-processed chunks).

## Alternatives Considered
- **Pinecone**: Cloud-based, managed.
- **Qdrant**: High performance, rust-based.
- **ChromaDB**: Lightweight, local-file persistent, highly integrated with LangChain.

## Decision
We selected **ChromaDB**.

## Justification
- **Simplicity**: ChromaDB operates perfectly as an embedded database within Python, serializing directly to the `/chroma_db` folder.
- **Portability**: Since our document pool is currently static (ingested once via Playwright/PyMuPDF scripts), we can effortlessly commit or deploy the pre-built `chroma_db` folder to the Render instance without requiring external database provisioning.
- **Cost**: 100% free with no latency introduced via external HTTP calls.
