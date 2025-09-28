from fastapi import APIRouter, Depends, HTTPException

from app.apis.deps import get_current_user
from app.core.logging import logger
from app.models.user import User
from app.operations.controller.controller_operation import ControllerOperation
from app.schemas.controller import (
    ControllerSerializer,
    AddControllerRequest,
    UpdateControllerRequest,
    ListControllerQueryParams,
)
from app.schemas.pagination import PaginatedResponse
from app.utils.pagination import get_total_pages


router = APIRouter()


@router.get("/{controller_id}", response_model=ControllerSerializer)
def get_controller(
    controller_id: str,
    _: User = Depends(get_current_user),
):
    try:
        return ControllerOperation.get(controller_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        logger.error("Get controller failed", type=type(e).__name__, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_model=PaginatedResponse[ControllerSerializer])
def list_controllers(
    query_params: ListControllerQueryParams = Depends(),
    _: User = Depends(get_current_user),
):
    try:
        total, controllers = ControllerOperation.list(query_params)
        return {
            "page": query_params.page,
            "page_size": query_params.page_size,
            "total": total,
            "total_pages": get_total_pages(total, query_params.page_size),
            "data": controllers,
        }
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        logger.error("List controllers failed", type=type(e).__name__, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/", response_model=ControllerSerializer)
def add_controller(
    request: AddControllerRequest,
    current_user: User = Depends(get_current_user),
):
    try:
        return ControllerOperation.create(current_user, request)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        logger.error("Add controller failed", type=type(e).__name__, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/{controller_id}", response_model=ControllerSerializer)
def update_partially_controller(
    controller_id: str,
    request: UpdateControllerRequest,
    current_user: User = Depends(get_current_user),
):
    try:
        return ControllerOperation.update_partially(current_user, controller_id, request)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        logger.error("Update partially controller failed", type=type(e).__name__, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))
