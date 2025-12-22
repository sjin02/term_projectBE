from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class ReviewCreate(BaseModel):
    rating: int = Field(..., ge=1, le=5)
    comment: str = Field(..., min_length=1, max_length=2000)


class ReviewUpdate(BaseModel):
    rating: Optional[int] = Field(None, ge=1, le=5)
    comment: Optional[str] = Field(None, min_length=1, max_length=2000)


class ReviewResponse(BaseModel):
    id: int
    content_id: int
    user_id: int
    rating: int
    comment: str
    like_count: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ReviewListResponse(BaseModel):
    content: list[ReviewResponse]
    page: int
    size: int
    totalElements: int
    totalPages: int
    sort: str
