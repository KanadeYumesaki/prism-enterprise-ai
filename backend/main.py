import time
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime

from policy_store import load_policies
from logging_db import init_db, insert_log, get_recent_logs
from governance_kernel import detect_domain, detect_pii, decide_mode, select_model
from policy_compiler import build_system_prompt
from providers import call_llm
from models import ChatRequest, ChatResponse
from file_parser import extract_text_from_file


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
    global POLICIES
    POLICIES = load_policies(BASE_DIR / "policies.yaml")
    init_db()


# [OLD CODE]
# @app.post("/chat", response_model=ChatResponse)
# async def chat_endpoint(req: ChatRequest):
#     start = time.time()
#     message = req.message
#     user_id = req.user_id
#
#     domain = detect_domain(message)
#     pii = detect_pii(message)
#     mode = decide_mode(message, POLICIES, domain, pii)
#     model = select_model(mode, POLICIES)
#     system_prompt = build_system_prompt(mode, POLICIES)
#
#     reply, latency_ms = await call_llm(model, system_prompt, message)
#
#     total_ms = int((time.time() - start) * 1000)
#
#     # Log
#     insert_log(
#         timestamp=datetime.utcnow().isoformat() + "Z",
#         user_id=user_id,
#         mode=mode,
#         model=model,
#         policy_version=POLICIES.get("version", "0.0"),
#         pii_mask_applied=pii.get("pii_detected", False),
#         safety_flags={"detected_types": pii.get("detected_types", [])},
#         tools_used=[],
#         latency_ms=total_ms,
#     )
#
#     return ChatResponse(
#         reply=reply,
#         mode=mode,
#         model=model,
#         policy_version=POLICIES.get("version", "0.0"),
#         safety_flags=["pii" ] if pii.get("pii_detected") else [],
#         tools_used=[],
#         latency_ms=total_ms,
#     )

# [NEW CODE] なぜこのように変更したか:
# 1. ファイルアップロード (multipart/form-data) に対応するため、JSONボディ (ChatRequest) ではなく Form と File を使います。
# 2. Pydanticモデル (ChatRequest) は JSON ボディを期待するため、Formデータと混在させることが難しいため、個別の引数として定義します。
# 3. [UPDATE] 複数ファイルに対応するため、List[UploadFile] を使用します。
from typing import List

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(
    user_id: str = Form(...),
    message: str = Form(...),
    files: List[UploadFile] = File(default=[]) # [LEARN] 複数ファイルを受け取るために List と default=[] を指定
):
    start = time.time()

    # [NEW CODE] 複数ファイルの処理
    # 各ファイルからテキストを抽出し、メッセージに追記します。
    if files:
        file_contents = []
        for file in files:
            # 空のファイルオブジェクトが送られてくる場合があるためチェック
            if file.filename:
                content = await extract_text_from_file(file)
                file_contents.append(f"Filename: {file.filename}\nContent:\n{content}")
        
        if file_contents:
            message += "\n\n[Attached Files]\n" + "\n---\n".join(file_contents)

    domain = detect_domain(message)
    pii = detect_pii(message)
    mode = decide_mode(message, POLICIES, domain, pii)

    # [NEW CODE] ファイルがある場合の強制モード変更ロジック
    # ファイル処理は複雑な推論が必要な場合が多いため、より高性能なモード(HEAVY等)に切り替えます
    if files and mode == "FAST":
         mode = "HEAVY"

    model = select_model(mode, POLICIES)
    system_prompt = build_system_prompt(mode, POLICIES)

    reply, latency_ms = await call_llm(model, system_prompt, message)

    total_ms = int((time.time() - start) * 1000)

    # Log
    insert_log(
        timestamp=datetime.utcnow().isoformat() + "Z",
        user_id=user_id,
        mode=mode,
        model=model,
        policy_version=POLICIES.get("version", "0.0"),
        pii_mask_applied=pii.get("pii_detected", False),
        safety_flags={"detected_types": pii.get("detected_types", [])},
        tools_used=[],
        latency_ms=total_ms,
        input_text=message, # [UPDATE] 会話内容を保存
        output_text=reply   # [UPDATE] 会話内容を保存
    )

    return ChatResponse(
        reply=reply,
        mode=mode,
        model=model,
        policy_version=POLICIES.get("version", "0.0"),
        safety_flags=["pii" ] if pii.get("pii_detected") else [],
        tools_used=[],
        latency_ms=total_ms,
    )


@app.get("/policies")
def get_policies():
    return POLICIES


@app.get("/logs")
def get_logs(limit: int = 50):
    return get_recent_logs(limit)
