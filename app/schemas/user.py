from pydantic import BaseModel

from app.models.user import UserRole, UserStatus


class UserSerializer(BaseModel):
    id: str
    created_at: str
    updated_at: str
    deleted_at: str | None = None
    verified_at: str | None = None
    is_verified: bool
    email: str | None = None
    phone: str | None = None
    role: UserRole
    status: UserStatus
