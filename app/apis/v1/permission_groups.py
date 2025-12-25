from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.apis.deps import require_permissions
from app.libs.database import get_db
from app.models.user import User
from app.operations.permission.get_group_permissions import GetGroupPermissionsOperation
from app.operations.permission.list_permission_groups import ListPermissionGroupsOperation
from app.operations.permission.create_permission_group import CreatePermissionGroupOperation
from app.operations.permission.get_permission_group import GetPermissionGroupOperation
from app.operations.permission.delete_permission_group import DeletePermissionGroupOperation
from app.operations.permission.update_permission_group import UpdatePermissionGroupOperation
from app.operations.permission.add_permissions_to_group import AddPermissionsToGroupOperation
from app.schemas.permission import (
    PermissionGroupSerializer,
    PermissionGroupCreatePayload,
    PermissionGroupUpdatePayload,
    ListPermissionGroupsQueryParams,
    AddPermissionsToGroupPayload,
    PermissionSerializer,
    ListGroupPermissionsQueryParams,
)
from app.schemas.pagination import PaginatedResponse
from app.utils.pagination import get_total_pages

router = APIRouter()
    

@router.post("/{permission_group_id}/permissions", status_code=204)
def add_permissions_to_group(
    permission_group_id: UUID,
    payload: AddPermissionsToGroupPayload,
    current_user: User = Depends(require_permissions(["permission_group.create","permission.update"])),
    db: Session = Depends(get_db),
):
    try:
        operation = AddPermissionsToGroupOperation(
            db,
            current_user,
            permission_group_id,
            payload.permission_codes,
        )
        operation.execute()
    except PermissionError:
        raise HTTPException(status_code=403)
    except Exception as e:
        raise HTTPException(status_code=422, detail=str(e))
    

@router.get("/{permission_group_id}/permissions", response_model=PaginatedResponse[PermissionSerializer])
def get_group_permissions(
    permission_group_id: UUID,
    query_params: ListGroupPermissionsQueryParams = Depends(),
    current_user: User = Depends(require_permissions(["permission_group.get"])),
    db: Session = Depends(get_db),
):
    try:
        operation = GetGroupPermissionsOperation(
            db,
            current_user,
            permission_group_id,
            query_params,
        )
        total, permissions = operation.execute()
        return PaginatedResponse(
            page=query_params.page,
            page_size=query_params.page_size,
            total=total,
            total_pages=get_total_pages(total, query_params.page_size),
            data=permissions,
        )
    except PermissionError:
        raise HTTPException(status_code=403)
    except Exception as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.get("/{permission_group_id}", response_model=PermissionGroupSerializer)
def get_permission_group(
    permission_group_id: UUID,
    current_user: User = Depends(require_permissions(["permission_group.get"])),
    db: Session = Depends(get_db),
):
    try:
        operation = GetPermissionGroupOperation(
            db,
            current_user,
            permission_group_id,
        )
        permission_group = operation.execute()
        return permission_group
    except PermissionError:
        raise HTTPException(status_code=403)
    except Exception as e:
        raise HTTPException(status_code=422, detail=str(e))
    
    
@router.patch("/{permission_group_id}", status_code=204)
def update_permission_group(
    permission_group_id: UUID,
    payload: PermissionGroupUpdatePayload,
    current_user: User = Depends(require_permissions(["permission_group.update"])),
    db: Session = Depends(get_db),
):
    try:
        operation = UpdatePermissionGroupOperation(db, current_user, permission_group_id, payload)
        operation.execute()
    except PermissionError:
        raise HTTPException(status_code=403)
    except Exception as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.delete("/{permission_group_id}", status_code=204)
def delete_permission_group(
    permission_group_id: UUID,
    current_user: User = Depends(require_permissions(["permission_group.delete"])),
    db: Session = Depends(get_db),
):
    try:
        operation = DeletePermissionGroupOperation(db, current_user, permission_group_id)
        operation.execute()
    except PermissionError:
        raise HTTPException(status_code=403)
    except Exception as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.get("", response_model=PaginatedResponse[PermissionGroupSerializer])
def list_permission_groups(
    query_params: ListPermissionGroupsQueryParams = Depends(),
    current_user: User = Depends(require_permissions(["permission_group.list"])),
    db: Session = Depends(get_db),
):
    try:
        operation = ListPermissionGroupsOperation(db, current_user, query_params)
        total, permission_groups = operation.execute()
        return PaginatedResponse(
            page=query_params.page,
            page_size=query_params.page_size,
            total=total,
            total_pages=get_total_pages(total, query_params.page_size),
            data=permission_groups,
        )
    except PermissionError:
        raise HTTPException(status_code=403)
    except Exception as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.post("", status_code=201)
def create_permission_group(
    payload: PermissionGroupCreatePayload,
    current_user: User = Depends(require_permissions(["permission_group.create"])),
    db: Session = Depends(get_db),
):
    try:
        operation = CreatePermissionGroupOperation(db, current_user, payload)
        operation.execute()
    except PermissionError:
        raise HTTPException(status_code=403)
    except Exception as e:
        raise HTTPException(status_code=422, detail=str(e))
