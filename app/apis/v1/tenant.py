from fastapi import APIRouter, Depends, HTTPException, status

from sqlalchemy.orm import Session

from app.apis.deps import get_current_user, require_permissions
from app.libs.database import get_db
from app.models.user import User
from app.operations.tenant.tenant_operation import TenantOperation
from app.operations.tenant.list_tenants import ListTenantsOperation
from app.operations.tenant.delete_tenant import DeleteTenantOperation
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


@router.get("", response_model=PaginatedResponse[TenantSerializer])
def list_tenants(
    query_params: ListTenantQueryParams = Depends(),
    current_user: User = Depends(require_permissions(["tenant.list"])),
    db: Session = Depends(get_db),
):
    try:
        operation = ListTenantsOperation(db, current_user, query_params)
        total, tenants = operation.execute()

        return PaginatedResponse(
            page=query_params.page,
            page_size=query_params.page_size,
            total=total,
            total_pages=get_total_pages(total, query_params.page_size),
            data=tenants,
        )
    except PermissionError as e:
        raise HTTPException(status_code=403)
    except Exception as e:
        logger.error("List tenants failed", error=str(e))
        raise HTTPException(status_code=500)


@router.post("", response_model=TenantSerializer)
def add_tenant(
    request: AddTenantRequest,
    current_user: User = Depends(get_current_user),
):
    try:
        return TenantOperation.add(current_user, request)
    except ValueError:
        raise HTTPException(status_code=400)
    except Exception as e:
        logger.error("Add tenant failed", type=type(e).__name__, error=str(e))
        raise HTTPException(status_code=500)


@router.get("/{tenant_id}", response_model=TenantSerializer)
def get_tenant(
    tenant_id: str,
    current_user: User = Depends(get_current_user),
):
    try:
        return TenantOperation.get(current_user, tenant_id)
    except ValueError:
        raise HTTPException(status_code=404)
    except PermissionError:
        raise HTTPException(status_code=403)
    except Exception as e:
        logger.error("Get tenant failed", type=type(e).__name__, error=str(e))
        raise HTTPException(status_code=500)


@router.patch("/{tenant_id}", response_model=TenantSerializer)
def update_tenant(
    tenant_id: str,
    request: UpdateTenantRequest,
    current_user: User = Depends(get_current_user),
):
    try:
        return TenantOperation.update_partially(current_user, tenant_id, request)
    except ValueError:
        raise HTTPException(status_code=404)
    except PermissionError:
        raise HTTPException(status_code=403)
    except Exception as e:
        logger.error("Update tenant failed", type=type(e).__name__, error=str(e))
        raise HTTPException(status_code=500)


@router.delete("/{tenant_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_tenant(
    tenant_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        operation = DeleteTenantOperation(db, current_user, tenant_id)
        operation.execute()
    except ValueError:
        raise HTTPException(status_code=404)
    except PermissionError:
        raise HTTPException(status_code=403)
    except Exception as e:
        logger.error("Delete tenant failed", type=type(e).__name__, error=str(e))
        raise HTTPException(status_code=500)
