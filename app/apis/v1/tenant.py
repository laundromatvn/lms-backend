from fastapi import APIRouter, Depends, HTTPException, status

from sqlalchemy.orm import Session

from app.apis.deps import require_permissions, get_current_user
from app.libs.database import get_db
from app.models.user import User
from app.operations.tenant.get_active_subscrpition_plan import GetTenantSubscriptionPlanOperation
from app.operations.tenant.get_tenant_permissions import GetTenantPermissionsOperation
from app.operations.tenant.list_tenants import ListTenantsOperation
from app.operations.tenant.get_tenant import GetTenantOperation
from app.operations.tenant.subscribe_to_plan import SubscribeToPlanOperation
from app.operations.tenant.update_tenant import UpdateTenantOperation
from app.operations.tenant.create_tenant import CreateTenantOperation    
from app.operations.tenant.delete_tenant import DeleteTenantOperation
from app.schemas.tenant import (
    TenantSerializer,
    AddTenantRequest,
    UpdateTenantRequest,
    ListTenantQueryParams,
    CreateTenantSubscriptionPlanRequest,
    ListTenantPermissionsQueryParams,
)
from app.schemas.subscription import SubscriptionPlanSerializer
from app.schemas.permission import PermissionSerializer
from app.core.logging import logger
from app.schemas.pagination import PaginatedResponse
from app.utils.pagination import get_total_pages


router = APIRouter()




@router.get("/{tenant_id}/subscription-plan", response_model=SubscriptionPlanSerializer)
def get_tenant_subscription_plan(
    tenant_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        operation = GetTenantSubscriptionPlanOperation(db, current_user, tenant_id)
        subscription_plan = operation.execute()
        return subscription_plan
    except PermissionError:
        raise HTTPException(status_code=403)
    except Exception as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.post("/{tenant_id}/subscription-plan", status_code=204)
def add_tenant_subscription_plan(
    tenant_id: str,
    request: CreateTenantSubscriptionPlanRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        operation = SubscribeToPlanOperation(db, current_user, tenant_id, request.subscription_plan_id)
        operation.execute()
    except PermissionError:
        raise HTTPException(status_code=403)
    except Exception as e:
        raise HTTPException(status_code=422, detail=str(e))
    
    
@router.get("/{tenant_id}/permissions", response_model=PaginatedResponse[PermissionSerializer])
def get_tenant_permissions(
    tenant_id: str,
    query_params: ListTenantPermissionsQueryParams = Depends(),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        operation = GetTenantPermissionsOperation(
            db,
            current_user,
            tenant_id,
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
    except PermissionError:
        raise HTTPException(status_code=403)
    except Exception as e:
        logger.error("List tenants failed", error=str(e))
        raise HTTPException(status_code=422)


@router.post("", status_code=status.HTTP_201_CREATED, response_model=TenantSerializer)
def add_tenant(
    request: AddTenantRequest,
    current_user: User = Depends(require_permissions(["tenant.create"])),
    db: Session = Depends(get_db),
):
    try:
        operation = CreateTenantOperation(db, current_user, request)
        tenant = operation.execute()
        return tenant
    except Exception as e:
        logger.error("Add tenant failed", type=type(e).__name__, error=str(e))
        raise HTTPException(status_code=422)


@router.get("/{tenant_id}", response_model=TenantSerializer)
def get_tenant(
    tenant_id: str,
    current_user: User = Depends(require_permissions(["tenant.get"])),
    db: Session = Depends(get_db),
):
    try:
        operation = GetTenantOperation(db, current_user, tenant_id)
        tenant = operation.execute()
        return tenant
    except PermissionError:
        raise HTTPException(status_code=403)
    except Exception as e:
        logger.error("Get tenant failed", type=type(e).__name__, error=str(e))
        raise HTTPException(status_code=422)


@router.patch("/{tenant_id}", response_model=TenantSerializer)
def update_tenant(
    tenant_id: str,
    request: UpdateTenantRequest,
    current_user: User = Depends(require_permissions(["tenant.update"])),
    db: Session = Depends(get_db),
):
    try:
        operation = UpdateTenantOperation(db, current_user, tenant_id, request)
        tenant = operation.execute()
        return tenant
    except PermissionError:
        raise HTTPException(status_code=403)
    except Exception as e:
        logger.error("Update tenant failed", type=type(e).__name__, error=str(e))
        raise HTTPException(status_code=422)


@router.delete("/{tenant_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_tenant(
    tenant_id: str,
    current_user: User = Depends(require_permissions(["tenant.delete"])),
    db: Session = Depends(get_db),
):
    try:
        operation = DeleteTenantOperation(db, current_user, tenant_id)
        operation.execute()
    except PermissionError:
        raise HTTPException(status_code=403)
    except Exception as e:
        logger.error("Delete tenant failed", type=type(e).__name__, error=str(e))
        raise HTTPException(status_code=422)
