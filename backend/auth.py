from fastapi import HTTPException, Depends, Cookie
from typing import Optional, Dict, Any
import jwt
from datetime import datetime, timedelta
from sqlmodel import Session, select
from logging_db import get_session
from models import TenantMember, User

SECRET_KEY = "mock-secret-key-for-dev-only"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 # 1 day

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_current_user_id(access_token: Optional[str] = Cookie(None)) -> str:
    if not access_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        payload = jwt.decode(access_token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return user_id
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

def get_current_context(
    tenant_id: str,
    user_id: str = Depends(get_current_user_id),
    session: Session = Depends(get_session)
) -> Dict[str, Any]:
    """
    Verifies that the authenticated user is a member of the requested tenant.
    Returns context dict with user_id, tenant_id, role, and display_name.
    """
    # Verify membership
    statement = select(TenantMember).where(
        TenantMember.tenant_id == tenant_id,
        TenantMember.user_id == user_id
    )
    member = session.exec(statement).first()
    if not member:
        raise HTTPException(status_code=403, detail="Access to tenant denied")
    
    # Get user details for display name
    user = session.get(User, user_id)
    
    return {
        "user_id": user_id,
        "tenant_id": tenant_id,
        "role": member.role,
        "display_name": user.display_name if user else user_id
    }
