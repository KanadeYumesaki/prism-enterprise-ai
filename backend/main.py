import time
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from starlette.concurrency import run_in_threadpool
from datetime import datetime
import json

from policy_store import load_policies
from logging_db import init_db, insert_log, get_recent_logs
from governance_kernel import detect_domain, detect_pii, decide_mode, select_model
from policy_compiler import build_system_prompt
from providers import call_llm, call_llm_stream
from models import ChatRequest, ChatResponse
from file_parser import extract_text_from_file
from rag_kernel import HybridRetriever
import os
from dotenv import load_dotenv

load_dotenv()


BASE_DIR = Path(__file__).parent

app = FastAPI(title="Governance Kernel v0.1")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup_event():
    # Load policies
    global POLICIES, RAG_ENGINE
    POLICIES = load_policies(BASE_DIR / "policies.yaml")
    init_db()
    
    # Initialize RAG Engine
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("WARNING: GEMINI_API_KEY not found. RAG will not work.")
        RAG_ENGINE = None
    else:
        RAG_ENGINE = HybridRetriever(api_key)


from typing import List

@app.post("/chat")
async def chat_endpoint(
    user_id: str = Form(...),
    message: str = Form(...),
    files: List[UploadFile] = File(default=[])
):
    try:
        start = time.time()

        # [NEW CODE] 複数ファイルの処理
        if files:
            file_contents = []
            for file in files:
                if file.filename:
                    content = await extract_text_from_file(file)
                    file_contents.append(f"Filename: {file.filename}\nContent:\n{content}")
            
            if file_contents:
                message += "\n\n[Attached Files]\n" + "\n---\n".join(file_contents)

        domain = detect_domain(message)
        pii = detect_pii(message)
        mode = decide_mode(message, POLICIES, domain, pii)

        if files and mode == "FAST":
             mode = "HEAVY"

        model = select_model(mode, POLICIES)
        system_prompt = build_system_prompt(mode, POLICIES)

        # [MOVED] RAG Context Injection logic is now inside stream_generator

        async def stream_generator():
            nonlocal system_prompt
            full_reply = ""
            
            try:
                # 1. Status: Searching
                yield json.dumps({"type": "status", "content": "🔍 Searching Knowledge Base..."}) + "\n"

                if RAG_ENGINE:
                    # Search for relevant documents in a thread pool
                    context_docs = await run_in_threadpool(RAG_ENGINE.search, message, n_results=3)
                    if context_docs:
                        context_str = "\n\n".join(context_docs)
                        current_system_prompt = system_prompt + f"\n\n[Reference Information]\nUse the following information to answer the user's request if relevant:\n{context_str}\n"
                    else:
                        current_system_prompt = system_prompt
                else:
                    current_system_prompt = system_prompt

                # 2. Status: Generating
                yield json.dumps({"type": "status", "content": "🤖 Generating Response..."}) + "\n"

                # ストリーミング呼び出し
                async for chunk in call_llm_stream(model, current_system_prompt, message):
                    full_reply += chunk
                    # NDJSON: {"type": "chunk", "content": "..."}
                    data = {"type": "chunk", "content": chunk}
                    yield json.dumps(data) + "\n"

                total_ms = int((time.time() - start) * 1000)

                # Log (Async / Non-blocking)
                # run_in_threadpool を使ってメインスレッドをブロックせずにDB保存を行う
                await run_in_threadpool(
                    insert_log,
                    timestamp=datetime.utcnow().isoformat() + "Z",
                    user_id=user_id,
                    mode=mode,
                    model=model,
                    policy_version=POLICIES.get("version", "0.0"),
                    pii_mask_applied=pii.get("pii_detected", False),
                    safety_flags={"detected_types": pii.get("detected_types", [])},
                    tools_used=[],
                    latency_ms=total_ms,
                    input_text=message,
                    output_text=full_reply
                )

                # 完了通知とメタデータ
                meta = {
                    "type": "complete",
                    "meta": {
                        "reply": full_reply, # 念のため全体も送る
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
                # ストリーミング中のエラーハンドリング
                error_data = {"type": "error", "content": f"An error occurred during generation: {str(e)}"}
                yield json.dumps(error_data) + "\n"
                # エラー時もログを残す（オプション）
                print(f"Stream Error: {e}")

        return StreamingResponse(stream_generator(), media_type="application/x-ndjson")

    except Exception as e:
        # エンドポイント初期化時のエラーハンドリング
        print(f"Endpoint Error: {e}")
        # ストリーミング開始前のエラーなので、通常のJSONレスポンスを返すか、
        # クライアントがNDJSONを期待している場合はそれに合わせる
        # ここでは簡易的にJSONエラーを返す
        from fastapi.responses import JSONResponse
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.get("/policies")
def get_policies():
    return POLICIES


@app.get("/logs")
def get_logs(limit: int = 50):
    return get_recent_logs(limit)

@app.post("/ingest")
async def ingest_document(file: UploadFile = File(...)):
    if not RAG_ENGINE:
        return {"error": "RAG Engine not initialized"}
    
    content = await extract_text_from_file(file)
    if not content:
        return {"error": "Could not extract text from file"}
        
    doc_id = RAG_ENGINE.add_document(content, metadata={"filename": file.filename, "timestamp": datetime.utcnow().isoformat() + "Z"})
    return {"status": "success", "doc_id": doc_id, "filename": file.filename}

@app.get("/knowledge")
def get_knowledge_base():
    if not RAG_ENGINE:
        return []
    return RAG_ENGINE.list_documents()
