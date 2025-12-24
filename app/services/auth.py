# (login/refresh/logout + Redis refresh 저장)
from fastapi import HTTPException
from redis import Redis
from sqlmodel import Session
from typing import Optional

from app.core.security import verify_password, create_token, decode_token
from app.repositories.users import get_user_by_email, get_user_by_id
from app.db.models import UserStatus

ACCESS_MIN = 30
REFRESH_MIN = 60 * 24 * 7  # 7 days

def _refresh_key(user_id: int) -> str:
    return f"refresh:{user_id}"

def login(db: Session, rds: Redis, email: str, password: str):
    user = get_user_by_email(db, email)
    if not user or user.deleted_at is not None:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if user.status in (UserStatus.BLOCKED, UserStatus.DELETED):
        raise HTTPException(status_code=403, detail="User blocked/deleted")
    if not verify_password(password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    access = create_token(str(user.id), "access", ACCESS_MIN)
    refresh = create_token(str(user.id), "refresh", REFRESH_MIN)

    # store refresh token (simple: 1 per user)
    if rds is not None:
        rds.setex(_refresh_key(user.id), REFRESH_MIN * 60, refresh)
    return access, refresh

def refresh(db: Session, rds: Optional[Redis], refresh_token: str):
    try:
        payload = decode_token(refresh_token)
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    if payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Refresh token required")

    user_id = int(payload.get("sub", 0))
    user = get_user_by_id(db, user_id)
    if not user or user.deleted_at is not None:
        raise HTTPException(status_code=401, detail="User not found")

    # Redis가 있으면 토큰 검증 (Whitelist), 없으면 생략
    if rds:
        try:
            saved = rds.get(_refresh_key(user_id))
            if not saved or saved != refresh_token:
                raise HTTPException(status_code=401, detail="Refresh token revoked")
        except Exception:
            pass

    new_access = create_token(str(user_id), "access", ACCESS_MIN)
    new_refresh = create_token(str(user_id), "refresh", REFRESH_MIN)
    
    if rds:
        try:
            rds.setex(_refresh_key(user_id), REFRESH_MIN * 60, new_refresh)
        except Exception:
            pass

    return new_access, new_refresh

def logout(rds: Optional[Redis], user_id: int):
    # Redis가 없으면 아무것도 하지 않음
    if rds:
        try:
            rds.delete(_refresh_key(user_id))
        except Exception:
            pass
