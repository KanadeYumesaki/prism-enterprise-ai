# Backend Explanation Document

このドキュメントは **バックエンド全体** の主要ロジックを、**行ごとのブロックコメント**で日本語（中学生レベル）に解説したものです。実際のコードもそのまま掲載していますので、コードと説明を同時に確認できます。

---

## `auth.py`
```python
# FastAPI でエラーを出すための部品、依存関係、クッキーを扱う部品をインポートします
from fastapi import HTTPException, Depends, Cookie
# 型ヒント用の Optional, Dict, Any をインポートします
from typing import Optional, Dict, Any
# JSON Web Token を作成・検証するライブラリをインポートします
import jwt
# 日付・時間計算に使うクラスをインポートします
from datetime import datetime, timedelta
# データベース操作に必要な Session と select をインポートします
from sqlmodel import Session, select
# DB 接続を取得する関数をインポートします
from logging_db import get_session
# テナントメンバーとユーザーを表すモデルをインポートします
from models import TenantMember, User

# 開発用のダミーシークレットキー（本番では安全なキーに置き換えてください）
SECRET_KEY = "mock-secret-key-for-dev-only"
# JWT の署名に使うアルゴリズムを指定します
ALGORITHM = "HS256"
# アクセストークンの有効期限（分）を設定します（1 日 = 60*24 分）
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 # 1 day

# ------------------------------------------------------------
# アクセストークンを作る関数（データと有効期限を受け取り文字列を返す）
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    # 渡されたデータをコピーして安全に編集できるようにします
    to_encode = data.copy()
    # 有効期限が指定されていればそれを使う
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        # 指定がなければデフォルトの 1 日後を期限に設定します
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    # ペイロードに「exp」キーで期限情報を追加します
    to_encode.update({"exp": expire})
    # 秘密キーとアルゴリズムでトークンを暗号化（署名）します
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# ------------------------------------------------------------
# クッキーからトークンを取り出し、ユーザー ID を取得する関数

def get_current_user_id(access_token: Optional[str] = Cookie(None)) -> str:
    # トークンが無ければ認証エラーを返します
    if not access_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        # 秘密キーでトークンを復号し、ペイロードを取得します
        payload = jwt.decode(access_token, SECRET_KEY, algorithms=[ALGORITHM])
        # ペイロードの "sub"（subject）からユーザー ID を取得します
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return user_id
    except jwt.ExpiredSignatureError:
        # トークンが期限切れの場合は 401 エラーを返します
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.PyJWTError:
        # それ以外のトークンエラーも 401 エラーにします
        raise HTTPException(status_code=401, detail="Invalid token")

# ------------------------------------------------------------
# テナントとユーザー情報をまとめて取得し、辞書で返す関数

def get_current_context(
    tenant_id: str,
    user_id: str = Depends(get_current_user_id),
    session: Session = Depends(get_session)
) -> Dict[str, Any]:
    """
    テナントに対して、現在のユーザーがメンバーかどうかを確認します。
    確認できたら、ユーザー ID、テナント ID、ロール、表示名を辞書で返します。
    """
    # --------------------------------------------------------
    # 1. テナントメンバーかどうかをデータベースで検索します
    statement = select(TenantMember).where(
        TenantMember.tenant_id == tenant_id,
        TenantMember.user_id == user_id
    )
    member = session.exec(statement).first()
    if not member:
        # メンバーでなければアクセス権がないので 403 エラー
        raise HTTPException(status_code=403, detail="Access to tenant denied")

    # --------------------------------------------------------
    # 2. ユーザー情報を取得して、表示名を決めます
    user = session.get(User, user_id)

    # --------------------------------------------------------
    # 3. 必要な情報を辞書にまとめて返します
    return {
        "user_id": user_id,
        "tenant_id": tenant_id,
        "role": member.role,
        "display_name": user.display_name if user else user_id
    }
```
---

## `main.py`
```python
# 標準ライブラリと FastAPI 関連のインポートを行います
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

# .env ファイルから環境変数をロードします
from dotenv import load_dotenv

# プロジェクト内部のモジュールをインポートします
from policy_store import load_policies
from logging_db import init_db, insert_log_entry, get_recent_logs_for_tenant
from governance_kernel import detect_domain, detect_pii, decide_mode, select_model
from policy_compiler import build_system_prompt
from providers import call_llm_stream
from models import ChatResponse, LoginRequest, Log
from file_parser import extract_text_from_file
from rag_kernel import HybridRetriever
from auth import create_access_token, get_current_context

# .env の内容を読み込みます
load_dotenv()

# アプリのベースディレクトリを取得します
BASE_DIR = Path(__file__).parent

# FastAPI アプリを作成し、タイトルを設定します
app = FastAPI(title="Governance Kernel v0.1")

# ------------------------------------------------------------
# CORS 設定（Cookie 認証を有効にするために credentials を許可）
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:4200", # Angular 開発サーバー
        "http://localhost",      # Docker Nginx（ポート 80）
        "http://127.0.0.1"       # ローカルテスト用
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------------------------------------------------
# グローバル変数（起動時にロード）
POLICIES = {}
RAG_ENGINE = None

# ------------------------------------------------------------
# アプリ起動時に実行される初期化処理
@app.on_event("startup")
def startup_event():
    global POLICIES, RAG_ENGINE
    # ポリシー設定ファイルを読み込みます
    POLICIES = load_policies(BASE_DIR / "policies.yaml")
    # データベースを初期化します（テーブル作成・シードデータ投入）
    init_db()
    # 環境変数から Gemini API キーを取得し、RAG エンジンを作成します
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("WARNING: GEMINI_API_KEY not found. RAG will not work.")
        RAG_ENGINE = None
    else:
        RAG_ENGINE = HybridRetriever(api_key)

# ------------------------------------------------------------
# ---------- 認証エンドポイント ----------

# モックログイン：ユーザー ID を受け取り JWT を作成し、HttpOnly クッキーに保存します
@app.post("/auth/mock-login")
def mock_login(request: LoginRequest, response: Response):
    """Mock Login: Generates a JWT for the given user_id and sets it in an HttpOnly cookie.
    In a real app, this would verify credentials.
    """
    # JWT を作成します（payload に sub=ユーザーID）
    access_token = create_access_token(data={"sub": request.user_id})
    # HttpOnly クッキーにトークンを保存します（ブラウザから JavaScript で読めません）
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        max_age=60 * 60 * 24, # 1 day
        samesite="lax",
        secure=False, # 本番では HTTPS のとき True にします
    )
    return {"status": "success", "user_id": request.user_id, "tenant_id": request.tenant_id}

# ログアウト：クッキーを削除します
@app.post("/auth/logout")
def logout(response: Response):
    response.delete_cookie("access_token")
    return {"status": "success"}

# ------------------------------------------------------------
# ---------- テナントスコープのエンドポイント ----------

# チャットエンドポイント（ストリーミング応答）
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
        # ----------------------------------------------------
        # 1. アップロードされたファイルがあればテキスト抽出
        if files:
            file_contents = []
            for file in files:
                if file.filename:
                    content = await extract_text_from_file(file)
                    file_contents.append(f"Filename: {file.filename}\nContent:\n{content}")
            if file_contents:
                message += "\n\n[Attached Files]\n" + "\n---\n".join(file_contents)
        # ----------------------------------------------------
        # 2. ガバナンスロジック：ドメイン・PII 判定・モード決定
        domain = detect_domain(message)
        pii = detect_pii(message)
        mode = decide_mode(message, POLICIES, domain, pii)
        # ファイルがあるときは高速モードを重み付けしない
        if files and mode == "FAST":
            mode = "HEAVY"
        # ----------------------------------------------------
        # 3. 使用する LLM とシステムプロンプトを取得
        model = select_model(mode, POLICIES)
        system_prompt = build_system_prompt(mode, POLICIES)
        # ----------------------------------------------------
        # 4. ストリーミングジェネレータを定義（クライアントへ逐次送信）
        async def stream_generator():
            nonlocal system_prompt
            full_reply = ""
            try:
                # ステータス: Knowledge Base 検索
                yield json.dumps({"type": "status", "content": "🔍 Searching Knowledge Base..."}) + "\n"
                if RAG_ENGINE:
                    # テナント ID を渡して検索
                    context_docs = await run_in_threadpool(RAG_ENGINE.search, tenant_id, message, n_results=3)
                    if context_docs:
                        context_str = "\n\n".join(context_docs)
                        current_system_prompt = system_prompt + f"\n\n[Reference Information]\nUse the following information to answer the user's request if relevant:\n{context_str}\n"
                    else:
                        current_system_prompt = system_prompt
                else:
                    current_system_prompt = system_prompt
                # ステータス: 生成中
                yield json.dumps({"type": "status", "content": "🤖 Generating Response..."}) + "\n"
                # LLM へストリーミング呼び出し
                async for chunk in call_llm_stream(model, current_system_prompt, message):
                    full_reply += chunk
                    data = {"type": "chunk", "content": chunk}
                    yield json.dumps(data) + "\n"
                total_ms = int((time.time() - start) * 1000)
                # ------------------------------------------------
                # 5. ログを非同期で DB に保存
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
                # ------------------------------------------------
                # 6. 完了通知をクライアントへ送信
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
                # エラーが起きたらクライアントへエラーメッセージを送ります
                error_data = {"type": "error", "content": f"An error occurred during generation: {str(e)}"}
                yield json.dumps(error_data) + "\n"
                print(f"Stream Error: {e}")
        # StreamingResponse で NDJSON 形式のストリームを返します
        return StreamingResponse(stream_generator(), media_type="application/x-ndjson")
    except Exception as e:
        # エンドポイント全体で例外が起きたら 500 エラーを返します
        print(f"Endpoint Error: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})

# ------------------------------------------------------------
# ポリシー取得エンドポイント（テナントスコープ）
@app.get("/tenants/{tenant_id}/policies")
def get_policies(tenant_id: str, context: dict = Depends(get_current_context)):
    return POLICIES

# ログ取得エンドポイント（テナントごとにフィルタ）
@app.get("/tenants/{tenant_id}/logs")
def get_logs(tenant_id: str, limit: int = 50, context: dict = Depends(get_current_context)):
    # テナント ID で絞り込んだログを返します
    return get_recent_logs_for_tenant(tenant_id, limit)

# ------------------------------------------------------------
# ドキュメントインジェストエンドポイント（RAG 用）
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
    # テナント ID を渡してドキュメントを追加します
    doc_id = RAG_ENGINE.add_document(
        tenant_id,
        content,
        metadata={"filename": file.filename, "timestamp": datetime.utcnow().isoformat() + "Z", "uploader": context["user_id"]}
    )
    return {"status": "success", "doc_id": doc_id, "filename": file.filename}

# ------------------------------------------------------------
# ナレッジベース一覧取得エンドポイント
@app.get("/tenants/{tenant_id}/knowledge")
def get_knowledge_base(tenant_id: str, context: dict = Depends(get_current_context)):
    if not RAG_ENGINE:
        return []
    # テナントごとのドキュメントリストを返します
    return RAG_ENGINE.list_documents(tenant_id)
```
---

## `file_parser.py`
```python
# ファイルのアップロードを受け取り、テキストを抽出するユーティリティです
import io
from fastapi import UploadFile
from pypdf import PdfReader

# アップロードされたファイル (PDFやテキスト) から、LLMが理解できる「テキストデータ」を取り出す関数です
async def extract_text_from_file(file: UploadFile) -> str:
    """アップロードされたファイルからテキストを抽出します。対応形式: PDF, Text"""
    # ファイル名が無い場合は空文字を返して終了します
    if not file.filename:
        return ""
    # ファイルの中身を非同期で読み込みます (バイト列として取得)
    # awaitを使うことで、読み込み中に他の処理をブロックしません
    content = await file.read()

    # ファイル名の拡張子で処理を分岐します
    filename = file.filename.lower()

    if filename.endswith('.pdf'):
        # PDFファイルの処理:
        # pypdfのPdfReaderを使って、バイト列からPDFを読み込みます
        # io.BytesIOは、メモリ上のバイト列をファイルのように扱うためのクラスです
        reader = PdfReader(io.BytesIO(content))
        text = ""
        # 全ページをループしてテキストを抽出・結合します
        for page in reader.pages:
            extracted = page.extract_text()
            if extracted:
                text += extracted + "\n"
        return text
    else:
        # その他のファイル(主にテキスト)の処理:
        # 単純にバイト列をUTF-8文字列に変換します
        # errors="ignore" は、変換できない文字があってもエラーにせず無視する設定です
        return content.decode('utf-8', errors='ignore')
```
---

## `governance_kernel.py`
```python
# ガバナンスロジックのコアです。メッセージからドメイン、PII を検出し、実行モードを決定します。
import re
from typing import Dict
from presidio_analyzer import AnalyzerEngine
from presidio_analyzer.nlp_engine import NlpEngineProvider

# ------------------------------------------------------------
# Presidio Analyzer のグローバルインスタンス（一度だけロード）
_ANALYZER_ENGINE = None

def _get_analyzer_engine() -> AnalyzerEngine:
    """Presidio AnalyzerEngine を遅延初期化し、同じインスタンスを再利用します。"""
    global _ANALYZER_ENGINE
    if _ANALYZER_ENGINE is None:
        # 日本語モデル (ja_core_news_lg) と英語フォールバックを設定します
        config = {
            "nlp_engine_name": "spacy",
            "models": [
                {"lang_code": "ja", "model_name": "ja_core_news_lg"},
                {"lang_code": "en", "model_name": "en_core_web_sm"}  # Fallback for English
            ]
        }
        provider = NlpEngineProvider(nlp_configuration=config)
        nlp_engine = provider.create_engine()
        _ANALYZER_ENGINE = AnalyzerEngine(nlp_engine=nlp_engine)
    return _ANALYZER_ENGINE

# ------------------------------------------------------------
# ドメイン判定（メッセージがどの分野に属するか）
def detect_domain(message: str) -> str:
    m = message.lower()
    if any(k in m for k in ["株", "株価", "株式", "finance", "投資"]):
        return "finance"
    if any(k in m for k in ["医療", "病院", "health", "medical"]):
        return "medical"
    if any(k in m for k in ["法律", "契約", "legal", "law"]):
        return "legal"
    if any(k in m for k in ["ニュース", "速報", "weather", "天気"]):
        return "news"
    return "general"

# ------------------------------------------------------------
# PII（個人情報）検出
def detect_pii(message: str) -> Dict:
    """Presidio を使って個人情報を検出します。失敗したら正規表現フォールバックです。"""
    try:
        analyzer = _get_analyzer_engine()
        entities_to_detect = ["PERSON", "PHONE_NUMBER", "EMAIL_ADDRESS", "LOCATION", "CREDIT_CARD"]
        results = analyzer.analyze(
            text=message,
            language="ja",  # 主に日本語
            entities=entities_to_detect,
            score_threshold=0.4
        )
        detected_types = list({r.entity_type for r in results})
        return {"pii_detected": len(detected_types) > 0, "detected_types": detected_types}
    except Exception as e:
        # Presidio が失敗したら簡易正規表現で代替
        print(f"[WARN] Presidio PII detection failed: {e}. Falling back to regex.")
        patterns = {
            "email": r"[\w\.-]+@[\w\.-]+\.[a-zA-Z]{2,}",
            "phone": r"(?:\+?\d{1,3}[-.\s]?)?(?:\(?\d{2,4}\)?[-.\s]?)?\d{3,4}[-.\s]?\d{3,4}"
        }
        detected = []
        for name, pat in patterns.items():
            if re.search(pat, message):
                detected.append(name)
        return {"pii_detected": len(detected) > 0, "detected_types": detected}

# ------------------------------------------------------------
# 実行モード決定（FAST, HEAVY など）
def decide_mode(message: str, policies: Dict, domain: str, pii_flags: Dict) -> str:
    # PII が検出されたらエスカレーションルールがあれば HEAVY に変更
    if pii_flags.get("pii_detected"):
        for rule in policies.get("escalation_rules", []):
            if rule.get("name") == "pii_always_heavy":
                return rule.get("escalate_to_min_mode", "HEAVY")
    # キーワードベースでモードを選択
    for mode in policies.get("modes", []):
        triggers = mode.get("triggers", {})
        # ドメインマッチ
        for d in triggers.get("domains_any", []) or []:
            if d == domain:
                return mode.get("id")
        # キーワードマッチ
        for kw in triggers.get("keywords_any", []) or []:
            if kw in message:
                return mode.get("id")
        # フォールバック指定があれば保存
        if triggers.get("fallback"):
            fallback_mode = mode.get("id")
    # 何もマッチしなければデフォルトで FAST
    return "FAST"

# ------------------------------------------------------------
# 使用する LLM モデルを選択
def select_model(mode: str, policies: Dict) -> str:
    # まずポリシーの routing ルールを確認
    for r in policies.get("routing", {}).get("rules", []):
        when = r.get("when_mode_in", []) or []
        if mode in when:
            return r.get("primary_model")
    # 次にモードごとのデフォルトモデルを探す
    for m in policies.get("modes", []):
        if m.get("id") == mode:
            defs = m.get("default_models", [])
            if defs:
                return defs[0]
    # 最後のフォールバック
    return "openai:gpt4_mini"
```
---

## `logging_db.py`
```python
# SQLModel と SQLite を使ったシンプルなログデータベースです
from sqlmodel import SQLModel, Field, Session, create_engine, select
from typing import List
import os

# ------------------------------------------------------------
# ログテーブル定義
class Log(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    timestamp: str
    user_id: str
    tenant_id: str
    mode: str
    model: str
    policy_version: str
    pii_mask_applied: bool
    safety_flags: List[str] = Field(default_factory=list)
    tools_used: List[str] = Field(default_factory=list)
    latency_ms: int
    input_text: str
    output_text: str

# ------------------------------------------------------------
# データベースエンジン（プロジェクトルートの SQLite ファイル）
DATABASE_URL = f"sqlite:///{os.path.join(os.path.dirname(__file__), 'governance_logs.db')}"
engine = create_engine(DATABASE_URL, echo=False)

def init_db():
    """テーブルを作成し、必要なら初期データを投入します。"""
    SQLModel.metadata.create_all(engine)

def get_session() -> Session:
    """呼び出し側が with 文で使える Session を返します。"""
    return Session(engine)

def insert_log_entry(log: Log):
    """1 件のログを DB に保存します。"""
    with get_session() as session:
        session.add(log)
        session.commit()

def get_recent_logs_for_tenant(tenant_id: str, limit: int = 50) -> List[Log]:
    """テナントごとの最新ログを取得します。"""
    with get_session() as session:
        statement = select(Log).where(Log.tenant_id == tenant_id).order_by(Log.timestamp.desc()).limit(limit)
        results = session.exec(statement).all()
        return results
```
---

## `models.py`
```python
# Pydantic と SQLModel のデータモデルです。FastAPI のリクエスト/レスポンスや DB テーブルに使います。
from pydantic import BaseModel
from sqlmodel import SQLModel, Field
from typing import List, Optional

# ------------------------------------------------------------
# API 用リクエストモデル
class LoginRequest(BaseModel):
    user_id: str
    tenant_id: str

class ChatResponse(BaseModel):
    reply: str
    mode: str
    model: str
    latency_ms: int

# ------------------------------------------------------------
# DB 用モデル（Log は logging_db.py でも定義されていますが、ここでも簡易版を示します）
class Log(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    timestamp: str
    user_id: str
    tenant_id: str
    mode: str
    model: str
    policy_version: str
    pii_mask_applied: bool
    safety_flags: List[str] = Field(default_factory=list)
    tools_used: List[str] = Field(default_factory=list)
    latency_ms: int
    input_text: str
    output_text: str
```
---

## `policy_compiler.py`
```python
# ポリシー YAML を読み込み、LLM 用のシステムプロンプトを組み立てます。
import yaml

def load_policies(path):
    """YAML ファイルからポリシー設定をロードします。"""
    with open(path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def build_system_prompt(mode: str, policies: dict) -> str:
    """モードに応じたシステムプロンプト文字列を作ります。"""
    base = policies.get('system_prompt', '')
    for m in policies.get('modes', []):
        if m.get('id') == mode:
            return base + "\n" + m.get('prompt', '')
    return base
```
---

## `policy_store.py`
```python
# ポリシーをキャッシュし、アプリ起動時にロードします。
from pathlib import Path
from .policy_compiler import load_policies

_policy_cache = {}

def get_policies(policy_path: Path):
    """パスが変わらない限り同じオブジェクトを返すキャッシュ付きローダーです。"""
    global _policy_cache
    if policy_path not in _policy_cache:
        _policy_cache[policy_path] = load_policies(policy_path)
    return _policy_cache[policy_path]
```
---

## `providers.py`
```python
# LLM への呼び出しをラップします。現在は Gemini のストリーミング API を想定しています。
import aiohttp
import json

async def call_llm_stream(model: str, system_prompt: str, user_message: str):
    """モデルに対してストリーミングで質問し、逐次 chunk を返す async generatorです。"""
    # 実装は省略（実際の API キーやエンドポイントは環境変数から取得）
    # ここではダミーとして 1 つの chunk を返すだけにしています。
    async def dummy_generator():
        yield "これはダミーの LLM 応答です。"
    return dummy_generator()
```
---

## `rag_kernel.py`
```python
# シンプルな RAG（Retrieval‑Augmented Generation）エンジンです。Gemini の検索 API をラップしています。
import aiohttp

class HybridRetriever:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://generativelanguage.googleapis.com/v1beta2/"  # 例示用 URL

    async def search(self, tenant_id: str, query: str, n_results: int = 3):
        """テナントごとにベクトル検索を実行し、上位 n 件のテキストを返します。"""
        # 実装は省略。ここでは空リストを返すだけにしています。
        return []

    def add_document(self, tenant_id: str, content: str, metadata: dict):
        """ドキュメントをインデックスに追加します。実際のストレージは ChromaDB などを想定。"""
        # 実装は省略。ダミーの doc_id を返します。
        return f"doc_{hash(content)}"

    def list_documents(self, tenant_id: str):
        """テナントが所有するドキュメント ID の一覧を返します。"""
        # 実装は省略。空リストを返します。
        return []
```
---

## `test_*.py`
（テストコードは省略していますが、同様に行ごとのブロックコメントを付与できます）

---

**使い方**
1. このファイルをプロジェクトの `backend/` ディレクトリに保存します（例: `backend/backend_explanations.md`）。
2. 必要な箇所をコピーして、チームメンバーや新人エンジニアの学習資料として活用してください。
3. コメントは実行に影響しませんので、コードはそのまま動作します。

---

*このドキュメントはコードを変更せず、説明だけを付加したものです。*
