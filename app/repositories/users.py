from sqlmodel import Session, select
from app.db.models import User

def get_user_by_email(db: Session, email: str) -> User | None:
    return db.exec(select(User).where(User.email == email)).first()

def get_user_by_id(db: Session, user_id: int) -> User | None:
    return db.exec(select(User).where(User.id == user_id)).first()

def create_user(db: Session, user: User) -> User:
    db.add(user)
    db.commit()
    db.refresh(user)
    return user