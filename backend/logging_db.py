from sqlmodel import SQLModel, Session, create_engine, select
from pathlib import Path
from typing import List, Dict, Any, Generator
import json
from models import Log, Tenant, User, TenantMember

# ...
# 変更前: ソースコードの横に作られる（コンテナ再作成で消える）
# DB_PATH = Path(__file__).parent / "governance_logs.db"

# 変更後: マウントされたボリューム(/app/data)の中に作る（消えない）
# ※ ローカル開発時とDocker時でパスを切り替えるロジック
import os

if os.path.exists("/app/data"):
    # Docker環境
    DB_PATH = Path("/app/data/governance_logs.db")
else:
    # ローカル開発環境
    DB_PATH = Path(__file__).parent / "governance_logs.db"

sqlite_url = f"sqlite:///{DB_PATH}"

# check_same_thread=False is needed for SQLite with multiple threads (FastAPI)
engine = create_engine(sqlite_url, connect_args={"check_same_thread": False})

def init_db():
    SQLModel.metadata.create_all(engine)
    
    # Seed Mock Data
    with Session(engine) as session:
        # Check if data exists
        if not session.exec(select(Tenant)).first():
            # Create Tenants
            t1 = Tenant(id="tenant-a", name="Acme Corp")
            t2 = Tenant(id="tenant-b", name="Beta Inc")
            
            # Create Users
            u1 = User(id="user-1", display_name="Alice (Admin)")
            u2 = User(id="user-2", display_name="Bob (User)")
            
            # Create Memberships
            # Alice is Admin of Tenant A, User of Tenant B
            m1 = TenantMember(tenant_id="tenant-a", user_id="user-1", role="admin")
            m2 = TenantMember(tenant_id="tenant-b", user_id="user-1", role="user")
            
            # Bob is User of Tenant A
            m3 = TenantMember(tenant_id="tenant-a", user_id="user-2", role="user")
            
            session.add(t1)
            session.add(t2)
            session.add(u1)
            session.add(u2)
            session.add(m1)
            session.add(m2)
            session.add(m3)
            session.commit()

def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session

# Helper for legacy support or direct usage
def insert_log_entry(log: Log):
    with Session(engine) as session:
        session.add(log)
        session.commit()
        session.refresh(log)
    return log

def get_recent_logs_for_tenant(tenant_id: str, limit: int = 50) -> List[Dict[str, Any]]:
    with Session(engine) as session:
        statement = select(Log).where(Log.tenant_id == tenant_id).order_by(Log.id.desc()).limit(limit)
        results = session.exec(statement).all()
        return [log.model_dump() for log in results]
