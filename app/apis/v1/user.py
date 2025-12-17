from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.logging import logger
from app.libs.database import get_db
from app.models.user import User
from app.schemas.store import StoreSerializer
from app.schemas.pagination import PaginatedResponse
from app.schemas.user import (
    UserSerializer,
    UpdateUserRequest,
    ResetPasswordRequest,
    CreateUserRequest,
    ListAssignedStoresQueryParams,
    AssignMemberToStoreRequest,
)
from app.apis.deps import get_current_user, require_permissions
from app.operations.permission.get_user_permissions import GetUserPermissionsOperation
from app.operations.user.user_operation import UserOperation
from app.operations.user.assign_member_to_store import AssignMemberToStoreOperation
from app.operations.user.list_assigned_stores import ListAssignedStoresOperation
from app.operations.user.delete_assigned_store import DeleteAssignedStoreOperation
from app.schemas.user import UserPermissionSerializer
from app.utils.pagination import get_total_pages

router = APIRouter()


@router.get("/me")
def get_me(current_user: User = Depends(get_current_user)):
    return current_user.to_dict()


@router.get("/me/permissions", response_model=UserPermissionSerializer)
def get_me_permissions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    permissions = GetUserPermissionsOperation().execute(db, current_user)
    return UserPermissionSerializer(permissions=permissions)


@router.post("/{user_id}/reset-password", response_model=UserSerializer)
def reset_password(
    user_id: str,
    request: ResetPasswordRequest,
    current_user: User = Depends(get_current_user),
):
    try:
        user = UserOperation.reset_password(current_user, user_id, request)
        return user
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("", response_model=UserSerializer)
def create_user(
    request: CreateUserRequest,
    current_user: User = Depends(get_current_user),
):
    try:
        user = UserOperation.create(current_user, request)
        return user
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{user_id}", response_model=UserSerializer)
def get_user(
    user_id: str,
    current_user: User = Depends(get_current_user),
):
    try:
        user = UserOperation.get(current_user, user_id)
        return user
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/{user_id}", response_model=UserSerializer)
def update_user(
    user_id: str,
    request: UpdateUserRequest,
    current_user: User = Depends(get_current_user),
):
    try:
        user = UserOperation.update_partially(current_user, user_id, request)
        return user
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{user_id}/assigned-stores", response_model=PaginatedResponse[StoreSerializer])
def list_assigned_stores(
    user_id: str,
    query_params: ListAssignedStoresQueryParams = Depends(),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        operation = ListAssignedStoresOperation(current_user, user_id, query_params)
        total, stores = operation.execute(db)

        return {
            "page": query_params.page,
            "page_size": query_params.page_size,
            "total": total,
            "total_pages": get_total_pages(total, query_params.page_size),
            "data": stores,
        }
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        logger.error("List assigned stores failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{user_id}/assign-member-to-stores", status_code=status.HTTP_201_CREATED)
def assign_member_to_store(
    user_id: UUID,
    request: AssignMemberToStoreRequest,
    current_user: User = Depends(require_permissions(["store_member.create"])),
    db: Session = Depends(get_db),
):
    try:
        operation = AssignMemberToStoreOperation(current_user, user_id, request.store_ids)
        operation.execute(db)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        logger.error("Assign member to store failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{user_id}/assigned-stores/{store_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_assigned_store(
    user_id: UUID,
    store_id: UUID,
    current_user: User = Depends(require_permissions(["store_member.delete"])),
    db: Session = Depends(get_db),
):
    try:
        operation = DeleteAssignedStoreOperation(current_user, user_id, store_id)
        operation.execute(db)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        logger.error("Delete assigned store failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))