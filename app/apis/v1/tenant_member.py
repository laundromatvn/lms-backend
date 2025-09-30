from fastapi import APIRouter, Depends, HTTPException

from app.apis.deps import get_current_user
from app.core.logging import logger
from app.models.user import User
from app.operations.tenant.tenant_member_opreation import TenantMemberOperation
from app.schemas.tenant_member import (
    TenantMemberSerializer,
    TenantMemberCreate,
)

router = APIRouter()

@router.post("", response_model=TenantMemberSerializer)
def add_tenant_member(
    request: TenantMemberCreate,
    current_user: User = Depends(get_current_user),
):
    try:
        return TenantMemberOperation.add(current_user, request)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        logger.error("Add tenant member failed", type=type(e).__name__, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))
