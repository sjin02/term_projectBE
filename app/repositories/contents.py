from datetime import datetime
from typing import List, Optional, Tuple

from sqlmodel import Session, func, select

from app.db.models import Content, ContentGenreLink, Genre, Review


def create_content(
    db: Session,
    tmdb_id: int,
    title: str,
    release_date,
    runtime_minutes,
) -> Content:
    now = datetime.utcnow()
    content = Content(
        tmdb_id=tmdb_id,
        title=title,
        release_date=release_date,
        runtime_minutes=runtime_minutes,
        created_at=now,
        updated_at=now,
    )
    db.add(content)
    db.commit()
    db.refresh(content)
    return content


def set_content_genres(db: Session, content_id: int, genre_ids: List[int]) -> None:
    db.exec(
        ContentGenreLink.__table__.delete().where(
            ContentGenreLink.content_id == content_id
        )
    )
    for gid in genre_ids:
        db.add(ContentGenreLink(content_id=content_id, genre_id=gid))
    db.commit()


def list_contents(
    db: Session,
    q: Optional[str],
    genre_id: Optional[int],
    sort: str,
    page: int,
    size: int,
) -> Tuple[List[Content], int]:
    stmt = select(Content).where(Content.deleted_at.is_(None))
    if q:
        stmt = stmt.where(Content.title.ilike(f"%{q}%"))
    if genre_id:
        stmt = stmt.join(ContentGenreLink).where(ContentGenreLink.genre_id == genre_id)

    if sort == "latest":
        stmt = stmt.order_by(Content.created_at.desc())
    elif sort == "oldest":
        stmt = stmt.order_by(Content.created_at.asc())
    else:
        stmt = stmt.order_by(Content.id.desc())

    total = db.exec(select(func.count()).select_from(stmt.subquery())).one()
    items = list(db.exec(stmt.offset((page - 1) * size).limit(size)).all())
    return items, int(total)


def get_content(db: Session, content_id: int) -> Content | None:
    return db.exec(
        select(Content).where(Content.id == content_id, Content.deleted_at.is_(None))
    ).first()


def get_content_by_tmdb_id(db: Session, tmdb_id: int) -> Content | None:
    return db.exec(
        select(Content).where(Content.tmdb_id == tmdb_id, Content.deleted_at.is_(None))
    ).first()


def get_content_genres(db: Session, content_id: int) -> List[Genre]:
    stmt = (
        select(Genre)
        .join(ContentGenreLink, ContentGenreLink.genre_id == Genre.id)
        .where(
            ContentGenreLink.content_id == content_id,
            Genre.deleted_at.is_(None),
        )
    )
    return list(db.exec(stmt).all())


def top_rated(db: Session, limit: int = 10):
    avg_rating = func.avg(Review.rating).label("avg_rating")
    review_count = func.count(Review.id).label("review_count")

    stmt = (
        select(Content.id, Content.title, avg_rating, review_count)
        .join(Review, Review.content_id == Content.id)
        .where(Content.deleted_at.is_(None))
        .group_by(Content.id)
        .order_by(avg_rating.desc(), review_count.desc())
        .limit(limit)
    )
    return db.exec(stmt).all()
