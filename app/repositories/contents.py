from typing import Optional, List, Tuple
from sqlmodel import Session, select, func
from app.db.models import Content, Genre, ContentGenreLink, Review

def get_genres_by_ids(db: Session, ids: List[int]) -> List[Genre]:
    if not ids:
        return []
    return list(db.exec(select(Genre).where(Genre.id.in_(ids), Genre.deleted_at.is_(None))).all())

def create_content(db: Session, content: Content) -> Content:
    db.add(content)
    db.commit()
    db.refresh(content)
    return content

def set_content_genres(db: Session, content_id: int, genre_ids: List[int]) -> None:
    db.exec(
        ContentGenreLink.__table__.delete().where(ContentGenreLink.content_id == content_id)
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

    # sort
    if sort == "latest":
        stmt = stmt.order_by(Content.created_at.desc())
    elif sort == "oldest":
        stmt = stmt.order_by(Content.created_at.asc())
    else:
        # default
        stmt = stmt.order_by(Content.id.desc())

    total = db.exec(
        select(func.count()).select_from(stmt.subquery())
    ).one()

    items = list(db.exec(stmt.offset((page - 1) * size).limit(size)).all())
    return items, int(total)

def get_content(db: Session, content_id: int) -> Content | None:
    return db.exec(
        select(Content).where(Content.id == content_id, Content.deleted_at.is_(None))
    ).first()

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
