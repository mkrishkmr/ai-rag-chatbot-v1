import json
from phase3_api.main import app
from fastapi.testclient import TestClient

client = TestClient(app)
print("Testing Chat...")
resp = client.post("/api/chat", json={
    "query": "Show me the fund manager for Groww Value Fund",
    "history": []
})
print(f"Status: {resp.status_code}")
print(f"Response: {resp.text}")
