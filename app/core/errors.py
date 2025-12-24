from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional

from fastapi import HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.core.logging import logger

# ==========================================
# 1. Error Codes (from error_codes.py)
# ==========================================

class ErrorCode(str, Enum):
    BAD_REQUEST = "BAD_REQUEST"
    VALIDATION_FAILED = "VALIDATION_FAILED"
    INVALID_QUERY_PARAM = "INVALID_QUERY_PARAM"
    UNAUTHORIZED = "UNAUTHORIZED"
    TOKEN_EXPIRED = "TOKEN_EXPIRED"
    FORBIDDEN = "FORBIDDEN"
    RESOURCE_NOT_FOUND = "RESOURCE_NOT_FOUND"
    USER_NOT_FOUND = "USER_NOT_FOUND"
    DUPLICATE_RESOURCE = "DUPLICATE_RESOURCE"
    STATE_CONFLICT = "STATE_CONFLICT"
    UNPROCESSABLE_ENTITY = "UNPROCESSABLE_ENTITY"
    TOO_MANY_REQUESTS = "TOO_MANY_REQUESTS"
    INTERNAL_SERVER_ERROR = "INTERNAL_SERVER_ERROR"
    DATABASE_ERROR = "DATABASE_ERROR"
    UNKNOWN_ERROR = "UNKNOWN_ERROR"
    SUCCESS = "SUCCESS"


DEFAULT_ERROR_CODE_BY_STATUS = {
    400: ErrorCode.BAD_REQUEST,
    401: ErrorCode.UNAUTHORIZED,
    403: ErrorCode.FORBIDDEN,
    404: ErrorCode.RESOURCE_NOT_FOUND,
    409: ErrorCode.STATE_CONFLICT,
    422: ErrorCode.UNPROCESSABLE_ENTITY,
    429: ErrorCode.TOO_MANY_REQUESTS,
    500: ErrorCode.INTERNAL_SERVER_ERROR,
}


def resolve_error_code(status_code: int) -> ErrorCode:
    return DEFAULT_ERROR_CODE_BY_STATUS.get(status_code, ErrorCode.UNKNOWN_ERROR)


# ==========================================
# 2. Response Helpers (from responses.py)
# ==========================================

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


# ==========================================
# 3. Exception Helpers (from exceptions.py)
# ==========================================

def http_error(
    status_code: int,
    code: ErrorCode,
    message: str,
    details: dict | None = None,
) -> HTTPException:
    return HTTPException(
        status_code=status_code,
        detail={
            "code": code.value,
            "message": message,
            "details": details or {},
        },
    )


# ==========================================
# 4. Exception Handlers (original errors.py)
# ==========================================

def _extract_error(exc: HTTPException) -> tuple[ErrorCode, str, dict | None]:
    code: ErrorCode = resolve_error_code(exc.status_code)
    message = "Error"
    details: dict | None = None

    if isinstance(exc.detail, dict):
        detail_dict = exc.detail
        message = detail_dict.get("message", message)
        details = detail_dict.get("details")
        maybe_code = detail_dict.get("code")
        if maybe_code:
            try:
                code = ErrorCode(maybe_code)
            except ValueError:
                code = resolve_error_code(exc.status_code)
    elif isinstance(exc.detail, str):
        message = exc.detail
    else:
        message = str(exc.detail)

    return code, message, details


async def http_exception_handler(request: Request, exc: HTTPException):
    logger.warning(
        "HTTPException %s %s %s",
        request.method,
        request.url.path,
        exc.status_code,
    )
    code, message, details = _extract_error(exc)
    return error_response(
        request,
        status_code=exc.status_code,
        code=code,
        message=message,
        details=details,
    )


async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception(
        "Unhandled error %s %s",
        request.method,
        request.url.path,
    )
    return error_response(
        request,
        status_code=500,
        code=ErrorCode.INTERNAL_SERVER_ERROR,
        message="Internal Server Error",
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.warning(
        "Validation error %s %s",
        request.method,
        request.url.path,
    )
    field_errors: dict[str, str] = {}
    for err in exc.errors():
        loc = ".".join(str(x) for x in err.get("loc", []))
        field_errors[loc] = err.get("msg")

    return error_response(
        request,
        status_code=422,
        code=ErrorCode.VALIDATION_FAILED,
        message="Validation failed",
        details=field_errors,
    )