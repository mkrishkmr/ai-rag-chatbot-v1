from phase3_api.main import app
from fastapi.testclient import TestClient
client = TestClient(app)
try:
    with client.stream("POST", "/api/chat", json={"query": "Show me the fund manager for Groww Value Fund", "history": []}) as response:
        for line in response.iter_lines():
            print(line)
except Exception as e:
    print(f"FAILED: {e}")
