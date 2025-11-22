from pydantic import BaseModel

from app.schemas.pagination import Pagination


class PermissionSerializer(BaseModel):
    id: int
    code: str
    name: str | None = None
    description: str | None = None
    is_enabled: bool
    
    
class PermissionCreateRequest(BaseModel):
    code: str
    name: str
    description: str | None = None
    is_enabled: bool
    

class PermissionEditRequest(BaseModel):
    name: str | None = None
    description: str | None = None
    is_enabled: bool | None = None


class ListPermissionQueryParams(Pagination):
    is_enabled: bool | None = None
    search: str | None = None
    order_by: str | None = None
    order_direction: str | None = None
