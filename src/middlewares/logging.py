#요청 및 응답 시간을 기록하는 미들웨어

import time
from fastapi import Request
from src.core.logging import logger

async def logging_middleware(request: Request, call_next):
    start = time.perf_counter()
    try:
        response = await call_next(request)
        elapsed_ms = (time.perf_counter() - start) * 1000
        logger.info("%s %s -> %s (%.1fms)",
                    request.method, request.url.path, response.status_code, elapsed_ms)
        return response
    except Exception:
        elapsed_ms = (time.perf_counter() - start) * 1000
        # 스택트레이스 포함 (민감정보 제외)
        logger.exception("%s %s -> EXCEPTION (%.1fms)", request.method, request.url.path, elapsed_ms)
        raise