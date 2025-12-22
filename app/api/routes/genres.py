from datetime import datetime
from math import ceil

from fastapi import APIRouter, Depends, Query, Request
from sqlmodel import Session, select, func

from app.core.error_codes import ErrorCode
from app.core.exceptions import http_error
from app.core.responses import STANDARD_ERROR_RESPONSES, success_response
from app.db.models import Genre
from app.deps.auth import require_admin
from app.deps.db import get_db
from app.schemas.genres import (
    GenreCreateRequest,
    GenreListResponse,
    GenreResponse,
    GenreUpdateRequest,
)

router = APIRouter(
    prefix="/api/v1/genres",
    tags=["genres"],
    responses=STANDARD_ERROR_RESPONSES,
)


def _sort_clause(sort: str):
    allowed = {
        "createdAt": Genre.created_at,
        "name": Genre.name,
    }
    try:
        field, direction = sort.split(",")
    except ValueError:
        raise http_error(
            status_code=400,
            code=ErrorCode.INVALID_QUERY_PARAM,
            message="sort 형식은 field,DESC|ASC 이어야 합니다.",
        )
    if field not in allowed or direction.upper() not in ("ASC", "DESC"):
        raise http_error(
            status_code=400,
            code=ErrorCode.INVALID_QUERY_PARAM,
            message="지원하지 않는 정렬 필드 혹은 방향입니다.",
            details={"sort": sort},
        )
    column = allowed[field]
    return column.desc() if direction.upper() == "DESC" else column.asc()


@router.get("")
def list_genres(
    request: Request,
    page: int = Query(0, ge=0),
    size: int = Query(20, ge=1, le=50),
    sort: str = Query("createdAt,DESC"),
    keyword: str | None = Query(None, description="장르명 검색어"),
    created_from: datetime | None = Query(None, alias="createdFrom"),
    created_to: datetime | None = Query(None, alias="createdTo"),
    db: Session = Depends(get_db),
):
    stmt = select(Genre).where(Genre.deleted_at.is_(None))
    if keyword:
        stmt = stmt.where(Genre.name.ilike(f"%{keyword}%"))
    if created_from:
        stmt = stmt.where(Genre.created_at >= created_from)
    if created_to:
        stmt = stmt.where(Genre.created_at <= created_to)
    stmt = stmt.order_by(_sort_clause(sort))

    total = db.exec(select(func.count()).select_from(stmt.subquery())).one()
    items = db.exec(stmt.offset(page * size).limit(size)).all()

    payload = GenreListResponse(
        content=[GenreResponse.model_validate(item) for item in items],
        page=page,
        size=size,
        totalElements=int(total),
        totalPages=ceil(int(total) / size) if size else 0,
        sort=sort,
    )
    return success_response(
        request,
        message="Genres fetched",
        data=payload.model_dump(),
    )


@router.post("", status_code=201, dependencies=[Depends(require_admin)])
def create_genre(
    request: Request,
    body: GenreCreateRequest,
    db: Session = Depends(get_db),
):
    exists = db.exec(
        select(Genre).where(
            Genre.name == body.name,
            Genre.deleted_at.is_(None),
        )
    ).first()
    if exists:
        raise http_error(
            status_code=409,
            code=ErrorCode.DUPLICATE_RESOURCE,
            message="이미 존재하는 장르입니다.",
            details={"name": body.name},
        )

    genre = Genre(name=body.name)
    db.add(genre)
    db.commit()
    db.refresh(genre)

    return success_response(
        request,
        status_code=201,
        message="Genre created",
        data=GenreResponse.model_validate(genre).model_dump(),
    )


@router.patch(
    "/{genre_id}",
    dependencies=[Depends(require_admin)],
)
def update_genre(
    request: Request,
    genre_id: int,
    body: GenreUpdateRequest,
    db: Session = Depends(get_db),
):
    genre = db.get(Genre, genre_id)
    if not genre or genre.deleted_at is not None:
        raise http_error(
            status_code=404,
            code=ErrorCode.RESOURCE_NOT_FOUND,
            message="Genre not found",
            details={"genreId": genre_id},
        )
    if body.name:
        dup = db.exec(
            select(Genre).where(
                Genre.name == body.name,
                Genre.id != genre_id,
                Genre.deleted_at.is_(None),
            )
        ).first()
        if dup:
            raise http_error(
                status_code=409,
                code=ErrorCode.DUPLICATE_RESOURCE,
                message="이미 존재하는 장르명입니다.",
                details={"name": body.name},
            )
        genre.name = body.name

    db.add(genre)
    db.commit()
    db.refresh(genre)
    return success_response(
        request,
        message="Genre updated",
        data=GenreResponse.model_validate(genre).model_dump(),
    )


@router.delete(
    "/{genre_id}",
    dependencies=[Depends(require_admin)],
)
def delete_genre(
    request: Request,
    genre_id: int,
    db: Session = Depends(get_db),
):
    genre = db.get(Genre, genre_id)
    if not genre or genre.deleted_at is not None:
        raise http_error(
            status_code=404,
            code=ErrorCode.RESOURCE_NOT_FOUND,
            message="Genre not found",
            details={"genreId": genre_id},
        )

    genre.deleted_at = datetime.utcnow()
    db.add(genre)
    db.commit()
    return success_response(
        request,
        message="Genre deleted",
        data={"genreId": genre_id},
    )