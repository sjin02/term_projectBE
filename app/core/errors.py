# 에러 발생 시 스택트레이스를 로깅하는 핸들러(민감정보 제외)
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from app.core.logging import logger

async def http_exception_handler(request: Request, exc: HTTPException):
    logger.warning(
        "HTTPException %s %s %s",
        request.method,
        request.url.path,
        exc.status_code,
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )


async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception(
        "Unhandled error %s %s",
        request.method,
        request.url.path,
    )
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal Server Error"},
    )
