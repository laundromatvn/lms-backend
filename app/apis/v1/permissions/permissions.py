from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.apis.deps import get_current_user
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
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not current_user.is_admin:
        raise PermissionError("You are not allowed to get permission")
    
    permission = db.query(Permission).filter(Permission.id == permission_id).first()
    if not permission:
        raise HTTPException(status_code=404, detail="Permission not found")
    
    return permission



@router.patch("/{permission_id}", status_code=status.HTTP_204_NO_CONTENT)
def update_permission(
    permission_id: int,
    request: PermissionEditRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not current_user.is_admin:
        raise PermissionError("You are not allowed to update permission")

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
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not current_user.is_admin:
        raise PermissionError("You are not allowed to delete permission")
    
    permission = db.query(Permission).filter(Permission.id == permission_id).first()
    if not permission:
        raise HTTPException(status_code=404, detail="Permission not found")
    
    db.delete(permission)
    db.commit()


@router.get("", response_model=PaginatedResponse[PermissionSerializer])
def list_permissions(
    query_params: ListPermissionQueryParams = Depends(),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        total, permissions = ListPermissionsOperation().execute(db, current_user, query_params)
        return {
            "page": query_params.page,
            "page_size": query_params.page_size,
            "total": total,
            "total_pages": get_total_pages(total, query_params.page_size),
            "data": permissions,
        }
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

@router.post("", status_code=status.HTTP_201_CREATED)
def create_permission(
    request: PermissionCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        CreatePermissionOperation().execute(db, current_user, request)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


