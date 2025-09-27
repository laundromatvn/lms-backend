from fastapi import APIRouter, Depends, HTTPException

from app.apis.deps import get_current_user
from app.models.user import User
from app.operations.tenant.tenant_operation import TenantOperation
from app.schemas.tenant import (
    TenantSerializer,
    AddTenantRequest,
    UpdateTenantRequest,
)
from app.core.logging import logger


router = APIRouter()


@router.post("/", response_model=TenantSerializer)
def add_tenant(
    request: AddTenantRequest,
    current_user: User = Depends(get_current_user),
):
    try:
        return TenantOperation.add(current_user, request)
    except ValueError:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Add tenant failed", type=type(e).__name__, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{tenant_id}", response_model=TenantSerializer)
def get_tenant(
    tenant_id: str,
    current_user: User = Depends(get_current_user),
):
    try:
        return TenantOperation.get(current_user, tenant_id)
    except ValueError:
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionError:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        logger.error("Get tenant failed", type=type(e).__name__, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{tenant_id}", response_model=TenantSerializer)
def update_tenant(
    tenant_id: str,
    request: UpdateTenantRequest,
    current_user: User = Depends(get_current_user),
):
    try:
        return TenantOperation.update(current_user, tenant_id, request)
    except ValueError:
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionError:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        logger.error("Update tenant failed", type=type(e).__name__, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))
