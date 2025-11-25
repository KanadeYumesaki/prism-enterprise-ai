import time
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, Form, Response, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from starlette.concurrency import run_in_threadpool
from datetime import datetime
import json
import os
from typing import List

from dotenv import load_dotenv

from policy_store import load_policies
from logging_db import init_db, insert_log_entry, get_recent_logs_for_tenant
from governance_kernel import detect_domain, detect_pii, decide_mode, select_model
from policy_compiler import build_system_prompt
from providers import call_llm_stream
from models import ChatResponse, LoginRequest, Log
from file_parser import extract_text_from_file
from rag_kernel import HybridRetriever
from auth import create_access_token, get_current_context

load_dotenv()

BASE_DIR = Path(__file__).parent

app = FastAPI(title="Governance Kernel v0.1")

# [REFAC] CORS Update for Cookie Auth
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:4200", # Angular Dev Server (ng serve)
        "http://localhost",      # Docker Nginx (Port 80) ★これを追加
        "http://127.0.0.1"       # 念のため追加
    ], # Must be specific for allow_credentials=True
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global State
POLICIES = {}
RAG_ENGINE = None

@app.on_event("startup")
def startup_event():
    global POLICIES, RAG_ENGINE
    POLICIES = load_policies(BASE_DIR / "policies.yaml")
    init_db() # SQLModel init and seeding
    
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("WARNING: GEMINI_API_KEY not found. RAG will not work.")
        RAG_ENGINE = None
    else:
        RAG_ENGINE = HybridRetriever(api_key)

# --- Auth Endpoints ---

@app.post("/auth/mock-login")
def mock_login(request: LoginRequest, response: Response):
    """
    Mock Login: Generates a JWT for the given user_id and sets it in an HttpOnly cookie.
    In a real app, this would verify credentials.
    """
    # Create JWT
    access_token = create_access_token(data={"sub": request.user_id})
    
    # Set HttpOnly Cookie
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        max_age=60 * 60 * 24, # 1 day
        samesite="lax",
        secure=False, # Set to True in production with HTTPS
    )
    return {"status": "success", "user_id": request.user_id, "tenant_id": request.tenant_id}

@app.post("/auth/logout")
def logout(response: Response):
    response.delete_cookie("access_token")
    return {"status": "success"}

# --- Tenant Scoped Endpoints ---

@app.post("/tenants/{tenant_id}/chat")
async def chat_endpoint(
    tenant_id: str,
    message: str = Form(...),
    files: List[UploadFile] = File(default=[]),
    context: dict = Depends(get_current_context)
):
    user_id = context["user_id"]
    
    try:
        start = time.time()

        # Handle Files
        if files:
            file_contents = []
            for file in files:
                if file.filename:
                    content = await extract_text_from_file(file)
                    file_contents.append(f"Filename: {file.filename}\nContent:\n{content}")
            
            if file_contents:
                message += "\n\n[Attached Files]\n" + "\n---\n".join(file_contents)

        # Governance Logic
        domain = detect_domain(message)
        pii = detect_pii(message)
        mode = decide_mode(message, POLICIES, domain, pii)

        if files and mode == "FAST":
             mode = "HEAVY"

        model = select_model(mode, POLICIES)
        system_prompt = build_system_prompt(mode, POLICIES)

        async def stream_generator():
            nonlocal system_prompt
            full_reply = ""
            
            try:
                # 1. Status: Searching
                yield json.dumps({"type": "status", "content": "🔍 Searching Knowledge Base..."}) + "\n"

                if RAG_ENGINE:
                    # [REFAC] Pass tenant_id to RAG
                    context_docs = await run_in_threadpool(RAG_ENGINE.search, tenant_id, message, n_results=3)
                    if context_docs:
                        context_str = "\n\n".join(context_docs)
                        current_system_prompt = system_prompt + f"\n\n[Reference Information]\nUse the following information to answer the user's request if relevant:\n{context_str}\n"
                    else:
                        current_system_prompt = system_prompt
                else:
                    current_system_prompt = system_prompt

                # 2. Status: Generating
                yield json.dumps({"type": "status", "content": "🤖 Generating Response..."}) + "\n"

                # Streaming Call
                async for chunk in call_llm_stream(model, current_system_prompt, message):
                    full_reply += chunk
                    data = {"type": "chunk", "content": chunk}
                    yield json.dumps(data) + "\n"

                total_ms = int((time.time() - start) * 1000)

                # Log (Async / Non-blocking)
                # [REFAC] Use SQLModel Log object
                log_entry = Log(
                    timestamp=datetime.utcnow().isoformat() + "Z",
                    user_id=user_id,
                    tenant_id=tenant_id,
                    mode=mode,
                    model=model,
                    policy_version=POLICIES.get("version", "0.0"),
                    pii_mask_applied=pii.get("pii_detected", False),
                    safety_flags=pii.get("detected_types", []),
                    tools_used=[],
                    latency_ms=total_ms,
                    input_text=message,
                    output_text=full_reply
                )
                
                await run_in_threadpool(insert_log_entry, log_entry)

                # Complete Notification
                meta = {
                    "type": "complete",
                    "meta": {
                        "reply": full_reply,
                        "mode": mode,
                        "model": model,
                        "policy_version": POLICIES.get("version", "0.0"),
                        "safety_flags": ["pii"] if pii.get("pii_detected") else [],
                        "tools_used": [],
                        "latency_ms": total_ms
                    }
                }
                yield json.dumps(meta) + "\n"

            except Exception as e:
                error_data = {"type": "error", "content": f"An error occurred during generation: {str(e)}"}
                yield json.dumps(error_data) + "\n"
                print(f"Stream Error: {e}")

        return StreamingResponse(stream_generator(), media_type="application/x-ndjson")

    except Exception as e:
        print(f"Endpoint Error: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.get("/tenants/{tenant_id}/policies")
def get_policies(tenant_id: str, context: dict = Depends(get_current_context)):
    return POLICIES


@app.get("/tenants/{tenant_id}/logs")
def get_logs(tenant_id: str, limit: int = 50, context: dict = Depends(get_current_context)):
    # [REFAC] Filter by tenant_id
    return get_recent_logs_for_tenant(tenant_id, limit)


@app.post("/tenants/{tenant_id}/ingest")
async def ingest_document(
    tenant_id: str,
    file: UploadFile = File(...),
    context: dict = Depends(get_current_context)
):
    if not RAG_ENGINE:
        return {"error": "RAG Engine not initialized"}
    
    content = await extract_text_from_file(file)
    if not content:
        return {"error": "Could not extract text from file"}
        
    # [REFAC] Pass tenant_id
    doc_id = RAG_ENGINE.add_document(
        tenant_id,
        content,
        metadata={"filename": file.filename, "timestamp": datetime.utcnow().isoformat() + "Z", "uploader": context["user_id"]}
    )
    return {"status": "success", "doc_id": doc_id, "filename": file.filename}


@app.get("/tenants/{tenant_id}/knowledge")
def get_knowledge_base(tenant_id: str, context: dict = Depends(get_current_context)):
    if not RAG_ENGINE:
        return []
    # [REFAC] Pass tenant_id
    return RAG_ENGINE.list_documents(tenant_id)
