from fastapi import APIRouter, Depends
from sqlmodel import Session, select
from redis import Redis

from app.deps.db import get_db
from app.deps.redis import get_redis
from app.deps.auth import get_current_user
from app.schemas.users import (
    SignupRequest, UserMeResponse, UpdateMeRequest, ChangePasswordRequest
)
from app.services import users as users_svc
from app.services import auth as auth_svc
from app.db.models import User, Review, Bookmark

router = APIRouter(prefix="/users", tags=["users"])

@router.post("/signup", response_model=UserMeResponse)
def signup(body: SignupRequest, db: Session = Depends(get_db)):
    user = users_svc.signup(db, body.email, body.password, body.nickname)
    return UserMeResponse(**user.model_dump())

@router.get("/me", response_model=UserMeResponse)
def me(user=Depends(get_current_user)):
    return UserMeResponse(**user.model_dump())

@router.put("/me", response_model=UserMeResponse)
def update_me(body: UpdateMeRequest, db: Session = Depends(get_db), user=Depends(get_current_user)):
    user = users_svc.update_me(db, user, body.nickname)
    return UserMeResponse(**user.model_dump())

@router.patch("/me/password")
def change_password(body: ChangePasswordRequest, db: Session = Depends(get_db), user=Depends(get_current_user)):
    users_svc.change_password(db, user, body.current_password, body.new_password)
    return {"ok": True}

@router.delete("/me")
def delete_me(db: Session = Depends(get_db), rds: Redis = Depends(get_redis), user=Depends(get_current_user)):
    users_svc.soft_delete_user(db, user)
    auth_svc.logout(rds, user.id)  # refresh revoke
    return {"ok": True}

@router.get("/me/reviews")
def my_reviews(page: int = 1, size: int = 20, db: Session = Depends(get_db), user=Depends(get_current_user)):
    stmt = (
        select(Review)
        .where(Review.user_id == user.id)
        .order_by(Review.created_at.desc())
        .offset((page - 1) * size)
        .limit(size)
    )
    items = list(db.exec(stmt).all())
    return {"page": page, "size": size, "items": [r.model_dump() for r in items]}

@router.get("/me/bookmarks")
def my_bookmarks(page: int = 1, size: int = 20, db: Session = Depends(get_db), user=Depends(get_current_user)):
    stmt = (
        select(Bookmark)
        .where(Bookmark.user_id == user.id)
        .order_by(Bookmark.created_at.desc())
        .offset((page - 1) * size)
        .limit(size)
    )
    items = list(db.exec(stmt).all())
    return {"page": page, "size": size, "items": [b.model_dump() for b in items]}
