from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from app.libs.database import get_db
from app.apis.deps import get_current_user
from app.core.logging import logger
from app.models.user import User
from app.schemas.auth import LMSProfileResponse
from app.schemas.user import UserSerializer
from app.schemas.tenant import TenantSerializer
from app.operations.user.get_lms_profile import GetLMSProfileOperation


router = APIRouter()


@router.get("/lms-profile", response_model=LMSProfileResponse)
def get_lms_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        operation = GetLMSProfileOperation(db, current_user)
        user, tenant = operation.execute()
        return {
            "user": user.to_dict(),
            "tenant": tenant.to_dict(),
        }
    except Exception as e:
        logger.error("Get LMS profile failed", error=str(e))
        raise HTTPException(status_code=422)
