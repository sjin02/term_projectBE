from fastapi import APIRouter, Depends
from sqlmodel import Session, text
from app.db.session import get_db
from app.core.config import settings

router = APIRouter()

@router.get("/health")
def health_check(db: Session = Depends(get_db)):
    db.exec(text("SELECT 1"))

    return {
        "status": "ok",
        "version": settings.APP_VERSION,
        "build_time": settings.BUILD_TIME,
        "db": "connected",
    }
