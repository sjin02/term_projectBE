from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr

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

class UpdateMeRequest(BaseModel):
    nickname: Optional[str] = None

class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str
