import sqlite3
from pathlib import Path
from typing import List, Dict, Any
import json


DB_PATH = Path(__file__).parent / "governance_logs.db"


def init_db(db_path: str = None):
    p = DB_PATH if db_path is None else Path(db_path)
    conn = sqlite3.connect(p)
    cur = conn.cursor()
    # [LEARN] 会話内容を保存するために input_text, output_text カラムを追加しました。
    # 既存のDBファイルがある場合、このスキーマ変更は反映されないため、
    # 開発中はDBファイルを削除して再生成することを推奨します。
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            user_id TEXT,
            mode TEXT,
            model TEXT,
            policy_version TEXT,
            pii_mask_applied INTEGER,
            safety_flags TEXT,
            tools_used TEXT,
            latency_ms INTEGER,
            input_text TEXT,
            output_text TEXT
        )
        """
    )
    conn.commit()
    conn.close()


def insert_log(
    timestamp: str,
    user_id: str,
    mode: str,
    model: str,
    policy_version: str,
    pii_mask_applied: bool,
    safety_flags: Dict[str, Any],
    tools_used: List[str],
    latency_ms: int,
    input_text: str,
    output_text: str
):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO logs (
            timestamp, user_id, mode, model, policy_version,
            pii_mask_applied, safety_flags, tools_used, latency_ms,
            input_text, output_text
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            timestamp,
            user_id,
            mode,
            model,
            policy_version,
            1 if pii_mask_applied else 0,
            json.dumps(safety_flags or {}),
            json.dumps(tools_used or []),
            latency_ms,
            input_text,
            output_text,
        ),
    )
    conn.commit()
    conn.close()


def get_recent_logs(limit: int = 50) -> List[Dict[str, Any]]:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row # [LEARN] カラム名でアクセスできるようにします
    cur = conn.cursor()
    cur.execute("SELECT * FROM logs ORDER BY id DESC LIMIT ?", (limit,))
    rows = cur.fetchall()
    conn.close()
    result = []
    for r in rows:
        result.append({
            "id": r["id"],
            "timestamp": r["timestamp"],
            "user_id": r["user_id"],
            "mode": r["mode"],
            "model": r["model"],
            "policy_version": r["policy_version"],
            "pii_mask_applied": bool(r["pii_mask_applied"]),
            "safety_flags": json.loads(r["safety_flags"] or "{}"),
            "tools_used": json.loads(r["tools_used"] or "[]"),
            "latency_ms": r["latency_ms"],
            "input_text": r["input_text"],
            "output_text": r["output_text"],
        })
    return result
