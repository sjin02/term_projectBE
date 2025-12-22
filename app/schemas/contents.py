from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class ContentCreateRequest(BaseModel):
    tmdb_id: int = Field(..., description="TMDB movie id")


class GenreBrief(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True


class TMDBGenre(BaseModel):
    id: int
    name: str


class TMDBMoviePayload(BaseModel):
    id: int
    title: str
    overview: Optional[str] = None
    release_date: Optional[date] = None
    runtime: Optional[int] = None
    poster_path: Optional[str] = None
    backdrop_path: Optional[str] = None
    original_language: Optional[str] = None
    popularity: Optional[float] = None
    vote_average: Optional[float] = None
    vote_count: Optional[int] = None
    genres: List[TMDBGenre] = []


class ContentBase(BaseModel):
    id: int
    tmdb_id: int
    title: str
    release_date: Optional[date] = None
    runtime_minutes: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None
    genres: List[GenreBrief] = []

    class Config:
        from_attributes = True


class ContentResponse(ContentBase):
    tmdb: TMDBMoviePayload


class ContentListResponse(BaseModel):
    items: List[ContentBase]
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
