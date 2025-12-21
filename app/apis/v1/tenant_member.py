from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.apis.deps import require_permissions
from app.libs.database import get_db
from app.core.logging import logger
from app.models.user import User
from app.operations.tenant.tenant_member_opreation import TenantMemberOperation
from app.operations.tenant_member.delete_tenant_member import DeleteTenantMemberOperation
from app.operations.tenant_member.list_tenant_members import ListTenantMembersOperation
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
    current_user: User = Depends(require_permissions(["tenant_member.create"])),
):
    try:
        tenant_member = TenantMemberOperation.add(current_user, request)
        tenant_member = TenantMemberOperation.get(current_user, tenant_member.id)
        return tenant_member
    except PermissionError as e:
        raise HTTPException(status_code=403)
    except Exception as e:
        logger.error("Add tenant member failed", type=type(e).__name__, error=str(e))
        raise HTTPException(status_code=422)


@router.get("", response_model=PaginatedResponse[TenantMemberSerializer])
def list_tenant_members(
    query_params: ListTenantMemberQueryParams = Depends(),
    current_user: User = Depends(require_permissions(["tenant_member.list"])),
    db: Session = Depends(get_db),
):
    try:
        operation = ListTenantMembersOperation(db, current_user, query_params)
        total, tenant_members = operation.execute()

        return {
            "page": query_params.page,
            "page_size": query_params.page_size,
            "total": total,
            "total_pages": get_total_pages(total, query_params.page_size),
            "data": tenant_members,
        }
    except PermissionError as e:
        raise HTTPException(status_code=403)
    except Exception as e:
        logger.error("List tenant members failed", type=type(e).__name__, error=str(e))
        raise HTTPException(status_code=422)


@router.delete("/{tenant_member_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_tenant_member(
    tenant_member_id: str,
    current_user: User = Depends(require_permissions(["tenant_member.delete"])),
    db: Session = Depends(get_db),
):
    try:
        operation = DeleteTenantMemberOperation(db, current_user, tenant_member_id)
        operation.execute()
    except PermissionError as e:
        raise HTTPException(status_code=403)
    except Exception as e:
        logger.error("Delete tenant member failed", type=type(e).__name__, error=str(e))
        raise HTTPException(status_code=422)
