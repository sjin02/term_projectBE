from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class GenreResponse(BaseModel):
    id: int
    tmdb_genre_id: int
    name: str
    created_at: datetime
    deleted_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class GenreListResponse(BaseModel):
    items: List[GenreResponse]
