from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from src.core.config import settings
from src.api.routes import all_routers
from src.core.logging import setup_logging
from src.middlewares.logging import logging_middleware
from fastapi import HTTPException
from fastapi.exceptions import RequestValidationError
from src.core.errors import (
    http_exception_handler,
    unhandled_exception_handler,
    validation_exception_handler,
    rate_limit_handler,
)

# 1. Rate Limiter 설정 (IP 기준, 분당 100회 제한)
limiter = Limiter(key_func=get_remote_address, default_limits=["100/minute"])

app = FastAPI(title="Movie API", version=settings.APP_VERSION)
# 2. State에 limiter 저장 (라우터에서 사용 가능하도록)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

@app.on_event("startup")
def on_startup():
    setup_logging("INFO")

# 3. CORS 설정 (배포 주소 및 주요 로컬 환경 명시)
origins = [
    "http://113.198.66.75:10093",  # [중요] 실제 배포 주소
    "http://localhost",             # 로컬 (기본 포트)
    "http://localhost:3000",        # 로컬 프론트엔드 (React/Vue 등)
    "http://localhost:8000",        # 로컬 백엔드/Swagger
    "http://127.0.0.1:8000",        # 로컬 루프백 IP
    # 프론트엔드 만들면 이곳에 프론트엔드 배포 주소 추가
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,      # 명시된 도메인만 허용 (보안 강화)
    # allow_origins=["*"],      # (참고) 테스트 중 모든 곳에서 접속 허용하려면 위 대신 사용
    allow_credentials=True,
    allow_methods=["*"],        # 모든 HTTP Method 허용 (GET, POST, etc.)
    allow_headers=["*"],        # 모든 Header 허용
)

app.middleware("http")(logging_middleware)

app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(Exception, unhandled_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(RateLimitExceeded, rate_limit_handler)

for r in all_routers:
    app.include_router(r)