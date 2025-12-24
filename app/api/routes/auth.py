from fastapi import APIRouter, Depends, Request
from sqlmodel import Session
from redis import Redis
from typing import Optional

from app.core.config import settings
from app.core.docs import success_example, error_example
from app.core.errors import ErrorCode, http_error, success_response
from app.core.security import verify_password, create_token, decode_token
from app.db.models import UserStatus
from app.deps.db import get_db
from app.deps.redis import get_redis
from app.deps.auth import get_current_user
from app.repositories import users as users_repo
from app.schemas.auth import (
    LoginRequest,
    TokenResponse,
    RefreshRequest,
    LogoutResponse,
    FirebaseRequest,
    KakaoRequest,
)

router = APIRouter(prefix="/auth", tags=["auth"])

ACCESS_MIN = 30
REFRESH_MIN = 60 * 24 * 7  # 7일


def _refresh_key(user_id: int) -> str:
    return f"refresh:{user_id}"


@router.post(
    "/login",
    response_model=TokenResponse,
    responses={
        **success_example(TokenResponse, message="로그인 성공"),
        401: error_example(401, ErrorCode.UNAUTHORIZED, "이메일 또는 비밀번호가 올바르지 않습니다."),
        403: error_example(403, ErrorCode.FORBIDDEN, "정지된 계정입니다. 관리자에게 문의하세요."),
    },
)
def login(
    request: Request,
    body: LoginRequest,
    db: Session = Depends(get_db),
    rds: Optional[Redis] = Depends(get_redis),
):
    # 1. 사용자 조회
    user = users_repo.get_user_by_email(db, body.email)
    if not user or user.deleted_at is not None:
        raise http_error(
            401, ErrorCode.UNAUTHORIZED, "이메일 또는 비밀번호가 올바르지 않습니다."
        )

    # 2. 상태 체크
    if user.status in (UserStatus.BLOCKED, UserStatus.DELETED):
        raise http_error(
            403, ErrorCode.FORBIDDEN, "정지된 계정입니다. 관리자에게 문의하세요."
        )

    # 3. 비밀번호 검증
    if not verify_password(body.password, user.password_hash):
        raise http_error(
            401, ErrorCode.UNAUTHORIZED, "이메일 또는 비밀번호가 올바르지 않습니다."
        )

    # 4. 토큰 생성
    access = create_token(str(user.id), "access", ACCESS_MIN)
    refresh = create_token(str(user.id), "refresh", REFRESH_MIN)

    # 5. Redis 저장
    if rds:
        try:
            rds.setex(_refresh_key(user.id), REFRESH_MIN * 60, refresh)
        except Exception:
            pass

    return success_response(
        request,
        data={"access_token": access, "refresh_token": refresh},
        message="로그인 성공",
    )


@router.post(
    "/refresh",
    response_model=TokenResponse,
    responses={
        **success_example(TokenResponse, message="토큰 갱신 성공"),
        401: error_example(401, ErrorCode.UNAUTHORIZED, "유효하지 않거나 만료된 토큰입니다."),
        404: error_example(404, ErrorCode.USER_NOT_FOUND, "사용자를 찾을 수 없습니다."),
    },
)
def refresh(
    request: Request,
    body: RefreshRequest,
    db: Session = Depends(get_db),
    rds: Optional[Redis] = Depends(get_redis),
):
    # 1. 토큰 디코딩
    try:
        payload = decode_token(body.refresh_token)
    except ValueError:
        raise http_error(401, ErrorCode.UNAUTHORIZED, "유효하지 않은 토큰입니다.")

    if payload.get("type") != "refresh":
        raise http_error(401, ErrorCode.UNAUTHORIZED, "Refresh 토큰이 필요합니다.")

    # 2. 사용자 검증
    user_id = int(payload.get("sub", 0))
    user = users_repo.get_user_by_id(db, user_id)
    if not user or user.deleted_at is not None:
        raise http_error(404, ErrorCode.USER_NOT_FOUND, "사용자를 찾을 수 없습니다.")

    # 3. Redis 토큰 검증 (Whitelist)
    if rds:
        try:
            saved = rds.get(_refresh_key(user_id))
            if not saved or saved != body.refresh_token:
                raise http_error(
                    401, ErrorCode.UNAUTHORIZED, "만료되거나 취소된 토큰입니다."
                )
        except Exception:
            pass

    # 4. 새 토큰 발급
    new_access = create_token(str(user_id), "access", ACCESS_MIN)
    new_refresh = create_token(str(user_id), "refresh", REFRESH_MIN)

    if rds:
        try:
            rds.setex(_refresh_key(user_id), REFRESH_MIN * 60, new_refresh)
        except Exception:
            pass

    return success_response(
        request,
        data={"access_token": new_access, "refresh_token": new_refresh},
        message="토큰 갱신 성공",
    )


@router.post(
    "/logout",
    response_model=LogoutResponse,
    responses={
        **success_example(LogoutResponse, message="로그아웃 성공"),
    },
)
def logout(
    request: Request,
    user=Depends(get_current_user),
    rds: Optional[Redis] = Depends(get_redis),
):
    if rds:
        try:
            rds.delete(_refresh_key(user.id))
        except Exception:
            pass

    return success_response(request, message="로그아웃 되었습니다.", data={"ok": True})


@router.post("/firebase", status_code=501)
def firebase_login():
    raise http_error(501, ErrorCode.UNKNOWN_ERROR, "아직 구현되지 않은 기능입니다.")


@router.post("/google", status_code=501)
def kakao_login():
    raise http_error(501, ErrorCode.UNKNOWN_ERROR, "아직 구현되지 않은 기능입니다.")