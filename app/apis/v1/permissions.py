from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.apis.deps import require_permissions
from app.libs.database import get_db
from app.models.permission import Permission
from app.models.user import User
from app.operations.permission.list_permissions import ListPermissionsOperation
from app.operations.permission.create_permission import CreatePermissionOperation
from app.schemas.permission import (
    PermissionSerializer,
    ListPermissionQueryParams,
    PermissionEditRequest,
    PermissionCreateRequest,
)
from app.schemas.pagination import PaginatedResponse
from app.utils.pagination import get_total_pages

router = APIRouter()


@router.get("/{permission_id}", response_model=PermissionSerializer)
def get_permission(
    permission_id: int,
    current_user: User = Depends(require_permissions(["permission.get"])),
    db: Session = Depends(get_db),
):
    permission = db.query(Permission).filter(Permission.id == permission_id).first()
    if not permission:
        raise HTTPException(status_code=404, detail="Permission not found")

    return permission


@router.patch("/{permission_id}", status_code=status.HTTP_204_NO_CONTENT)
def update_permission(
    permission_id: int,
    request: PermissionEditRequest,
    _: User = Depends(require_permissions(["permission.update"])),
    db: Session = Depends(get_db),
):
    permission = db.query(Permission).filter(Permission.id == permission_id).first()
    if not permission:
        raise HTTPException(status_code=404, detail="Permission not found")

    for field, value in request.model_dump(exclude_unset=True).items():
        if hasattr(permission, field):
            setattr(permission, field, value)
            
    db.add(permission)
    db.commit()
    db.refresh(permission)


@router.delete("/{permission_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_permission(
    permission_id: int,
    _: User = Depends(require_permissions(["permission.delete"])),
    db: Session = Depends(get_db),
):
    permission = db.query(Permission).filter(Permission.id == permission_id).first()
    if not permission:
        raise HTTPException(status_code=404, detail="Permission not found")
    
    db.delete(permission)
    db.commit()


@router.get("", response_model=PaginatedResponse[PermissionSerializer])
def list_permissions(
    query_params: ListPermissionQueryParams = Depends(),
    _: User = Depends(require_permissions(["permission.list"])),
    db: Session = Depends(get_db),
):
    total, permissions = ListPermissionsOperation().execute(db, query_params)
    return {
        "page": query_params.page,
        "page_size": query_params.page_size,
        "total": total,
        "total_pages": get_total_pages(total, query_params.page_size),
        "data": permissions,
    }


@router.post("", status_code=status.HTTP_201_CREATED)
def create_permission(
    request: PermissionCreateRequest,
    _: User = Depends(require_permissions(["permission.create"])),
    db: Session = Depends(get_db),
):
    CreatePermissionOperation().execute(db, request)

