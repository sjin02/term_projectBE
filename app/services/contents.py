from datetime import datetime, timezone
from fastapi import HTTPException
from sqlmodel import Session

from app.db.models import Content
from app.repositories.contents import (
    create_content,
    get_content,
    list_contents,
    get_genres_by_ids,
    set_content_genres,
    top_rated,
)

def create(db: Session, payload):
    genres = get_genres_by_ids(db, payload.genre_ids)
    if len(genres) != len(payload.genre_ids):
        raise HTTPException(status_code=400, detail="Invalid genre_ids")

    content = Content(
        title=payload.title,
        description=payload.description,
        release_year=payload.release_year,
        runtime_minutes=payload.runtime_minutes,
        created_at=datetime.now(timezone.utc).replace(tzinfo=None),
        updated_at=datetime.now(timezone.utc).replace(tzinfo=None),
    )
    content = create_content(db, content)
    set_content_genres(db, content.id, payload.genre_ids)
    return content

def update(db: Session, content_id: int, payload):
    content = get_content(db, content_id)
    if not content:
        raise HTTPException(status_code=404, detail="Content not found")

    if payload.title is not None:
        content.title = payload.title
    if payload.description is not None:
        content.description = payload.description
    if payload.release_year is not None:
        content.release_year = payload.release_year
    if payload.runtime_minutes is not None:
        content.runtime_minutes = payload.runtime_minutes

    if payload.genre_ids is not None:
        genres = get_genres_by_ids(db, payload.genre_ids)
        if len(genres) != len(payload.genre_ids):
            raise HTTPException(status_code=400, detail="Invalid genre_ids")
        set_content_genres(db, content.id, payload.genre_ids)

    content.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
    db.add(content)
    db.commit()
    db.refresh(content)
    return content

def delete(db: Session, content_id: int):
    content = get_content(db, content_id)
    if not content:
        raise HTTPException(status_code=404, detail="Content not found")
    content.deleted_at = datetime.now(timezone.utc).replace(tzinfo=None)
    db.add(content)
    db.commit()

def list_(db: Session, q, genre_id, sort, page, size):
    return list_contents(db, q=q, genre_id=genre_id, sort=sort, page=page, size=size)

def top_rated_(db: Session, limit: int):
    return top_rated(db, limit=limit)
