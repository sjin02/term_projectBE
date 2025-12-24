from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional

class GenreBase(BaseModel):
    name: str = Field(min_length=1, max_length=50)

# 생성 요청 (POST)
class GenreCreate(GenreBase):
    pass

# 수정 요청 (PATCH) - 이름 변경 가능
class GenreUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=50)

# 응답 (GET)
class GenreResponse(GenreBase):
    id: int
    created_at: datetime
    # deleted_at은 보통 응답에 포함하지 않거나, 필요시 포함

    model_config = ConfigDict(from_attributes=True)