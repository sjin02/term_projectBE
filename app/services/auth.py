# (login/refresh/logout + Redis refresh 저장)
from sqlmodel import Session
from redis import Redis
from typing import Optional
from app.core.errors import http_error, ErrorCode # 수정
from app.core.security import verify_password, create_token, decode_token
from app.repositories.users import get_user_by_email, get_user_by_id
from app.db.models import UserStatus


ACCESS_MIN = 30
REFRESH_MIN = 60 * 24 * 7  # 7 days

def _refresh_key(user_id: int) -> str:
    return f"refresh:{user_id}"


def login(db: Session, rds: Optional[Redis], email: str, password: str):
    user = get_user_by_email(db, email)
    if not user or user.deleted_at is not None:
        raise http_error(
            status_code=401,
            code=ErrorCode.UNAUTHORIZED,
            message="이메일 또는 비밀번호가 올바르지 않습니다."
        )
    
    if user.status == UserStatus.BLOCKED:
        raise http_error(
            status_code=403,
            code=ErrorCode.FORBIDDEN,
            message="정지된 계정입니다 관리자에게 문의하세요."
        )

    if not verify_password(password, user.password_hash):
        raise http_error(
            status_code=401,
            code=ErrorCode.UNAUTHORIZED,
            message="이메일 또는 비밀번호가 올바르지 않습니다."
        )

def refresh(db: Session, rds: Optional[Redis], refresh_token: str):
    try:
        payload = decode_token(refresh_token)
    except ValueError:
        raise http_error(
            status_code=401,
            code=ErrorCode.UNAUTHORIZED,
            message="유효하지 않은 refresh token"
        )

    if payload.get("type") != "refresh":
        raise http_error(
            status_code=401,
            code=ErrorCode.UNAUTHORIZED,
            message="Refresh token 필요"
        )

    user_id = int(payload.get("sub", 0))
    user = get_user_by_id(db, user_id)
    if not user or user.deleted_at is not None:
        raise http_error(
            status_code=404,
            code=ErrorCode.USER_NOT_FOUND,
            message="User not found")

    # Redis가 있으면 토큰 검증 (Whitelist), 없으면 생략
    if rds:
        try:
            saved = rds.get(_refresh_key(user_id))
            if not saved or saved != refresh_token:
                raise http_error(
                    status_code=401,
                    code=ErrorCode.UNAUTHORIZED,
                    message="Refresh token revoked")
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
