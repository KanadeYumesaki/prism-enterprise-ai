# backend/providers.py
"""
LLM プロバイダをまとめるモジュール。
v0.2 では Google Gemini API（google-genai）を使った実装を入れる。
"""

import os
import time
from typing import Tuple, List

from dotenv import load_dotenv
from google import genai

# .env から GEMINI_API_KEY を読み込む
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    # 起動時に気付けるようにしておく
    raise RuntimeError("GEMINI_API_KEY が設定されていません（backend/.env を確認してください）")

# Google Gen AI クライアント生成
gemini_client = genai.Client(api_key=GEMINI_API_KEY)


def _split_model_id(model_id: str) -> Tuple[str, str]:
    """
    'google:gemini-2.5-pro' -> ('google', 'gemini-2.5-pro')
    のように provider と model 名を分解する。
    """
    parts = model_id.split(":", 1)
    if len(parts) != 2:
        raise ValueError(f"model_id の形式が不正です: {model_id}")
    return parts[0], parts[1]


async def call_llm(model_id: str, system_prompt: str, user_message: str) -> Tuple[str, int]:
    """
    Governance Kernel から呼ばれる LLM 呼び出しの共通エントリポイント。

    戻り値:
        reply: LLM の返答テキスト
        latency_ms: 推論にかかった時間（ミリ秒）
    """
    start = time.perf_counter()

    provider, model_name = _split_model_id(model_id)

    # system + user を 1つの prompt にまとめるシンプル実装
    prompt = f"{system_prompt}\n\n[User]\n{user_message}"

    # 1) Google Gemini (Gemini API)
    if provider == "google":
        # docs: client.models.generate_content(model=..., contents=...)
        response = gemini_client.models.generate_content(
            model=model_name,
            contents=prompt,
        )
        reply_text = response.text or ""
        latency_ms = int((time.perf_counter() - start) * 1000)
        return reply_text, latency_ms

    # 2) それ以外のプロバイダ（今はダミー実装）
    if provider == "openai":
        reply_text = f"[DUMMY OPENAI:{model_name}] {user_message}"
    elif provider == "aws":
        reply_text = f"[DUMMY AWS:{model_name}] {user_message}"
    elif provider == "local":
        reply_text = f"[DUMMY LOCAL:{model_name}] {user_message}"
    else:
        reply_text = f"[UNKNOWN PROVIDER {provider}] {user_message}"

    latency_ms = int((time.perf_counter() - start) * 1000)
    return reply_text, latency_ms


async def call_llm_stream(model_id: str, system_prompt: str, user_message: str):
    """
    Streaming 版の LLM 呼び出し。
    AsyncGenerator[str, None] を返す。
    """
    provider, model_name = _split_model_id(model_id)
    prompt = f"{system_prompt}\n\n[User]\n{user_message}"

    if provider == "google":
        # stream=True で呼び出す
        # response はイテレータになる (非同期イテレータではない場合もあるが、google-genaiの仕様による)
        # SDKのバージョンによっては同期イテレータかもしれないが、ここでは非同期的に扱うために
        # チャンクごとに yield する。
        # google-genai v0.2+ の場合、generate_content_stream があるか、generate_content(..., config=...) か確認が必要。
        # ここでは一般的な generate_content(..., stream=True) を想定。
        
        # Note: google-genai SDK の generate_content は stream=True でジェネレータを返す
        response_stream = gemini_client.models.generate_content(
            model=model_name,
            contents=prompt,
            config=genai.types.GenerateContentConfig(response_modalities=["TEXT"]),
        )
        
        # google-genai の stream は同期イテレータで返ってくることが多いが、
        # FastAPI の StreamingResponse で使うために async generator にラップする。
        # もし SDK が async 対応しているなら await for chunk in ... と書く。
        # 現状の google-genai は同期クライアントがメインのようだが、
        # ここでは簡易的に同期イテレータを回して yield する。
        # ※ 本来は非同期クライアントを使うべきだが、既存コードに合わせて実装する。
        
        # SDKの仕様に合わせて stream=True を使う方法:
        # client.models.generate_content_stream(...) がある場合はそちらを使う。
        # なければ generate_content(..., config=...) で stream を探す。
        # ここでは generate_content_stream があると仮定、もしくは generate_content の戻り値をイテレート。
        
        # 修正: google-genai SDK では generate_content_stream メソッドが推奨される
        for chunk in gemini_client.models.generate_content_stream(
            model=model_name,
            contents=prompt,
        ):
            if chunk.text:
                yield chunk.text
                
    else:
        # ダミー実装 (一括で返してしまうが、少し待ってから返すなど)
        yield f"[DUMMY STREAM {provider}:{model_name}] "
        time.sleep(0.1)
        yield user_message
