from datetime import datetime
from typing import Optional, Tuple

from sqlmodel import Session

from app.core.errors import ErrorCode, http_error
from app.db.models import Content
from app.repositories import contents as contents_repo
from app.services import genres as genres_svc
from app.services import tmdb as tmdb_svc


def create(db: Session, tmdb_id: int) -> Tuple[Content, dict]:
    exists = contents_repo.get_content_by_tmdb_id(db, tmdb_id)
    if exists:
        raise http_error(
            status_code=409,
            code=ErrorCode.DUPLICATE_RESOURCE,
            message="Content already exists",
            details={"contentId": exists.id, "tmdbId": tmdb_id},
        )

    tmdb_detail = tmdb_svc.fetch_movie_detail(tmdb_id)
    genres = tmdb_detail.get("genres") or []
    genre_ids = genres_svc.ensure_genres_from_tmdb_payload(db, genres)
    content = contents_repo.create_content(
        db=db,
        tmdb_id=tmdb_id,
        title=tmdb_detail.get("title") or tmdb_detail.get("original_title"),
        release_date=tmdb_detail.get("release_date"),
        runtime_minutes=tmdb_detail.get("runtime"),
    )
    contents_repo.set_content_genres(db, content.id, genre_ids)
    return content, tmdb_detail


def get_detail(db: Session, content_id: int) -> Tuple[Content, dict]:
    content = contents_repo.get_content(db, content_id)
    if not content:
        raise http_error(
            status_code=404,
            code=ErrorCode.RESOURCE_NOT_FOUND,
            message="Content not found",
            details={"contentId": content_id},
        )
    tmdb_detail = tmdb_svc.fetch_movie_detail(content.tmdb_id)
    return content, tmdb_detail


def delete(db: Session, content_id: int) -> None:
    content = contents_repo.get_content(db, content_id)
    if not content:
        raise http_error(
            status_code=404,
            code=ErrorCode.RESOURCE_NOT_FOUND,
            message="Content not found",
            details={"contentId": content_id},
        )
    now = datetime.utcnow()
    content.deleted_at = now
    content.updated_at = now
    db.add(content)
    db.commit()


def list_(
    db: Session,
    q: Optional[str],
    genre_id: Optional[int],
    sort: str,
    page: int,
    size: int,
):
    return contents_repo.list_contents(
        db,
        q=q,
        genre_id=genre_id,
        sort=sort,
        page=page,
        size=size,
    )


def top_rated_(db: Session, limit: int):
    return contents_repo.top_rated(db, limit=limit)
