from typing import Optional

from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlmodel import Session, select

from src.deps.db import get_db
from src.core.security import decode_token
from src.db.models import User, UserRole, UserStatus

bearer = HTTPBearer(auto_error=False)

def get_current_user(
    creds: Optional[HTTPAuthorizationCredentials] = Depends(bearer),
    db: Session = Depends(get_db),
) -> User:
    if creds is None:
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        payload = decode_token(creds.credentials)
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid token")

    if payload.get("type") != "access":
        raise HTTPException(status_code=401, detail="Access token required")

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token")

    user = db.exec(select(User).where(User.id == int(user_id))).first()
    if not user or user.deleted_at is not None:
        raise HTTPException(status_code=401, detail="User not found")

    if user.status in (UserStatus.BLOCKED, UserStatus.DELETED):
        raise HTTPException(status_code=403, detail="User blocked/deleted")

    return user


# Admin 권한이 필요한 경우(RBAC)
def require_admin(user: User = Depends(get_current_user)) -> User:
    if user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admin only")
    return user
