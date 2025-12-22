from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.apis.deps import get_current_user, require_permissions
from app.core.logging import logger
from app.libs.database import get_db
from app.models.user import User
from app.operations.controller.abandon_controller_operation import AbandonControllerOperation
from app.operations.controller.controller_operation import ControllerOperation
from app.operations.controller.list_controllers import ListControllersOperation
from app.schemas.controller import (
    ControllerSerializer,
    AddControllerRequest,
    UpdateControllerRequest,
    ListControllerQueryParams,
)
from app.schemas.pagination import PaginatedResponse
from app.utils.pagination import get_total_pages


router = APIRouter()


@router.post("", response_model=ControllerSerializer)
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


@router.get("", response_model=PaginatedResponse[ControllerSerializer])
def list_controllers(
    query_params: ListControllerQueryParams = Depends(),
    current_user: User = Depends(require_permissions(['controller.list'])),
    db: Session = Depends(get_db),
):
    try:
        operation = ListControllersOperation(db, current_user, query_params)
        total, controllers = operation.execute()

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
        logger.error("List controllers failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/abandoned", response_model=PaginatedResponse[str])
def get_abandoned_controllers(
    query_params: ListControllerQueryParams = Depends(),
    _: User = Depends(get_current_user),
):
    try:
        abandoned_controllers = AbandonControllerOperation.list()
        return {
            "page": query_params.page,
            "page_size": query_params.page_size,
            "total": len(abandoned_controllers if abandoned_controllers else []),
            "total_pages": get_total_pages(len(abandoned_controllers if abandoned_controllers else []), query_params.page_size),
            "data": abandoned_controllers[query_params.page - 1:query_params.page_size] if abandoned_controllers else [],
        }
    except Exception as e:
        logger.error("Get abandoned controllers failed", type=type(e).__name__, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/abandoned/assign", response_model=ControllerSerializer)
def assign_abandoned_controller(
    request: AddControllerRequest,
    current_user: User = Depends(get_current_user),
):
    try:
        controller = ControllerOperation.create(current_user, request)
        AbandonControllerOperation.confirm_assignment(controller)
        AbandonControllerOperation.remove(controller.device_id)
        return controller
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        logger.error("Add controller failed", type=type(e).__name__, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/abandoned/{device_id}/verify")
def verify_abandoned_controllers(
    device_id: str,
    _: User = Depends(get_current_user),
):
    try:
        AbandonControllerOperation.verify(device_id)
        return {
            "message": "Abandoned controller verified successfully",
        }
    except Exception as e:
        logger.error("Verify abandoned controllers failed", type=type(e).__name__, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{controller_id}", response_model=ControllerSerializer)
def get_controller(
    controller_id: str,
    current_user: User = Depends(get_current_user),
):
    try:
        return ControllerOperation.get(current_user, controller_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        logger.error("Get controller failed", type=type(e).__name__, error=str(e))
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


@router.delete("/{controller_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_controller(
    controller_id: str,
    current_user: User = Depends(get_current_user),
):
    try:
        ControllerOperation.delete(current_user, controller_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{controller_id}/activate-machines")
def activate_controller_machines(
    controller_id: str,
    current_user: User = Depends(get_current_user),
):
    try:
        ControllerOperation.activate_controller_machines(current_user, controller_id)
        return {"message": "Machines activated"}
    except Exception as e:
        logger.error("Activate machines failed", type=type(e).__name__, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))
