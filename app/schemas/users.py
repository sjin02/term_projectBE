from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, ConfigDict  # ConfigDict 추가

class SignupRequest(BaseModel):
    email: EmailStr
    password: str
    nickname: str

class UserMeResponse(BaseModel):
    id: int
    email: EmailStr
    nickname: str
    role: str
    status: str
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None

    # ORM 모드 활성화 (SQLModel 객체를 바로 model_validate 할 수 있게 함)
    model_config = ConfigDict(from_attributes=True)

class UpdateMeRequest(BaseModel):
    nickname: Optional[str] = None

class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str