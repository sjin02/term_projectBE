from fastapi import HTTPException

from app.core.error_codes import ErrorCode


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
