from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional

from fastapi import HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.core.logging import logger

# ==========================================
# 1. Error Codes (표준 코드 15종)
# ==========================================

class ErrorCode(str, Enum):
    # 400
    BAD_REQUEST = "BAD_REQUEST"
    VALIDATION_FAILED = "VALIDATION_FAILED"
    INVALID_QUERY_PARAM = "INVALID_QUERY_PARAM"
    
    # 401
    UNAUTHORIZED = "UNAUTHORIZED"
    TOKEN_EXPIRED = "TOKEN_EXPIRED"
    
    # 403
    FORBIDDEN = "FORBIDDEN"
    
    # 404
    RESOURCE_NOT_FOUND = "RESOURCE_NOT_FOUND"
    USER_NOT_FOUND = "USER_NOT_FOUND"
    
    # 409
    DUPLICATE_RESOURCE = "DUPLICATE_RESOURCE"
    STATE_CONFLICT = "STATE_CONFLICT"
    
    # 422
    UNPROCESSABLE_ENTITY = "UNPROCESSABLE_ENTITY"
    
    # 429
    TOO_MANY_REQUESTS = "TOO_MANY_REQUESTS"
    
    # 500
    INTERNAL_SERVER_ERROR = "INTERNAL_SERVER_ERROR"
    DATABASE_ERROR = "DATABASE_ERROR"
    UNKNOWN_ERROR = "UNKNOWN_ERROR"
    
    # Success
    SUCCESS = "SUCCESS"


# 상태 코드별 기본 에러 코드 매핑
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
# 2. Response Helpers & Format
# ==========================================

def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

def success_response(
    request: Request,
    data: Any = None,
    *,
    status_code: int = 200,
    code: ErrorCode = ErrorCode.SUCCESS,
    message: str = "성공",  # 기본 메시지 한글화
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

# 이 기본 딕셔너리는 이제 문서용 헬퍼(docs.py)가 대체하므로 최소화하거나 삭제해도 됩니다.
# 호환성을 위해 남겨두되 한글로 변경합니다.
STANDARD_ERROR_RESPONSES = {
    500: {"description": "서버 내부 오류"}
}


# ==========================================
# 3. http_error (Custom Exception)
# ==========================================

def http_error(
    status_code: int,
    code: ErrorCode,
    message: str,
    details: dict | None = None,
) -> HTTPException:
    """
    모든 비즈니스 로직 에러는 이 함수를 사용하여 발생시킵니다.
    """
    return HTTPException(
        status_code=status_code,
        detail={
            "code": code.value,
            "message": message,
            "details": details or {},
        },
    )


# ==========================================
# 4. Exception Handlers
# ==========================================

def _extract_error(exc: HTTPException) -> tuple[ErrorCode, str, dict | None]:
    code: ErrorCode = resolve_error_code(exc.status_code)
    message = "오류가 발생했습니다."
    details: dict | None = None

    if isinstance(exc.detail, dict):
        # http_error로 생성된 예외
        message = exc.detail.get("message", message)
        details = exc.detail.get("details")
        if "code" in exc.detail:
            try:
                code = ErrorCode(exc.detail["code"])
            except ValueError:
                pass
    elif isinstance(exc.detail, str):
        message = exc.detail
    else:
        message = str(exc.detail)

    return code, message, details


async def http_exception_handler(request: Request, exc: HTTPException):
    # 로그 경고
    code, message, details = _extract_error(exc)
    logger.warning(f"{code.value} {request.method} {request.url.path} - {message}")
    
    return error_response(
        request,
        status_code=exc.status_code,
        code=code,
        message=message,
        details=details,
    )

async def validation_exception_handler(request: Request, exc: RequestValidationError):
    # 스키마 검증 실패 시 호출됨
    field_errors: dict[str, str] = {}
    for err in exc.errors():
        # loc: ('body', 'email') -> "body.email"
        loc = ".".join(str(x) for x in err.get("loc", []))
        msg = err.get("msg", "잘못된 값입니다.")
        field_errors[loc] = msg

    logger.warning(f"VALIDATION_FAILED {request.method} {request.url.path} - {field_errors}")

    return error_response(
        request,
        status_code=400,  # 422 대신 400 BAD_REQUEST 계열 사용 
        code=ErrorCode.VALIDATION_FAILED,
        message="입력값이 유효하지 않습니다.",
        details=field_errors,
    )

async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception(f"Unhandled Error {request.method} {request.url.path}")
    return error_response(
        request,
        status_code=500,
        code=ErrorCode.INTERNAL_SERVER_ERROR,
        message="서버 내부 오류가 발생했습니다.",
    )