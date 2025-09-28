from fastapi import APIRouter, Depends, HTTPException

from app.apis.deps import get_current_user
from app.models.user import User
from app.operations.tenant.tenant_operation import TenantOperation
from app.schemas.tenant import (
    TenantSerializer,
    AddTenantRequest,
    UpdateTenantRequest,
    ListTenantQueryParams,
)
from app.core.logging import logger
from app.schemas.pagination import PaginatedResponse
from app.utils.pagination import get_total_pages


router = APIRouter()


@router.get("/{tenant_id}", response_model=TenantSerializer)
def get_tenant(
    tenant_id: str,
    current_user: User = Depends(get_current_user),
):
    try:
        return TenantOperation.get(current_user, tenant_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        logger.error("Get tenant failed", type=type(e).__name__, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_model=PaginatedResponse[TenantSerializer])
def list_tenants(
    query_params: ListTenantQueryParams = Depends(),
    current_user: User = Depends(get_current_user),
):
    try:
        total, tenants = TenantOperation.list(current_user, query_params)
        return {
            "page": query_params.page,
            "page_size": query_params.page_size,
            "total": total,
            "total_pages": get_total_pages(total, query_params.page_size),
            "data": tenants,
        }
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        logger.error("List tenants failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/", response_model=TenantSerializer)
def add_tenant(
    request: AddTenantRequest,
    current_user: User = Depends(get_current_user),
):
    try:
        return TenantOperation.add(current_user, request)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Add tenant failed", type=type(e).__name__, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/{tenant_id}", response_model=TenantSerializer)
def update_tenant(
    tenant_id: str,
    request: UpdateTenantRequest,
    current_user: User = Depends(get_current_user),
):
    try:
        return TenantOperation.update_partially(current_user, tenant_id, request)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        logger.error("Update tenant failed", type=type(e).__name__, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))
