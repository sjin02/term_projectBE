from typing import List, Optional, Generic, TypeVar
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict

class BookmarkCreate(BaseModel):
    pass
    # 만약 Body로 content_id를 받는다면:
    # content_id: int

# 응답 (GET) - 내 찜 목록 조회 시
class BookmarkResponse(BaseModel):
    user_id: int
    content_id: int
    created_at: datetime
    
    # 찜한 작품의 상세 정보를 같이 내려주는 경우
    content: Optional[ContentSummary] = None

    model_config = ConfigDict(from_attributes=True)