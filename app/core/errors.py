# 에러 발생 시 스택트레이스를 로깅하는 핸들러(민감정보 제외)
from fastapi import HTTPException, Request
from fastapi.exceptions import RequestValidationError

from app.core.error_codes import ErrorCode, resolve_error_code
from app.core.logging import logger
from app.core.responses import error_response


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
