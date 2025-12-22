from datetime import datetime
from typing import List
from uuid import UUID

from pydantic import BaseModel

from app.models.user import UserRole, UserStatus
from app.models.notification import NotificationType
from app.schemas.pagination import Pagination


class UserSerializer(BaseModel):
    id: UUID
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None = None
    verified_at: datetime | None = None
    is_verified: bool
    email: str | None = None
    phone: str | None = None
    role: UserRole
    status: UserStatus
    
    
class UserPermissionSerializer(BaseModel):
    permissions: List[str]
    
    
class CreateUserRequest(BaseModel):
    email: str | None = None
    phone: str | None = None
    role: UserRole
    password: str


class UpdateUserRequest(BaseModel):
    email: str | None = None
    phone: str | None = None
    role: UserRole | None = None
    status: UserStatus | None = None
    password: str | None = None


class ResetPasswordRequest(BaseModel):
    password: str


class ListAssignedStoresQueryParams(Pagination):
    pass


class AssignMemberToStoreRequest(BaseModel):
    store_ids: List[UUID]


class ListNotificationsQueryParams(Pagination):
    type: NotificationType | None = None


class ListAvailableUserTenantAdminsRequest(Pagination):
    pass
