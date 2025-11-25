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

from starlette.concurrency import run_in_threadpool

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

    try:
        # 1) Google Gemini (Gemini API)
        if provider == "google":
            # docs: client.models.generate_content(model=..., contents=...)
            # 同期メソッドなので run_in_threadpool でラップ
            response = await run_in_threadpool(
                gemini_client.models.generate_content,
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

    except Exception as e:
        print(f"LLM Call Error: {e}")
        # エラー時は空文字ではなくエラーメッセージを返すか、呼び出し元でハンドリングする
        # ここではエラーメッセージを返す
        return f"Error: {str(e)}", int((time.perf_counter() - start) * 1000)


async def call_llm_stream(model_id: str, system_prompt: str, user_message: str):
    """
    Streaming 版の LLM 呼び出し。
    AsyncGenerator[str, None] を返す。
    """
    provider, model_name = _split_model_id(model_id)
    prompt = f"{system_prompt}\n\n[User]\n{user_message}"

    try:
        if provider == "google":
            # stream=True で呼び出す
            # generate_content_stream は同期イテレータを返すことが多いが、
            # ネットワーク呼び出しを含むため run_in_threadpool でラップして呼び出す
            
            # Note: google-genai SDK の generate_content は stream=True でジェネレータを返す
            # ストリームの作成自体を非同期化
            response_stream = await run_in_threadpool(
                gemini_client.models.generate_content_stream,
                model=model_name,
                contents=prompt,
            )
            
            # 同期イテレータを回す
            # 注意: next() ごとにブロックする可能性があるが、
            # 現状のアーキテクチャでは許容範囲とするか、さらにラップが必要。
            # ここでは簡易的にそのまま回す。
            for chunk in response_stream:
                if chunk.text:
                    yield chunk.text
                    
        else:
            # ダミー実装 (一括で返してしまうが、少し待ってから返すなど)
            yield f"[DUMMY STREAM {provider}:{model_name}] "
            time.sleep(0.1)
            yield user_message

    except Exception as e:
        print(f"LLM Stream Error: {e}")
        yield f"Error: {str(e)}"
