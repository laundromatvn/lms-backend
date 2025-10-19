from fastapi import APIRouter, HTTPException, Depends

from app.apis.deps import get_current_user
from app.core.logging import logger
from app.models.user import User
from app.schemas.auth import LMSProfileResponse
from app.operations.tenant.tenant_operation import TenantOperation


router = APIRouter()


@router.get("/lms-profile", response_model=LMSProfileResponse)
def get_lms_profile(current_user: User = Depends(get_current_user)):
    try:
        tenant = TenantOperation.get_user_tenant(current_user.id)
        return {
            "user": current_user,
            "tenant": tenant,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        logger.error("Get LMS profile failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))
