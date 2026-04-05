import os
from phase3_api.main import app
from fastapi.testclient import TestClient

client = TestClient(app)
try:
    response = client.post("/api/chat", json={
        "query": "Show me the fund manager for Groww Value Fund.",
        "history": []
    })
    print(response.status_code)
    print(response.text)
except Exception as e:
    import traceback
    traceback.print_exc()
