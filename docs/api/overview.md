# API Overview

The Groww AI Fact Engine exposes a single REST endpoint over HTTP that accepts JSON payloads and returns Server-Sent Events (SSE).

## Base URL

- **Development**: `http://localhost:8080/api`
- **Production**: `https://<render-deployment-url>.onrender.com/api`

## Authentication

This API is strictly **public**. It does not enforce any standard Bearer tokens, OAuth2 flows, or third-party authentication. Security is handled exclusively via robust parameter validation and application-layer guardrails.

## Common Headers

- `Content-Type: application/json` is required for the request.
- The endpoint will respond with `Content-Type: text/event-stream`.

## Endpoints

- [`POST /chat`](endpoints/chat.md): The main RAG interaction endpoint.
- [`GET /health`](#): Useful for readiness probes (returns `{status: 'ok'}`).
