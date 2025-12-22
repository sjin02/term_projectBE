from typing import List

from sqlmodel import Session

from app.db.models import Genre
from app.repositories import genres as genres_repo
from app.services import tmdb as tmdb_svc


def sync_from_tmdb(db: Session) -> List[Genre]:
    tmdb_genres = tmdb_svc.fetch_genre_list()
    active_genres = genres_repo.upsert_genres_from_tmdb(db, tmdb_genres)
    genres_repo.soft_delete_missing(db, [g["id"] for g in tmdb_genres])
    return active_genres


def ensure_genres_from_tmdb_payload(db: Session, tmdb_genres: list[dict]) -> List[int]:
    if not tmdb_genres:
        return []
    active = genres_repo.upsert_genres_from_tmdb(db, tmdb_genres)
    return [g.id for g in active if g.deleted_at is None]


def list_active(db: Session) -> List[Genre]:
    return genres_repo.list_active_genres(db)
