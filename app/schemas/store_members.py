from datetime import datetime
from typing import List
from uuid import UUID

from pydantic import BaseModel

from app.schemas.pagination import Pagination
from app.models.user import UserRole, UserStatus


class StoreMemberSerializer(BaseModel):
    id: UUID
    created_at: datetime
    store_id: UUID
    user_id: UUID


class CreateStoreMemberRequest(BaseModel):
    user_id: UUID


class StoreMemberListSerializer(BaseModel):
    id: UUID
    created_at: datetime
    user_id: UUID
    email: str | None = None
    phone: str | None = None
    role: UserRole
    status: UserStatus

class ListStoreMembersQueryParams(Pagination):
    pass
