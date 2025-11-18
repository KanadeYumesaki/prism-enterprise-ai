"""Simple smoke runner to exercise the /chat endpoint using TestClient."""
from fastapi.testclient import TestClient
from main import app


def run_smoke():
    client = TestClient(app)
    payload = {"user_id": "tester", "message": "これはテストです。株価について教えてください。"}
    resp = client.post("/chat", json=payload)
    print("status_code:", resp.status_code)
    print(resp.json())


if __name__ == "__main__":
    run_smoke()
