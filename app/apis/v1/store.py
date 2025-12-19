from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.apis.deps import get_current_user, require_permissions
from app.core.logging import logger
from app.libs.database import get_db
from app.models.user import User
from app.operations.store.list_stores import ListStoresOperation
from app.operations.store.store_operation import StoreOperation
from app.operations.store.store_machine_opeartion import StoreMachineOperation
from app.operations.store.get_store_payment_methods_operation import GetStorePaymentMethodsOperation
from app.operations.store_members import (
    AddStoreMemberOperation,
    ListStoreMembersOperation,
    DeleteStoreMemberOperation,
)
from app.schemas.store import (
    StoreSerializer,
    AddStoreRequest,
    ListStoreQueryParams,
    UpdateStoreRequest,
    ClassifiedMachinesResponse,
    StorePaymentMethod,
)
from app.schemas.pagination import PaginatedResponse
from app.schemas.store_members import (
    StoreMemberListSerializer,
    CreateStoreMemberRequest,
    ListStoreMembersQueryParams,
)   
from app.utils.pagination import get_total_pages

router = APIRouter()


@router.post("", response_model=StoreSerializer)
def create_store(
    request: AddStoreRequest,
    current_user: User = Depends(get_current_user),
):
    try:
        return StoreOperation.create(current_user, request)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        logger.error("Create store failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("", response_model=PaginatedResponse[StoreSerializer])
def list_stores(
    query_params: ListStoreQueryParams = Depends(),
    current_user: User = Depends(require_permissions(["store.list"])),
    db: Session = Depends(get_db),
):
    try:
        operation = ListStoresOperation(db, current_user, query_params)
        total, stores = operation.execute()
        
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
        logger.error("List stores failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{store_id}", response_model=StoreSerializer)
def get_store(
    store_id: UUID,
    current_user: User = Depends(get_current_user),
):
    try:
        return StoreOperation.get(current_user, store_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error("Get store failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/{store_id}", response_model=StoreSerializer)
def update_store(
    store_id: UUID,
    request: UpdateStoreRequest,
    current_user: User = Depends(get_current_user),
):
    try:
        return StoreOperation.update_partially(current_user, store_id, request)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        logger.error("Update store failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{store_id}/classified-machines", response_model=ClassifiedMachinesResponse)
def classified_machines(
    store_id: UUID,
    _: User = Depends(get_current_user),
):
    try:
        washers, dryers = StoreMachineOperation.classify_machines(store_id)
        return {
            "washers": washers,
            "dryers": dryers,
        }
    except Exception as e:
        logger.error("Classified machines failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{store_id}/payment-methods", response_model=List[StorePaymentMethod])
def get_store_payment_methods(
    store_id: UUID,
    current_user: User = Depends(get_current_user),
):
    try:
        return GetStorePaymentMethodsOperation(current_user, store_id).execute()
    except Exception as e:
        logger.error("Get store payment methods failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{store_id}/members", response_model=PaginatedResponse[StoreMemberListSerializer])
def list_store_members(
    store_id: UUID,
    query_params: ListStoreMembersQueryParams = Depends(),
    current_user: User = Depends(require_permissions(["store_member.list"])),
    db: Session = Depends(get_db),
):
    try:
        operation = ListStoreMembersOperation(current_user, store_id, query_params)
        total, store_members = operation.execute(db)

        return {
            "page": query_params.page,
            "page_size": query_params.page_size,
            "total": total,
            "total_pages": get_total_pages(total, query_params.page_size),
            "data": store_members,
        }
    except Exception as e:
        logger.error("List store members failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{store_id}/members", status_code=status.HTTP_201_CREATED)
def add_store_member(
    store_id: UUID,
    request: CreateStoreMemberRequest,
    current_user: User = Depends(require_permissions(["store_member.create"])),
    db: Session = Depends(get_db),
):
    try:
        AddStoreMemberOperation(current_user, store_id, request.user_id).execute(db)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        logger.error("Add store member failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{store_id}/members/{store_member_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_store_member(
    store_member_id: UUID,
    current_user: User = Depends(require_permissions(["store_member.delete"])),
    db: Session = Depends(get_db),
):
    try:
        DeleteStoreMemberOperation(current_user, store_member_id).execute(db)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        logger.error("Delete store member failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))
