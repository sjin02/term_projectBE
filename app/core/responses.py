from datetime import datetime, timezone
from typing import Any, Optional

from fastapi import Request
from fastapi.responses import JSONResponse

from app.core.error_codes import ErrorCode


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def success_response(
    request: Request,
    data: Any = None,
    *,
    status_code: int = 200,
    code: ErrorCode = ErrorCode.SUCCESS,
    message: str = "OK",
) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "timestamp": _utc_now_iso(),
            "path": request.url.path,
            "status": status_code,
            "code": code.value,
            "message": message,
            "data": data,
        },
    )


def error_response(
    request: Request,
    *,
    status_code: int,
    code: ErrorCode,
    message: str,
    details: Optional[dict] = None,
) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "timestamp": _utc_now_iso(),
            "path": request.url.path,
            "status": status_code,
            "code": code.value,
            "message": message,
            "details": details or {},
        },
    )

STANDARD_ERROR_RESPONSES = {
    400: {
        "description": "잘못된 요청",
        "content": {
            "application/json": {
                "example": {
                    "timestamp": "2025-03-05T12:34:56Z",
                    "path": "/api/v1/example",
                    "status": 400,
                    "code": ErrorCode.BAD_REQUEST.value,
                    "message": "요청 형식이 올바르지 않음",
                    "details": {},
                }
            }
        },
    },
    401: {
        "description": "인증 실패",
        "content": {
            "application/json": {
                "example": {
                    "timestamp": "2025-03-05T12:34:56Z",
                    "path": "/api/v1/example",
                    "status": 401,
                    "code": ErrorCode.UNAUTHORIZED.value,
                    "message": "인증 토큰이 필요합니다.",
                    "details": {},
                }
            }
        },
    },
    403: {
        "description": "권한 없음",
        "content": {
            "application/json": {
                "example": {
                    "timestamp": "2025-03-05T12:34:56Z",
                    "path": "/api/v1/example",
                    "status": 403,
                    "code": ErrorCode.FORBIDDEN.value,
                    "message": "접근 권한이 없습니다.",
                    "details": {},
                }
            }
        },
    },
    404: {
        "description": "리소스를 찾을 수 없음",
        "content": {
            "application/json": {
                "example": {
                    "timestamp": "2025-03-05T12:34:56Z",
                    "path": "/api/v1/example",
                    "status": 404,
                    "code": ErrorCode.RESOURCE_NOT_FOUND.value,
                    "message": "요청한 리소스를 찾을 수 없습니다.",
                    "details": {},
                }
            }
        },
    },
    422: {
        "description": "유효성 검증 실패",
        "content": {
            "application/json": {
                "example": {
                    "timestamp": "2025-03-05T12:34:56Z",
                    "path": "/api/v1/example",
                    "status": 422,
                    "code": ErrorCode.VALIDATION_FAILED.value,
                    "message": "필드 유효성 검사 실패",
                    "details": {"field": "에러 메시지"},
                }
            }
        },
    },
    500: {
        "description": "서버 에러",
        "content": {
            "application/json": {
                "example": {
                    "timestamp": "2025-03-05T12:34:56Z",
                    "path": "/api/v1/example",
                    "status": 500,
                    "code": ErrorCode.INTERNAL_SERVER_ERROR.value,
                    "message": "Internal Server Error",
                    "details": {},
                }
            }
        },
    },
}
