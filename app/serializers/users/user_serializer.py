from pydantic import BaseModel
from typing import Optional

from datetime import datetime

from app.models.users.user import UserRole


class UserSerializer(BaseModel):
    id: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    role: Optional[UserRole] = None
    is_verified: Optional[bool] = None
    verified_at: Optional[datetime] = None
