from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.deps.db import get_db
from app.deps.auth import require_admin
from app.schemas.contents import (
    ContentCreateRequest, ContentUpdateRequest, ContentResponse,
    ContentListResponse, TopRatedResponse, TopRatedItem
)
from app.services import contents as contents_svc
from app.db.models import Content, Genre, ContentGenreLink

router = APIRouter(prefix="/api/v1/contents", tags=["contents"])

def _content_to_response(db: Session, c: Content) -> ContentResponse:
    # 장르 로드(간단 버전)
    stmt = (
        select(Genre.id, Genre.name)
        .join(ContentGenreLink, ContentGenreLink.genre_id == Genre.id)
        .where(ContentGenreLink.content_id == c.id, Genre.deleted_at.is_(None))
    )
    genres = [{"id": gid, "name": name} for gid, name in db.exec(stmt).all()]
    return ContentResponse(**c.model_dump(), genres=genres)

@router.get("", response_model=ContentListResponse)
def list_contents(
    q: str | None = None,
    genre_id: int | None = None,
    sort: str = "latest",
    page: int = 1,
    size: int = 20,
    db: Session = Depends(get_db),
):
    items, total = contents_svc.list_(db, q=q, genre_id=genre_id, sort=sort, page=page, size=size)
    return ContentListResponse(
        items=[_content_to_response(db, c) for c in items],
        page=page,
        size=size,
        total=total,
    )

@router.get("/{id}", response_model=ContentResponse)
def get_content(id: int, db: Session = Depends(get_db)):
    c = db.exec(select(Content).where(Content.id == id, Content.deleted_at.is_(None))).first()
    if not c:
        raise HTTPException(status_code=404, detail="Content not found")
    return _content_to_response(db, c)

@router.post("", response_model=ContentResponse, dependencies=[Depends(require_admin)])
def create_content(body: ContentCreateRequest, db: Session = Depends(get_db)):
    c = contents_svc.create(db, body)
    return _content_to_response(db, c)

@router.put("/{id}", response_model=ContentResponse, dependencies=[Depends(require_admin)])
def update_content(id: int, body: ContentUpdateRequest, db: Session = Depends(get_db)):
    c = contents_svc.update(db, id, body)
    return _content_to_response(db, c)

@router.delete("/{id}", dependencies=[Depends(require_admin)])
def delete_content(id: int, db: Session = Depends(get_db)):
    contents_svc.delete(db, id)
    return {"ok": True}

@router.get("/top-rated", response_model=TopRatedResponse)
def top_rated(limit: int = 10, db: Session = Depends(get_db)):
    rows = contents_svc.top_rated_(db, limit)
    items = [
        TopRatedItem(
            content_id=r[0],
            title=r[1],
            avg_rating=float(r[2]),
            review_count=int(r[3]),
        )
        for r in rows
    ]
    return TopRatedResponse(items=items)
