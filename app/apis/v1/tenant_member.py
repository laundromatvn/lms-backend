from fastapi import APIRouter, Depends, HTTPException

from app.apis.deps import get_current_user
from app.core.logging import logger
from app.models.user import User
from app.operations.tenant.tenant_member_opreation import TenantMemberOperation
from app.schemas.tenant_member import (
    TenantMemberSerializer,
    TenantMemberCreate,
    ListTenantMemberQueryParams,
)
from app.schemas.pagination import PaginatedResponse
from app.utils.pagination import get_total_pages

router = APIRouter()

@router.post("", response_model=TenantMemberSerializer)
def add_tenant_member(
    request: TenantMemberCreate,
    current_user: User = Depends(get_current_user),
):
    try:
        tenant_member = TenantMemberOperation.add(current_user, request)
        tenant_member = TenantMemberOperation.get(current_user, tenant_member.id)
        return tenant_member
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        logger.error("Add tenant member failed", type=type(e).__name__, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("", response_model=PaginatedResponse[TenantMemberSerializer])
def list_tenant_members(
    query_params: ListTenantMemberQueryParams = Depends(),
    current_user: User = Depends(get_current_user),
):
    try:
        total, tenant_members = TenantMemberOperation.list(current_user, query_params)
        return {
            "page": query_params.page,
            "page_size": query_params.page_size,
            "total": total,
            "total_pages": get_total_pages(total, query_params.page_size),
            "data": tenant_members,
        }
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        logger.error("List tenant members failed", type=type(e).__name__, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))
