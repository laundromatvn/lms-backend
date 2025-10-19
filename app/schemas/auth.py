from pydantic import BaseModel
from typing import Any

from app.enums.auth import OTPActionEnum
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
    session_id: str | None = None


class SignInResponse(BaseModel):
    access_token: str
    refresh_token: str


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class RefreshTokenResponse(BaseModel):
    access_token: str
    refresh_token: str


class SendOTPRequest(BaseModel):
    action: OTPActionEnum
    data: Any | None = {}


class SendOTPResponse(BaseModel):
    message: str
    email: str
    expires_in_minutes: int


class VerifyOTPRequest(BaseModel):
    otp: str
    action: OTPActionEnum
    session_id: str | None = None


class LMSProfileResponse(BaseModel):
    user: UserSerializer
    tenant: TenantSerializer


class GenerateTokenByOneTimeAccessTokenRequest(BaseModel):
    one_time_access_token: str
