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
