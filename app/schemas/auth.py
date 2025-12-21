from pydantic import BaseModel, EmailStr

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class RefreshRequest(BaseModel):
    refresh_token: str

class LogoutResponse(BaseModel):
    ok: bool = True

class FirebaseRequest(BaseModel):
    id_token: str

class KakaoRequest(BaseModel):
    access_token: str
