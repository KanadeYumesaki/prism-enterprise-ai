from typing import List, Optional, Dict, Any
from sqlmodel import Field, SQLModel, Relationship, JSON
from pydantic import BaseModel

# --- API Models (Pydantic) ---

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


class LoginRequest(BaseModel):
    user_id: str
    tenant_id: str


# --- DB Models (SQLModel) ---

class Tenant(SQLModel, table=True):
    id: str = Field(primary_key=True)
    name: str
    
    members: List["TenantMember"] = Relationship(back_populates="tenant")
    logs: List["Log"] = Relationship(back_populates="tenant")


class User(SQLModel, table=True):
    id: str = Field(primary_key=True)
    display_name: str
    
    tenant_memberships: List["TenantMember"] = Relationship(back_populates="user")
    logs: List["Log"] = Relationship(back_populates="user")


class TenantMember(SQLModel, table=True):
    tenant_id: str = Field(foreign_key="tenant.id", primary_key=True)
    user_id: str = Field(foreign_key="user.id", primary_key=True)
    role: str = Field(default="user")  # "admin", "user"
    
    user: User = Relationship(back_populates="tenant_memberships")
    tenant: Tenant = Relationship(back_populates="members")


class Log(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    timestamp: str
    user_id: str = Field(foreign_key="user.id")
    tenant_id: str = Field(foreign_key="tenant.id")
    mode: str
    model: str
    policy_version: str
    pii_mask_applied: bool
    safety_flags: List[str] = Field(default=[], sa_type=JSON)
    tools_used: List[str] = Field(default=[], sa_type=JSON)
    latency_ms: int
    input_text: str
    output_text: str

    user: User = Relationship(back_populates="logs")
    tenant: Tenant = Relationship(back_populates="logs")
