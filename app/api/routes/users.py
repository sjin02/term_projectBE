from fastapi import APIRouter, Depends
from sqlmodel import Session, select
from redis import Redis

from app.deps.db import get_db
from app.deps.redis import get_redis
from app.deps.auth import get_current_user, require_admin
from app.schemas.users import (
    SignupRequest, UserMeResponse, UpdateMeRequest, ChangePasswordRequest
)
from app.services import users as users_svc
from app.services import auth as auth_svc
from app.db.models import User, Review, Bookmark, WatchHistory

router = APIRouter(prefix="/api/v1/users", tags=["users"])

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

@router.get("/me/watch-history")
def my_watch_history(page: int = 1, size: int = 20, db: Session = Depends(get_db), user=Depends(get_current_user)):
    stmt = (
        select(WatchHistory)
        .where(WatchHistory.user_id == user.id)
        .order_by(WatchHistory.created_at.desc())
        .offset((page - 1) * size)
        .limit(size)
    )
    items = list(db.exec(stmt).all())
    return {"page": page, "size": size, "items": [w.model_dump() for w in items]}

@router.get("/me/watch-time")
def my_watch_time(db: Session = Depends(get_db), user=Depends(get_current_user)):
    # 간단 합산(파이썬) - 나중에 SQL SUM으로 최적화해도 됨
    items = list(db.exec(select(WatchHistory).where(WatchHistory.user_id == user.id)).all())
    total = sum(w.watched_minutes for w in items)
    return {"total_minutes": total}

# ===== ADMIN =====

@router.get("", dependencies=[Depends(require_admin)])
def list_users(q: str | None = None, page: int = 1, size: int = 20, db: Session = Depends(get_db)):
    stmt = select(User).where(User.deleted_at.is_(None))
    if q:
        stmt = stmt.where(User.email.ilike(f"%{q}%"))
    items = list(db.exec(stmt.offset((page - 1) * size).limit(size)).all())
    return {"page": page, "size": size, "items": [u.model_dump() for u in items]}

@router.get("/{id}", dependencies=[Depends(require_admin)])
def get_user(id: int, db: Session = Depends(get_db)):
    user = db.get(User, id)
    if not user or user.deleted_at is not None:
        return {"error": "not found"}
    return user.model_dump()

@router.patch("/{id}/role", dependencies=[Depends(require_admin)])
def change_role(id: int, role: str, db: Session = Depends(get_db)):
    user = db.get(User, id)
    if not user or user.deleted_at is not None:
        return {"error": "not found"}
    user.role = role
    db.add(user)
    db.commit()
    return {"ok": True}

@router.patch("/{id}/status", dependencies=[Depends(require_admin)])
def change_status(id: int, status: str, db: Session = Depends(get_db)):
    user = db.get(User, id)
    if not user or user.deleted_at is not None:
        return {"error": "not found"}
    user.status = status
    db.add(user)
    db.commit()
    return {"ok": True}

@router.delete("/{id}", dependencies=[Depends(require_admin)])
def force_delete(id: int, db: Session = Depends(get_db)):
    user = db.get(User, id)
    if not user:
        return {"error": "not found"}
    user.deleted_at = __import__("datetime").datetime.utcnow()
    user.status = "DELETED"
    db.add(user)
    db.commit()
    return {"ok": True}
