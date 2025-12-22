from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class GenreCreateRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=50)


class GenreUpdateRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=50)


class GenreResponse(BaseModel):
    id: int
    name: str
    created_at: datetime
    deleted_at: Optional[datetime]

    class Config:
        from_attributes = True


class GenreListResponse(BaseModel):
    content: list[GenreResponse]
    page: int
    size: int
    totalElements: int
    totalPages: int
    sort: str
