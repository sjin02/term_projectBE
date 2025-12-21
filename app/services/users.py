from datetime import datetime, timezone
from fastapi import HTTPException
from sqlmodel import Session, select

from app.core.security import hash_password, verify_password
from app.repositories.users import get_user_by_email, create_user
from app.db.models import User, UserStatus

def signup(db: Session, email: str, password: str, nickname: str) -> User:
    if get_user_by_email(db, email):
        raise HTTPException(status_code=409, detail="Email already exists")

    user = User(
        email=email,
        password_hash=hash_password(password),
        nickname=nickname,
        status=UserStatus.ACTIVE,
    )
    return create_user(db, user)

def update_me(db: Session, user: User, nickname: str | None) -> User:
    if nickname is not None:
        user.nickname = nickname
    user.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def change_password(db: Session, user: User, current_password: str, new_password: str) -> None:
    if not verify_password(current_password, user.password_hash):
        raise HTTPException(status_code=400, detail="Wrong password")
    user.password_hash = hash_password(new_password)
    user.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
    db.add(user)
    db.commit()

def soft_delete_user(db: Session, user: User) -> None:
    user.deleted_at = datetime.now(timezone.utc).replace(tzinfo=None)
    user.status = UserStatus.DELETED
    db.add(user)
    db.commit()
