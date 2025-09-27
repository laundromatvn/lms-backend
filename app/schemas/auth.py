from pydantic import BaseModel

from app.models.user import UserRole


class RegisterLMSUserRequest(BaseModel):
    email: str
    password: str
    role: UserRole


class SignInRequest(BaseModel):
    email: str | None = None
    phone: str | None = None
    password: str


class SignInResponse(BaseModel):
    access_token: str
    refresh_token: str


class RefreshTokenRequest(BaseModel):
    refresh_token: str

class RefreshTokenResponse(BaseModel):
    access_token: str
    refresh_token: str
