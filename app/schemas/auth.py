from pydantic import BaseModel

from app.models.user import UserRole
from app.schemas.user import UserSerializer
from app.schemas.tenant import TenantSerializer


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


class SendOTPRequest(BaseModel):
    email: str


class SendOTPResponse(BaseModel):
    message: str
    email: str
    expires_in_minutes: int


class VerifyOTPRequest(BaseModel):
    otp: str


class VerifyOTPResponse(BaseModel):
    message: str


class LMSProfileResponse(BaseModel):
    user: UserSerializer
    tenant: TenantSerializer
