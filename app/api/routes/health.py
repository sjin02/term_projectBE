import time
from datetime import timedelta
from fastapi import APIRouter, Depends, Request
from sqlmodel import Session, text

from app.deps.db import get_db
from app.core.config import settings
from app.core.docs import success_example
from app.core.errors import success_response

router = APIRouter(tags=["system"])

# 서버 시작 시간 기록
START_TIME = time.time()

@router.get(
    "/health",
    responses={**success_example(message="시스템 상태 정상")}
)
def health_check(request: Request, db: Session = Depends(get_db)):
    # 1. DB 연결 확인
    db.exec(text("SELECT 1"))
    
    # 2. 런타임(Uptime) 계산
    uptime_seconds = int(time.time() - START_TIME)
    uptime_str = str(timedelta(seconds=uptime_seconds))

    # 3. Request 객체를 반드시 전달해야 함
    return success_response(
        request, 
        message="System is healthy",
        data={
            "status": "ok",
            "version": settings.APP_VERSION,
            "build_time": settings.BUILD_TIME,
            "uptime": uptime_str,
            "uptime_seconds": uptime_seconds,
            "db": "connected",
        }
    )