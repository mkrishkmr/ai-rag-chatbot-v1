# User Journey: PII Blocked Query

This journey demonstrates the system's hard restriction on Personal Identifiable Information (PII) to ensure compliance and data safety. Neither the user's data nor the query ever leaves the FastAPI server boundaries.

## Scenario
A user inadvertently inputs their Permanent Account Number (PAN) while asking a question about their ability to invest.

**User Input:**
> *"My PAN is ABCDE1234F, can I invest in the Value Fund?"*

## Flow Execution

1. **Frontend Request**
   The Next.js client posts the payload:
   ```json
   { "question": "My PAN is ABCDE1234F, can I invest in the Value Fund?" }
   ```

2. **Backend Guardrails (PII Check)**
   - The query hits `guardrails.py -> detect_pii(text)`.
   - The Regex pattern `r'\b[A-Z]{5}[0-9]{4}[A-Z]{1}\b'` scans the `query.text`.
   - The pattern matches "ABCDE1234F".
   - The function returns `True`.

3. **Immediate Backend Response**
   - The FastAPI endpoint triggers an immediate `HTTPException` with a status code of 400.
   - It responds with `{"detail": "PII Detected. Request blocked."}`.

4. **Frontend Display**
   - The Next.js frontend intercepts the 400 response.
   - It falls into a `catch` or `error` state.
   - A red error bubble/toast is displayed to the user indicating their input has been rejected.

## Security Considerations
- Because the restriction triggers at the top level of the `POST` interface, the PII string is completely isolated.
- It is never embedded, never stored in history, and never sent remotely to Groq or any other third-party API.
