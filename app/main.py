from fastapi import FastAPI
from app.core.config import settings
from app.api.routes import all_routers
from app.core.logging import setup_logging

from app.middlewares.logging import logging_middleware
from fastapi.middleware.cors import CORSMiddleware
from fastapi import HTTPException
from fastapi.exceptions import RequestValidationError
from app.core.errors import (
    http_exception_handler,
    unhandled_exception_handler,
    validation_exception_handler,
)

app = FastAPI(title="Movie API", version=settings.APP_VERSION)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 실제 배포때는 프론트 주소만 적는게 좋지만, 지금은 "*"로 모두 허용
    allow_credentials=True,
    allow_methods=["*"],  # GET, POST, PUT, DELETE 등 모든 방법 허용
    allow_headers=["*"],  # 모든 헤더 허용 (토큰 포함)
)
@app.on_event("startup")
def on_startup():
    setup_logging("INFO")


app.middleware("http")(logging_middleware)

app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(Exception, unhandled_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)


for r in all_routers:
    app.include_router(r)