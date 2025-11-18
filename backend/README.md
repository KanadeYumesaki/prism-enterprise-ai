# Governance Kernel (backend)

This is a minimal FastAPI backend for the Multi-LLM Governance Kernel v0.1.

Quick start:

1. Create a virtual environment and activate it.
2. Install dependencies:

```powershell
cd backend; python -m venv .venv; .\.venv\Scripts\Activate.ps1; pip install -r requirements.txt
```

3. Run the app:

```powershell
uvicorn main:app --reload --port 8000
```

The API provides:
- `POST /chat` — chat endpoint
- `GET /policies` — currently loaded policies
- `GET /logs?limit=50` — recent logs

policies are in `policies.yaml`.
