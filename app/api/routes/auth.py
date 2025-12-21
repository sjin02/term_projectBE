from fastapi import APIRouter, Depends
from sqlmodel import Session
from redis import Redis

from app.deps.db import get_db
from app.deps.redis import get_redis
from app.deps.auth import get_current_user
from app.schemas.auth import (
    LoginRequest, TokenResponse, RefreshRequest, LogoutResponse,
    FirebaseRequest, KakaoRequest
)
from app.services import auth as auth_svc

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])

@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, db: Session = Depends(get_db), rds: Redis = Depends(get_redis)):
    access, refresh = auth_svc.login(db, rds, body.email, body.password)
    return TokenResponse(access_token=access, refresh_token=refresh)

@router.post("/refresh", response_model=TokenResponse)
def refresh(body: RefreshRequest, db: Session = Depends(get_db), rds: Redis = Depends(get_redis)):
    access, refresh = auth_svc.refresh(db, rds, body.refresh_token)
    return TokenResponse(access_token=access, refresh_token=refresh)

@router.post("/logout", response_model=LogoutResponse)
def logout(user=Depends(get_current_user), rds: Redis = Depends(get_redis)):
    auth_svc.logout(rds, user.id)
    return LogoutResponse(ok=True)

@router.post("/firebase", response_model=TokenResponse)
def firebase_login(body: FirebaseRequest, db: Session = Depends(get_db), rds: Redis = Depends(get_redis)):
    # TODO: firebase-admin으로 body.id_token 검증 → email/uid 얻기
    # TODO: 유저 없으면 생성(소셜유저 정책 결정)
    raise NotImplementedError("Firebase login not implemented yet")

@router.post("/kakao", response_model=TokenResponse)
def kakao_login(body: KakaoRequest, db: Session = Depends(get_db), rds: Redis = Depends(get_redis)):
    # TODO: 카카오 access_token으로 사용자 정보 조회 → email/id 얻기
    # TODO: 유저 없으면 생성
    raise NotImplementedError("Kakao login not implemented yet")
