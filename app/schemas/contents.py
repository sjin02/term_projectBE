from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel

class ContentCreateRequest(BaseModel):
    title: str
    description: Optional[str] = None
    release_year: int
    runtime_minutes: int
    genre_ids: List[int] = []

class ContentUpdateRequest(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    release_year: Optional[int] = None
    runtime_minutes: Optional[int] = None
    genre_ids: Optional[List[int]] = None

class ContentResponse(BaseModel):
    id: int
    title: str
    description: Optional[str]
    release_year: int
    runtime_minutes: int
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime]
    genres: List[dict] = []

class ContentListResponse(BaseModel):
    items: List[ContentResponse]
    page: int
    size: int
    total: int

class TopRatedItem(BaseModel):
    content_id: int
    title: str
    avg_rating: float
    review_count: int

class TopRatedResponse(BaseModel):
    items: List[TopRatedItem]