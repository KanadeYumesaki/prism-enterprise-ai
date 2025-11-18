import sqlite3
from pathlib import Path
from typing import List, Dict, Any
import json


DB_PATH = Path(__file__).parent / "governance_logs.db"


def init_db(db_path: str = None):
    p = DB_PATH if db_path is None else Path(db_path)
    conn = sqlite3.connect(p)
    cur = conn.cursor()
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
            latency_ms INTEGER
        )
        """
    )
    conn.commit()
    conn.close()


def insert_log(timestamp: str, user_id: str, mode: str, model: str, policy_version: str, pii_mask_applied: bool, safety_flags: Dict[str, Any], tools_used: List[str], latency_ms: int):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO logs (timestamp, user_id, mode, model, policy_version, pii_mask_applied, safety_flags, tools_used, latency_ms) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
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
        ),
    )
    conn.commit()
    conn.close()


def get_recent_logs(limit: int = 50) -> List[Dict[str, Any]]:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT id, timestamp, user_id, mode, model, policy_version, pii_mask_applied, safety_flags, tools_used, latency_ms FROM logs ORDER BY id DESC LIMIT ?", (limit,))
    rows = cur.fetchall()
    conn.close()
    result = []
    for r in rows:
        result.append({
            "id": r[0],
            "timestamp": r[1],
            "user_id": r[2],
            "mode": r[3],
            "model": r[4],
            "policy_version": r[5],
            "pii_mask_applied": bool(r[6]),
            "safety_flags": json.loads(r[7] or "{}"),
            "tools_used": json.loads(r[8] or "[]"),
            "latency_ms": r[9],
        })
    return result
