# Contributing to Groww AI Fact Engine

We welcome contributions to the Groww AI Fact Engine. Please follow these guidelines to ensure a smooth development process.

## Local Development Setup

### Backend

1. Navigate to the project root.
2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Set up `.env` with require API keys:
   ```
   GOOGLE_API_KEY=your_gemini_api_key
   GROQ_API_KEY=your_groq_api_key
   ```
5. Run the FastAPI dev server:
   ```bash
   export PYTHONPATH=.
   uvicorn phase3_api.main:app --host 0.0.0.0 --port 8080 --reload
   ```

### Frontend

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```
2. Install dependencies:
   ```bash
   npm install
   ```
3. Set environment variables (e.g. `NEXT_PUBLIC_API_URL=http://localhost:8080`).
4. Run the development server:
   ```bash
   npm run dev
   ```

## Workflow

1. Create a feature branch off `main` (`git checkout -b feature/your-feature-name`).
2. Write clean, modular code following existing conventions.
3. If modifying RAG behavior, ensure you run the curl tests defined in `docs/testing/test-cases.md`.
4. Submit a Pull Request with a clear description of the changes.

## Code Constraints

- **Guardrails**: Modifications to `phase3_api/guardrails.py` must be extensively tested to prevent jailbreaks or hallucinations.
- **External Data**: Do not ingest external funds. The system is strictly scoped to the 4 approved Groww funds.
