from datetime import datetime
from uuid import UUID
from typing import Any

from pydantic import BaseModel

from app.enums.auth_session import AuthSessionStatusEnum


class AuthSession(BaseModel):
    id: UUID
    created_at: datetime
    updated_at: datetime
    status: AuthSessionStatusEnum
    expires_in: int
    expires_at: datetime
    data: Any | None


class AuthSessionSerializer(BaseModel):
    id: UUID
    created_at: datetime
    updated_at: datetime
    status: AuthSessionStatusEnum
    expires_in: int
    expires_at: datetime
    data: Any | None
