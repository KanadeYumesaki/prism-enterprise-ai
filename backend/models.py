from pydantic import BaseModel
from typing import List, Optional


class ChatRequest(BaseModel):
    user_id: str
    message: str
    metadata: Optional[dict] = None


class ChatResponse(BaseModel):
    reply: str
    mode: str
    model: str
    policy_version: str
    safety_flags: List[str]
    tools_used: List[str]
    latency_ms: int


class LogRecord(BaseModel):
    id: int
    timestamp: str
    user_id: str
    mode: str
    model: str
    policy_version: str
    pii_mask_applied: bool
    safety_flags: List[str]
    tools_used: List[str]
    latency_ms: int
