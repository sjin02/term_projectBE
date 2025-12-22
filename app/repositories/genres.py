from datetime import datetime
from typing import Iterable, List, Sequence

from sqlmodel import Session, select

from app.db.models import Genre


def upsert_genres_from_tmdb(
    db: Session, tmdb_genres: Iterable[dict]
) -> List[Genre]:
    """
    Ensure every TMDB genre exists in the DB.
    Returns the active Genre rows corresponding to the provided TMDB genres.
    """
    tmdb_genres = list(tmdb_genres)
    tmdb_ids = [g["id"] for g in tmdb_genres]
    current = {
        g.tmdb_genre_id: g
        for g in db.exec(select(Genre).where(Genre.tmdb_genre_id.in_(tmdb_ids))).all()
    }
    result: List[Genre] = []
    now = datetime.utcnow()

    for tmdb_genre in tmdb_genres:
        gid = tmdb_genre["id"]
        name = tmdb_genre["name"]
        if gid in current:
            genre = current[gid]
            genre.name = name
            genre.deleted_at = None
        else:
            genre = Genre(tmdb_genre_id=gid, name=name, created_at=now)
        db.add(genre)
        db.flush()
        result.append(genre)

    db.commit()
    for genre in result:
        db.refresh(genre)
    return result


def soft_delete_missing(db: Session, tmdb_ids: Sequence[int]) -> None:
    """Mark genres missing from TMDB list as deleted."""
    now = datetime.utcnow()
    if not tmdb_ids:
        stale = db.exec(select(Genre).where(Genre.deleted_at.is_(None))).all()
    else:
        stale = db.exec(
            select(Genre).where(
                ~Genre.tmdb_genre_id.in_(tmdb_ids),
                Genre.deleted_at.is_(None),
            )
        ).all()
    for genre in stale:
        genre.deleted_at = now
        db.add(genre)
    if stale:
        db.commit()


def list_active_genres(db: Session) -> List[Genre]:
    return list(db.exec(select(Genre).where(Genre.deleted_at.is_(None))).all())
