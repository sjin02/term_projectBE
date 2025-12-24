from datetime import datetime, timezone
from fastapi import APIRouter, Depends, Query, Request
from sqlmodel import Session, select, func

from app.core.docs import success_example, error_example
from app.core.errors import ErrorCode, http_error, success_response, STANDARD_ERROR_RESPONSES
from app.deps.auth import require_admin
from app.deps.db import get_db
from app.db.models import User, UserRole, UserStatus
from app.schemas.users import UserMeResponse

# users.py와 경로가 겹치므로 주의 (users.py의 /me 등이 먼저 매칭되어야 함)
# 관리자 기능임을 명확히 하려면 prefix를 /api/v1/admin/users 로 변경하는 것도 고려 가능
router = APIRouter(
    prefix="/users",
    tags=["admin"],
    responses={
        **STANDARD_ERROR_RESPONSES,
        403: error_example(403, ErrorCode.FORBIDDEN, "관리자 권한이 필요합니다."),
    },
)


@router.get(
    "",
    dependencies=[Depends(require_admin)],
    responses={**success_example(description="전체 사용자 목록 조회")},
)
def list_users(
    request: Request,
    q: str | None = Query(None, description="이메일 검색"),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    stmt = select(User).where(User.deleted_at.is_(None))
    if q:
        stmt = stmt.where(User.email.ilike(f"%{q}%"))
    
    # 페이징 처리를 위한 전체 개수 조회
    total_count = db.exec(select(func.count()).select_from(stmt.subquery())).one()
    
    items = list(db.exec(stmt.offset((page - 1) * size).limit(size)).all())
    
    return success_response(
        request,
        message="사용자 목록을 조회했습니다.",
        data={
            "page": page,
            "size": size,
            "total": total_count,
            "items": [UserMeResponse.model_validate(u) for u in items]
        },
    )


@router.get(
    "/{user_id}",
    dependencies=[Depends(require_admin)],
    response_model=UserMeResponse,
    responses={
        **success_example(UserMeResponse),
        404: error_example(404, ErrorCode.USER_NOT_FOUND, "사용자를 찾을 수 없습니다."),
    },
)
def get_user(
    request: Request,
    user_id: int,
    db: Session = Depends(get_db),
):
    user = db.get(User, user_id)
    if not user or user.deleted_at is not None:
        raise http_error(
            404, ErrorCode.USER_NOT_FOUND, "사용자를 찾을 수 없습니다.",
            details={"userId": user_id}
        )
    return success_response(
        request,
        data=UserMeResponse.model_validate(user).model_dump()
    )


@router.patch(
    "/{user_id}/role",
    dependencies=[Depends(require_admin)],
    responses={
        **success_example(message="권한 변경 완료"),
        404: error_example(404, ErrorCode.USER_NOT_FOUND, "사용자를 찾을 수 없습니다."),
        400: error_example(400, ErrorCode.BAD_REQUEST, "잘못된 권한 값입니다."),
    },
)
def change_role(
    request: Request,
    user_id: int,
    role: str = Query(..., description="변경할 Role (USER, ADMIN)"),
    db: Session = Depends(get_db),
):
    user = db.get(User, user_id)
    if not user or user.deleted_at is not None:
        raise http_error(404, ErrorCode.USER_NOT_FOUND, "사용자를 찾을 수 없습니다.")

    # Enum 유효성 검사 (선택 사항)
    if role not in [r.value for r in UserRole]:
        raise http_error(400, ErrorCode.BAD_REQUEST, f"허용되지 않는 Role입니다: {role}")

    user.role = role
    db.add(user)
    db.commit()
    
    return success_response(request, message="사용자 권한이 변경되었습니다.", data={"userId": user_id, "role": role})


@router.patch(
    "/{user_id}/status",
    dependencies=[Depends(require_admin)],
    responses={
        **success_example(message="상태 변경 완료"),
        404: error_example(404, ErrorCode.USER_NOT_FOUND, "사용자를 찾을 수 없습니다."),
        400: error_example(400, ErrorCode.BAD_REQUEST, "잘못된 상태 값입니다."),
    },
)
def change_status(
    request: Request,
    user_id: int,
    status: str = Query(..., description="변경할 Status (ACTIVE, BLOCKED)"),
    db: Session = Depends(get_db),
):
    user = db.get(User, user_id)
    if not user or user.deleted_at is not None:
        raise http_error(404, ErrorCode.USER_NOT_FOUND, "사용자를 찾을 수 없습니다.")

    # Enum 유효성 검사
    if status not in [s.value for s in UserStatus]:
        raise http_error(400, ErrorCode.BAD_REQUEST, f"허용되지 않는 Status입니다: {status}")

    user.status = status
    db.add(user)
    db.commit()
    
    return success_response(request, message="사용자 상태가 변경되었습니다.", data={"userId": user_id, "status": status})


@router.delete(
    "/{user_id}",
    dependencies=[Depends(require_admin)],
    responses={
        **success_example(message="강제 탈퇴 처리 완료"),
        404: error_example(404, ErrorCode.USER_NOT_FOUND, "사용자를 찾을 수 없습니다."),
    },
)
def force_delete(
    request: Request,
    user_id: int,
    db: Session = Depends(get_db),
):
    user = db.get(User, user_id)
    if not user:
        raise http_error(404, ErrorCode.USER_NOT_FOUND, "사용자를 찾을 수 없습니다.")

    # 이미 삭제된 유저인지 체크할 수도 있음
    if user.deleted_at:
         raise http_error(409, ErrorCode.STATE_CONFLICT, "이미 삭제된 사용자입니다.")

    user.deleted_at = datetime.now(timezone.utc).replace(tzinfo=None)
    user.status = UserStatus.DELETED
    db.add(user)
    db.commit()
    
    return success_response(request, message="사용자를 강제 탈퇴 처리했습니다.", data={"userId": user_id})