from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, Field


class ReviewCreate(BaseModel):
    rating: int = Field(..., ge=1, le=5 , description="평점은 1부터 5까지의 정수입니다.")
    comment: str = Field(..., min_length=1 , description="리뷰 내용은 최소 1자 이상이어야 합니다.")

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

class ReviewLikeResponse(BaseModel):
    review_id: int
    user_id: int
    is_liked: bool # 좋아요 상태 (True: 좋아요, False: 취소됨)
    total_likes: int # 갱신된 좋아요 수

    model_config = ConfigDict(from_attributes=True)

class ReviewListResponse(BaseModel):
    items: List[ReviewResponse]
    total: int