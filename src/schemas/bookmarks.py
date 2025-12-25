from datetime import datetime

from pydantic import BaseModel, Field


class BookmarkCreateRequest(BaseModel):
    content_id: int = Field(..., gt=0)


class BookmarkItem(BaseModel):
    content_id: int
    title: str
    created_at: datetime


class BookmarkListResponse(BaseModel):
    content: list[BookmarkItem]
    page: int
    size: int
    totalElements: int
    totalPages: int
    sort: str
