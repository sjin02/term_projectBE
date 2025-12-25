from datetime import datetime, timezone
from fastapi import APIRouter, Depends, Request
from sqlmodel import Session, select
from redis import Redis
from typing import Optional

from app.core.docs import success_example, error_example
from app.core.errors import ErrorCode, http_error, success_response, STANDARD_ERROR_RESPONSES
from app.core.security import hash_password, verify_password
from app.db.models import User, UserStatus, Review, Bookmark
from app.deps.db import get_db
from app.deps.redis import get_redis
from app.deps.auth import get_current_user
from app.repositories import users as users_repo
from app.schemas.users import (
    SignupRequest,
    UserMeResponse,
    UpdateMeRequest,
    ChangePasswordRequest,
)

router = APIRouter(
    prefix="/users", 
    tags=["users"],
    responses=STANDARD_ERROR_RESPONSES
)


def _refresh_key(user_id: int) -> str:
    return f"refresh:{user_id}"


@router.post(
    "/signup",
    response_model=UserMeResponse,
    responses={
        **success_example(UserMeResponse, message="회원가입 성공"),
        409: error_example(409, ErrorCode.DUPLICATE_RESOURCE, "이미 가입된 이메일입니다."),
    },
)
def signup(
    request: Request,
    body: SignupRequest,
    db: Session = Depends(get_db),
):
    if users_repo.get_user_by_email(db, body.email):
        raise http_error(409, ErrorCode.DUPLICATE_RESOURCE, "이미 가입된 이메일입니다.")

    user = User(
        email=body.email,
        password_hash=hash_password(body.password),
        nickname=body.nickname,
        status=UserStatus.ACTIVE,
    )
    created_user = users_repo.create_user(db, user)

    return success_response(
        request,
        data=created_user.model_dump(),
        message="회원가입이 완료되었습니다.",
    )


@router.get(
    "/me",
    response_model=UserMeResponse,
    responses={
        **success_example(UserMeResponse),
        401: error_example(401, ErrorCode.UNAUTHORIZED, "로그인이 필요합니다."),
    },
)
def me(request: Request, user=Depends(get_current_user)):
    return success_response(request, data=user.model_dump())


@router.put(
    "/me",
    response_model=UserMeResponse,
    responses={
        **success_example(UserMeResponse, message="정보 수정 완료"),
        401: error_example(401, ErrorCode.UNAUTHORIZED, "로그인이 필요합니다."),
    },
)
def update_me(
    request: Request,
    body: UpdateMeRequest,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    if body.nickname is not None:
        user.nickname = body.nickname
    
    user.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
    db.add(user)
    db.commit()
    db.refresh(user)

    return success_response(
        request,
        data=user.model_dump(),
        message="회원 정보가 수정되었습니다.",
    )


@router.patch(
    "/me/password",
    responses={
        **success_example(message="비밀번호 변경 완료"),
        400: error_example(400, ErrorCode.BAD_REQUEST, "현재 비밀번호가 일치하지 않습니다."),
        401: error_example(401, ErrorCode.UNAUTHORIZED, "로그인이 필요합니다."),
    },
)
def change_password(
    request: Request,
    body: ChangePasswordRequest,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    if not verify_password(body.current_password, user.password_hash):
        raise http_error(400, ErrorCode.BAD_REQUEST, "현재 비밀번호가 일치하지 않습니다.")

    user.password_hash = hash_password(body.new_password)
    user.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
    db.add(user)
    db.commit()

    return success_response(request, message="비밀번호가 변경되었습니다.", data={"ok": True})


@router.delete(
    "/me",
    responses={
        **success_example(message="회원 탈퇴 완료"),
        401: error_example(401, ErrorCode.UNAUTHORIZED, "로그인이 필요합니다.")
    },
)
def delete_me(
    request: Request,
    db: Session = Depends(get_db),
    rds: Optional[Redis] = Depends(get_redis),
    user=Depends(get_current_user),
):
    user.deleted_at = datetime.now(timezone.utc).replace(tzinfo=None)
    user.status = UserStatus.DELETED
    db.add(user)
    db.commit()

    if rds:
        try:
            rds.delete(_refresh_key(user.id))
        except Exception:
            pass

    return success_response(request, message="회원 탈퇴가 완료되었습니다.", data={"ok": True})


@router.get(
    "/me/reviews",
    responses={
        **success_example(description="내 리뷰 목록 조회"),
        401: error_example(401, ErrorCode.UNAUTHORIZED, "로그인이 필요합니다.")
    }
)
def my_reviews(
    request: Request,
    page: int = 1,
    size: int = 20,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    stmt = (
        select(Review)
        .where(Review.user_id == user.id)
        .order_by(Review.created_at.desc())
        .offset((page - 1) * size)
        .limit(size)
    )
    items = list(db.exec(stmt).all())
    return success_response(
        request,
        data={
            "page": page,
            "size": size,
            "items": [r.model_dump() for r in items],
        },
    )


@router.get(
    "/me/bookmarks",
    responses={
        **success_example(description="내 북마크 목록 조회"),
        401: error_example(401, ErrorCode.UNAUTHORIZED, "로그인이 필요합니다.")
    }
)
def my_bookmarks(
    request: Request,
    page: int = 1,
    size: int = 20,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    stmt = (
        select(Bookmark)
        .where(Bookmark.user_id == user.id)
        .order_by(Bookmark.created_at.desc())
        .offset((page - 1) * size)
        .limit(size)
    )
    items = list(db.exec(stmt).all())
    return success_response(
        request,
        data={
            "page": page,
            "size": size,
            "items": [b.model_dump() for b in items],
        },
    )