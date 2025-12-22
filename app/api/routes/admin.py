from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from app.deps.db import get_db
from app.deps.auth import require_admin
from app.db.models import User

router = APIRouter(prefix="/api/v1/users", tags=["admin"])

# Admin 전용 사용자 관리 API

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