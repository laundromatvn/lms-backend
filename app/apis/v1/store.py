from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from app.apis.deps import get_current_user
from app.core.logging import logger
from app.models.user import User
from app.operations.store.store_operation import StoreOperation
from app.operations.store.store_machine_opeartion import StoreMachineOperation
from app.schemas.store import (
    StoreSerializer,
    AddStoreRequest,
    ListStoreQueryParams,
    UpdateStoreRequest,
    ClassifiedMachinesResponse,
)
from app.schemas.pagination import PaginatedResponse
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
    current_user: User = Depends(get_current_user),
):
    try:
        total, stores = StoreOperation.list(current_user, query_params)
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
    except ValueError:
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
