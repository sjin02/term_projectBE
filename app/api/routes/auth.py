import firebase_admin
from firebase_admin import credentials, auth as firebase_auth
from google.oauth2 import id_token as google_id_token
from google.auth.transport import requests as google_requests

from fastapi import APIRouter, Depends, Request
from sqlmodel import Session
from redis import Redis
from typing import Optional

from app.core.config import settings
from app.core.docs import success_example, error_example
from app.core.errors import ErrorCode, http_error, success_response, STANDARD_ERROR_RESPONSES
from app.core.security import verify_password, create_token, decode_token
from app.db.models import User, UserStatus, UserRole
from app.deps.db import get_db
from app.deps.redis import get_redis
from app.deps.auth import get_current_user
from app.repositories import users as users_repo
from app.schemas.auth import (
    LoginRequest, TokenResponse, RefreshRequest, 
    FirebaseRequest, GoogleRequest
)

# Firebase 초기화 (생략 가능하나 기존 코드 유지)
if not firebase_admin._apps:
    try:
        cred = credentials.Certificate("app/core/firebase_key.json")
        firebase_admin.initialize_app(cred)
    except Exception as e:
        print(f"Firebase Init Failed: {e}")

router = APIRouter(
    prefix="/auth", 
    tags=["auth"],
    responses=STANDARD_ERROR_RESPONSES
)

ACCESS_MIN = 30
REFRESH_MIN = 60 * 24 * 7 

def _refresh_key(user_id: int) -> str:
    return f"refresh:{user_id}"

# [Helper] 로그인 공통 처리
def _process_social_login(request: Request, email: str, nickname: str, db: Session, rds: Optional[Redis]):
    user = users_repo.get_user_by_email(db, email)
    
    if not user:
        user = User(
            email=email, password_hash="", nickname=nickname,
            role=UserRole.USER, status=UserStatus.ACTIVE
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    elif user.deleted_at:
        raise http_error(403, ErrorCode.FORBIDDEN, "탈퇴한 계정입니다.")

    access = create_token(str(user.id), "access", ACCESS_MIN)
    refresh = create_token(str(user.id), "refresh", REFRESH_MIN)

    if rds:
        try:
            rds.setex(_refresh_key(user.id), REFRESH_MIN * 60, refresh)
        except Exception:
            pass

    return success_response(request, data={"access_token": access, "refresh_token": refresh}, message="로그인 성공")


@router.post(
    "/login", 
    response_model=TokenResponse,
    responses={
        **success_example(TokenResponse, message="로그인 성공"),
        401: error_example(401, ErrorCode.UNAUTHORIZED, "이메일 또는 비밀번호가 일치하지 않습니다."),
        403: error_example(403, ErrorCode.FORBIDDEN, "정지되었거나 탈퇴한 계정입니다."),
    }
)
def login(request: Request, body: LoginRequest, db: Session = Depends(get_db), rds: Optional[Redis] = Depends(get_redis)):
    user = users_repo.get_user_by_email(db, body.email)
    if not user or user.deleted_at or not verify_password(body.password, user.password_hash):
        raise http_error(401, ErrorCode.UNAUTHORIZED, "이메일/비번 불일치")
    if user.status in (UserStatus.BLOCKED, UserStatus.DELETED):
        raise http_error(403, ErrorCode.FORBIDDEN, "정지된 계정")

    access = create_token(str(user.id), "access", ACCESS_MIN)
    refresh = create_token(str(user.id), "refresh", REFRESH_MIN)

    if rds:
        try:
            rds.setex(_refresh_key(user.id), REFRESH_MIN * 60, refresh)
        except Exception:
            pass

    return success_response(request, data={"access_token": access, "refresh_token": refresh})


@router.post(
    "/refresh", 
    response_model=TokenResponse,
    responses={
        **success_example(TokenResponse, message="토큰 갱신 성공"),
        401: error_example(401, ErrorCode.UNAUTHORIZED, "유효하지 않거나 만료된 토큰입니다."),
    }
)
def refresh(request: Request, body: RefreshRequest, db: Session = Depends(get_db), rds: Optional[Redis] = Depends(get_redis)):
    try:
        payload = decode_token(body.refresh_token)
    except ValueError:
        raise http_error(401, ErrorCode.UNAUTHORIZED, "유효하지 않은 토큰")
        
    user_id = int(payload.get("sub", 0))
    if rds:
        saved = rds.get(_refresh_key(user_id))
        if not saved or saved != body.refresh_token:
            raise http_error(401, ErrorCode.UNAUTHORIZED, "만료된 토큰")

    new_access = create_token(str(user_id), "access", ACCESS_MIN)
    new_refresh = create_token(str(user_id), "refresh", REFRESH_MIN)
    
    if rds:
        rds.setex(_refresh_key(user_id), REFRESH_MIN * 60, new_refresh)

    return success_response(request, data={"access_token": new_access, "refresh_token": new_refresh})


@router.post(
    "/logout",
    responses={
        **success_example(message="로그아웃 완료"),
        401: error_example(401, ErrorCode.UNAUTHORIZED, "로그인이 필요합니다.")
    }
)
def logout(request: Request, user=Depends(get_current_user), rds: Optional[Redis] = Depends(get_redis)):
    if rds:
        try:
            rds.delete(_refresh_key(user.id))
        except Exception:
            pass
    return success_response(request, message="로그아웃 완료")


@router.post(
    "/firebase", 
    response_model=TokenResponse,
    responses={
        **success_example(TokenResponse, message="Firebase 로그인 성공"),
        401: error_example(401, ErrorCode.UNAUTHORIZED, "Firebase 토큰 검증 실패"),
    }
)
def firebase_login(request: Request, body: FirebaseRequest, db: Session = Depends(get_db), rds: Optional[Redis] = Depends(get_redis)):
    try:
        decoded_token = firebase_auth.verify_id_token(body.id_token)
        email = decoded_token.get("email")
        nickname = decoded_token.get("name") or email.split("@")[0]
    except Exception:
        raise http_error(401, ErrorCode.UNAUTHORIZED, "Firebase 토큰 오류")

    return _process_social_login(request, email, nickname, db, rds)


@router.post(
    "/google", 
    response_model=TokenResponse,
    responses={
        **success_example(TokenResponse, message="Google 로그인 성공"),
        401: error_example(401, ErrorCode.UNAUTHORIZED, "Google 토큰 검증 실패"),
    }
)
def google_login(request: Request, body: GoogleRequest, db: Session = Depends(get_db), rds: Optional[Redis] = Depends(get_redis)):
    try:
        CLIENT_ID = getattr(settings, "GOOGLE_CLIENT_ID", None) 
        PLAYGROUND_CLIENT_ID = "407408718192.apps.googleusercontent.com"
        
        id_info = google_id_token.verify_oauth2_token(
            body.id_token, 
            google_requests.Request(), 
            audience=[CLIENT_ID, PLAYGROUND_CLIENT_ID] 
        )
        
        email = id_info['email']
        nickname = id_info.get('name') or email.split("@")[0]
        
    except ValueError:
        raise http_error(401, ErrorCode.UNAUTHORIZED, "유효하지 않은 Google 토큰")

    return _process_social_login(request, email, nickname, db, rds)