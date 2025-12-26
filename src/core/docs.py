from typing import Any, Dict, Type, Union
from pydantic import BaseModel

from src.core.errors import ErrorCode

def success_example(
    model: Type[BaseModel] | None = None,
    description: str = "성공",
    message: str = "성공",
    status_code: int = 200,
) -> Dict[str, Any]:
    """
    Swagger의 2xx 응답 예시를 생성합니다.
    실제 응답 포맷(timestamp, code, message, data)을 따릅니다.
    """
    data_schema = model.model_json_schema() if model else {}
    
    # Swagger 예시 구조 생성
    example_structure = {
        "timestamp": "2025-12-24T12:34:56Z",
        "path": "/request/path",
        "status": status_code,
        "code": ErrorCode.SUCCESS.value,
        "message": message,
        "data": data_schema.get("example") or {}, # 모델에 example이 있으면 사용
    }

    return {
        status_code: {
            "description": description,
            "content": {
                "application/json": {
                    "example": example_structure
                }
            },
        }
    }

def error_example(
    status_code: int,
    code: ErrorCode,
    message: str,
    description: str | None = None,
    details: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    """
    Swagger의 4xx, 5xx 에러 응답 예시를 생성합니다.
    """
    return {
        "description": description or message,
        "content": {
            "application/json": {
                "example": {
                    "timestamp": "2025-12-24T12:34:56Z",
                    "path": "/error/path",
                    "status": status_code,
                    "code": code.value,
                    "message": message,
                    "details": details or {},
                }
            }
        },
    }