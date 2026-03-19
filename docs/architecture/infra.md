# Infrastructure & Deployment

The platform relies on managed cloud services to host the separated frontend and backend.

## Frontend (Vercel)
- The Next.js 14 frontend is deployed as a serverless application on Vercel.
- Vercel automatically handles edge caching, static asset delivery, and SSL.
- **Environment Variables**:
  - `NEXT_PUBLIC_API_URL`: Points to the Render backend URL (e.g., `https://groww-ai-api.render.com`).

## Backend (Render)
- The FastAPI application is deployed as a Web Service on Render.
- Uses `uvicorn` as the ASGI production web server.
- The persistent `chroma_db` directory must be included in the deployment artifact (or mounted as a Persistent Disk if updates are frequent). Since the app doesn't re-ingest in production, deploying the pre-baked `chroma_db` directory is standard.
- **Environment Variables**:
  - `GOOGLE_API_KEY`: Secrets for embeddings.
  - `GROQ_API_KEY`: Secrets for query completion.

## External Dependencies
- **Groq API**: Used for production LLM invocations because of its ultra-low latency LPU inference, which makes streaming generation practically instant.
- **Google Generative AI**: Used natively for embeddings.
