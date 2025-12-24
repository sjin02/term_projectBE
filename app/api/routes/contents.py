from fastapi import APIRouter, Depends, Request
from sqlmodel import Session

from app.core.errors import ErrorCode, http_error, success_response, STANDARD_ERROR_RESPONSES
from app.deps.auth import require_admin
from app.deps.db import get_db
from app.repositories import contents as contents_repo
from app.schemas.contents import (
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
from app.services import contents as contents_svc

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
    return ContentBase.model_validate(
        {
            **content.model_dump(),
            "genres": _genres(db, content.id),
        }
    )


@router.get("")
def list_contents(
    request: Request,
    q: str | None = None,
    genre_id: int | None = None,
    sort: str = "latest",
    page: int = 1,
    size: int = 20,
    db: Session = Depends(get_db),
):
    items, total = contents_svc.list_(
        db, q=q, genre_id=genre_id, sort=sort, page=page, size=size
    )
    payload = ContentListResponse(
        items=[_content_base(db, c) for c in items],
        page=page,
        size=size,
        total=total,
    )
    return success_response(request, message="Contents fetched", data=payload.model_dump())


@router.get("/top-rated")
def top_rated(request: Request, limit: int = 10, db: Session = Depends(get_db)):
    if limit <= 0:
        raise http_error(
            status_code=400,
            code=ErrorCode.INVALID_QUERY_PARAM,
            message="limit은 0보다 커야 합니다.",
            details={"limit": limit},
        )
    rows = contents_svc.top_rated_(db, limit)
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
        message="Top 순위의 콘텐츠들이 조회되었습니다.",
        data=TopRatedResponse(items=items).model_dump(),
    )


@router.get("/{content_id}")
def get_content(request: Request, content_id: int, db: Session = Depends(get_db)):
    content, tmdb_detail = contents_svc.get_detail(db, content_id)
    response = ContentResponse(
        **_content_base(db, content).model_dump(),
        tmdb=_tmdb_payload(tmdb_detail),
    )
    return success_response(
        request,
        message="Content fetched",
        data=response.model_dump(),
    )


@router.post("", status_code=201, dependencies=[Depends(require_admin)])
def create_content(
    request: Request, body: ContentCreateRequest, db: Session = Depends(get_db)
):
    content, tmdb_detail = contents_svc.create(db, body.tmdb_id)
    response = ContentResponse(
        **_content_base(db, content).model_dump(),
        tmdb=_tmdb_payload(tmdb_detail),
    )
    return success_response(
        request,
        status_code=201,
        message="Content created",
        data=response.model_dump(),
    )


@router.delete("/{content_id}", dependencies=[Depends(require_admin)])
def delete_content(request: Request, content_id: int, db: Session = Depends(get_db)):
    contents_svc.delete(db, content_id)
    return success_response(
        request,
        message="Content deleted",
        data={"contentId": content_id},
    )
