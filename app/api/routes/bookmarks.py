from datetime import datetime
from math import ceil

from fastapi import APIRouter, Depends, Query, Request
from sqlmodel import Session, select, func

from app.core.errors import ErrorCode, http_error, success_response, STANDARD_ERROR_RESPONSES
from app.core.docs import success_example, error_example
from app.db.models import Bookmark, Content
from app.deps.auth import get_current_user
from app.deps.db import get_db
from app.schemas.bookmarks import (
    BookmarkCreateRequest,
    BookmarkItem,
    BookmarkListResponse,
)

router = APIRouter(
    prefix="/bookmarks",
    tags=["bookmarks"],
    responses=STANDARD_ERROR_RESPONSES,
)


def _sort_clause(sort: str):
    allowed = {
        "createdAt": Bookmark.created_at,
        "title": Content.title,
    }
    try:
        field, direction = sort.split(",")
    except ValueError:
        raise http_error(
            400, ErrorCode.INVALID_QUERY_PARAM, "정렬 형식은 field,DESC|ASC 여야 합니다."
        )

    if field not in allowed or direction.upper() not in ("ASC", "DESC"):
        raise http_error(
            400, ErrorCode.INVALID_QUERY_PARAM, "지원하지 않는 정렬 필드 혹은 방향입니다.",
            details={"sort": sort}
        )

    column = allowed[field]
    return column.desc() if direction.upper() == "DESC" else column.asc()


@router.post(
    "",
    status_code=201,
    responses={
        **success_example(BookmarkItem, status_code=201, message="북마크 추가 성공"),
        400: error_example(400, ErrorCode.VALIDATION_FAILED, "입력값이 올바르지 않습니다."),
        401: error_example(401, ErrorCode.UNAUTHORIZED, "로그인이 필요합니다."),
        404: error_example(404, ErrorCode.RESOURCE_NOT_FOUND, "콘텐츠를 찾을 수 없습니다."),
        409: error_example(409, ErrorCode.DUPLICATE_RESOURCE, "이미 찜한 콘텐츠입니다."),
        422: error_example(422, ErrorCode.UNPROCESSABLE_ENTITY, "요청 형식이 잘못되었습니다."),
    }
)
def create_bookmark(
    request: Request,
    body: BookmarkCreateRequest,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    content = db.get(Content, body.content_id)
    if not content or content.deleted_at is not None:
        raise http_error(
            404, ErrorCode.RESOURCE_NOT_FOUND, "요청하신 콘텐츠를 찾을 수 없습니다.",
            details={"contentId": body.content_id}
        )

    existing = db.exec(
        select(Bookmark).where(
            Bookmark.user_id == user.id,
            Bookmark.content_id == body.content_id,
        )
    ).first()
    if existing:
        raise http_error(
            409, ErrorCode.DUPLICATE_RESOURCE, "이미 북마크에 등록된 콘텐츠입니다.",
            details={"contentId": body.content_id}
        )

    bookmark = Bookmark(user_id=user.id, content_id=body.content_id)
    db.add(bookmark)
    db.commit()
    db.refresh(bookmark)

    item = BookmarkItem(
        content_id=bookmark.content_id,
        title=content.title,
        created_at=bookmark.created_at,
    )
    return success_response(
        request,
        status_code=201,
        message="북마크에 추가되었습니다.",
        data=item.model_dump(),
    )


@router.get(
    "",
    responses={
        **success_example(BookmarkListResponse, message="북마크 목록 조회 성공"),
        400: error_example(400, ErrorCode.INVALID_QUERY_PARAM, "검색 파라미터가 잘못되었습니다."),
        401: error_example(401, ErrorCode.UNAUTHORIZED, "로그인이 필요합니다."),
    }
)
def list_bookmarks(
    request: Request,
    page: int = Query(0, ge=0),
    size: int = Query(20, ge=1, le=50),
    sort: str = Query("createdAt,DESC"),
    keyword: str | None = Query(None, description="콘텐츠 제목 검색어"),
    date_from: datetime | None = Query(None, alias="dateFrom"),
    date_to: datetime | None = Query(None, alias="dateTo"),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    stmt = (
        select(Bookmark, Content)
        .join(Content, Content.id == Bookmark.content_id)
        .where(Bookmark.user_id == user.id)
    )

    if keyword:
        stmt = stmt.where(Content.title.ilike(f"%{keyword}%"))
    if date_from:
        stmt = stmt.where(Bookmark.created_at >= date_from)
    if date_to:
        stmt = stmt.where(Bookmark.created_at <= date_to)

    stmt = stmt.order_by(_sort_clause(sort))

    total = db.exec(select(func.count()).select_from(stmt.subquery())).one()
    rows = db.exec(stmt.offset(page * size).limit(size)).all()

    items = [
        BookmarkItem(
            content_id=bookmark.content_id,
            title=content.title,
            created_at=bookmark.created_at,
        )
        for bookmark, content in rows
    ]

    payload = BookmarkListResponse(
        content=items,
        page=page,
        size=size,
        totalElements=int(total),
        totalPages=ceil(int(total) / size) if size else 0,
        sort=sort,
    )
    return success_response(
        request,
        message="북마크 목록이 조회되었습니다.",
        data=payload.model_dump(),
    )


@router.delete(
    "/{content_id}",
    responses={
        **success_example(message="북마크 삭제 완료"),
        401: error_example(401, ErrorCode.UNAUTHORIZED, "로그인이 필요합니다."),
        404: error_example(404, ErrorCode.RESOURCE_NOT_FOUND, "북마크를 찾을 수 없습니다."),
    }
)
def delete_bookmark(
    request: Request,
    content_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    bookmark = db.exec(
        select(Bookmark).where(
            Bookmark.user_id == user.id,
            Bookmark.content_id == content_id,
        )
    ).first()
    if not bookmark:
        raise http_error(
            404, ErrorCode.RESOURCE_NOT_FOUND, "해당 콘텐츠가 북마크에 존재하지 않습니다.",
            details={"contentId": content_id}
        )

    db.delete(bookmark)
    db.commit()
    return success_response(
        request,
        message="북마크가 삭제되었습니다.",
        data={"contentId": content_id},
    )