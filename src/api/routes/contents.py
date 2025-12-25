from datetime import datetime, timezone
from fastapi import APIRouter, Depends, Request
from sqlmodel import Session

from src.core.errors import ErrorCode, http_error, success_response, STANDARD_ERROR_RESPONSES
from src.core.docs import success_example, error_example
from src.deps.auth import require_admin
from src.deps.db import get_db
from src.core import tmdb as tmdb_svc 
from src.repositories import contents as contents_repo
from src.repositories import genres as genres_repo
from src.schemas.contents import (
    ContentBase,
    ContentCreateRequest,
    ContentListResponse,
    ContentResponse,
    GenreBrief,
    TMDBGenre,
    TMDBMoviePayload,
    TopRatedItem,
    TopRatedResponse,
)

router = APIRouter(
    prefix="/contents",
    tags=["contents"],
    responses=STANDARD_ERROR_RESPONSES,
)


def _genres(db: Session, content_id: int) -> list[GenreBrief]:
    genres = contents_repo.get_content_genres(db, content_id)
    return [GenreBrief.model_validate(g) for g in genres]


def _tmdb_payload(raw: dict) -> TMDBMoviePayload:
    return TMDBMoviePayload(
        id=raw["id"],
        title=raw.get("title") or raw.get("original_title"),
        overview=raw.get("overview"),
        release_date=raw.get("release_date"),
        runtime=raw.get("runtime"),
        poster_path=raw.get("poster_path"),
        backdrop_path=raw.get("backdrop_path"),
        original_language=raw.get("original_language"),
        popularity=raw.get("popularity"),
        vote_average=raw.get("vote_average"),
        vote_count=raw.get("vote_count"),
        genres=[TMDBGenre(id=g["id"], name=g["name"]) for g in raw.get("genres", [])],
    )


def _content_base(db: Session, content) -> ContentBase:
    content_dict = {
        "id": content.id,
        "tmdb_id": content.tmdb_id,
        "title": content.title,
        "release_date": content.release_date,
        "runtime_minutes": content.runtime_minutes,
        "created_at": content.created_at,
        "updated_at": content.updated_at,
        "deleted_at": content.deleted_at,
        "genres": _genres(db, content.id),
    }
    return ContentBase.model_validate(content_dict)


@router.get(
    "",
    response_model=ContentListResponse,
    responses={**success_example(ContentListResponse)},
)
def list_contents(
    request: Request,
    q: str | None = None,
    genre_id: int | None = None,
    sort: str = "latest",
    page: int = 1,
    size: int = 20,
    db: Session = Depends(get_db),
):
    items, total = contents_repo.list_contents(
        db, q=q, genre_id=genre_id, sort=sort, page=page, size=size
    )
    payload = ContentListResponse(
        items=[_content_base(db, c) for c in items],
        page=page,
        size=size,
        total=total,
    )
    return success_response(
        request, message="콘텐츠 목록 조회 성공", data=payload.model_dump()
    )


@router.get(
    "/top-rated",
    response_model=TopRatedResponse,
    responses={
        **success_example(TopRatedResponse),
        400: error_example(400, ErrorCode.INVALID_QUERY_PARAM, "limit 값 오류")
    },
)
def top_rated(
    request: Request,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    if limit <= 0:
        raise http_error(
            400, ErrorCode.INVALID_QUERY_PARAM, "limit은 0보다 커야 합니다."
        )

    rows = contents_repo.top_rated(db, limit=limit)
    items = [
        TopRatedItem(
            content_id=row[0],
            title=row[1],
            avg_rating=float(row[2]),
            review_count=int(row[3]),
        )
        for row in rows
    ]
    return success_response(
        request,
        message="인기 콘텐츠 조회 성공",
        data=TopRatedResponse(items=items).model_dump(),
    )


@router.get(
    "/{content_id}",
    response_model=ContentResponse,
    responses={
        **success_example(ContentResponse),
        404: error_example(404, ErrorCode.RESOURCE_NOT_FOUND, "요청하신 콘텐츠를 찾을 수 없습니다."),
    },
)
def get_content(
    request: Request,
    content_id: int,
    db: Session = Depends(get_db)
):
    content = contents_repo.get_content(db, content_id)
    if not content:
        raise http_error(
            404, ErrorCode.RESOURCE_NOT_FOUND, "요청하신 콘텐츠를 찾을 수 없습니다.",
            details={"contentId": content_id}
        )
    
    tmdb_detail = tmdb_svc.fetch_movie_detail(content.tmdb_id)
    
    response = ContentResponse(
        **_content_base(db, content).model_dump(),
        tmdb=_tmdb_payload(tmdb_detail),
    )
    return success_response(
        request, message="콘텐츠 상세 조회 성공", data=response.model_dump()
    )


@router.post(
    "",
    status_code=201,
    dependencies=[Depends(require_admin)],
    response_model=ContentResponse,
    responses={
        **success_example(ContentResponse, message="콘텐츠 생성 완료", status_code=201),
        401: error_example(401, ErrorCode.UNAUTHORIZED, "로그인이 필요합니다."),
        403: error_example(403, ErrorCode.FORBIDDEN, "관리자 권한이 필요합니다."),
        409: error_example(409, ErrorCode.DUPLICATE_RESOURCE, "이미 존재하는 콘텐츠입니다."),
    },
)
def create_content(
    request: Request,
    body: ContentCreateRequest,
    db: Session = Depends(get_db)
):
    existing = contents_repo.get_content_by_tmdb_id_with_deleted(db, body.tmdb_id)
    
    if existing:
        if existing.deleted_at is None:
            raise http_error(
                409, ErrorCode.DUPLICATE_RESOURCE, "이미 존재하는 콘텐츠입니다.",
                details={"contentId": existing.id}
            )
        else:
            # 복구 로직
            tmdb_detail = tmdb_svc.fetch_movie_detail(body.tmdb_id)
            existing.title = tmdb_detail.get("title") or tmdb_detail.get("original_title")
            existing.release_date = tmdb_detail.get("release_date")
            existing.runtime_minutes = tmdb_detail.get("runtime")
            existing.deleted_at = None
            existing.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
            
            db.add(existing)
            db.commit()
            db.refresh(existing)
            
            genres = tmdb_detail.get("genres") or []
            active_genres = genres_repo.upsert_genres_from_tmdb(db, genres)
            genre_ids = [g.id for g in active_genres if g.deleted_at is None]
            contents_repo.set_content_genres(db, existing.id, genre_ids)

            response = ContentResponse(
                **_content_base(db, existing).model_dump(),
                tmdb=_tmdb_payload(tmdb_detail),
            )
            return success_response(
                request,
                status_code=201,
                message="삭제된 콘텐츠가 복구되었습니다.",
                data=response.model_dump(),
            )

    tmdb_detail = tmdb_svc.fetch_movie_detail(body.tmdb_id)
    genres = tmdb_detail.get("genres") or []
    active_genres = genres_repo.upsert_genres_from_tmdb(db, genres)
    genre_ids = [g.id for g in active_genres if g.deleted_at is None]

    content = contents_repo.create_content(
        db=db,
        tmdb_id=body.tmdb_id,
        title=tmdb_detail.get("title") or tmdb_detail.get("original_title"),
        release_date=tmdb_detail.get("release_date"),
        runtime_minutes=tmdb_detail.get("runtime"),
    )
    contents_repo.set_content_genres(db, content.id, genre_ids)

    response = ContentResponse(
        **_content_base(db, content).model_dump(),
        tmdb=_tmdb_payload(tmdb_detail),
    )
    return success_response(
        request,
        status_code=201,
        message="콘텐츠가 생성되었습니다.",
        data=response.model_dump(),
    )


@router.delete(
    "/{content_id}",
    dependencies=[Depends(require_admin)],
    responses={
        **success_example(message="콘텐츠 삭제 완료"),
        401: error_example(401, ErrorCode.UNAUTHORIZED, "로그인이 필요합니다."),
        403: error_example(403, ErrorCode.FORBIDDEN, "관리자 권한이 필요합니다."),
        404: error_example(404, ErrorCode.RESOURCE_NOT_FOUND, "요청하신 콘텐츠를 찾을 수 없습니다."),
    },
)
def delete_content(
    request: Request,
    content_id: int,
    db: Session = Depends(get_db)
):
    content = contents_repo.get_content(db, content_id)
    if not content:
        raise http_error(
            404, ErrorCode.RESOURCE_NOT_FOUND, "요청하신 콘텐츠를 찾을 수 없습니다.",
            details={"contentId": content_id}
        )

    now = datetime.now(timezone.utc).replace(tzinfo=None)
    content.deleted_at = now
    content.updated_at = now
    db.add(content)
    db.commit()

    return success_response(
        request, message="콘텐츠가 삭제되었습니다.", data={"contentId": content_id}
    )