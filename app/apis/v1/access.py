from fastapi import APIRouter, Depends, HTTPException

from sqlalchemy.orm import Session

from app.apis.deps import get_current_user
from app.core.logging import logger
from app.libs.database import get_db
from app.models.user import User
from app.services.access_service import AccessService

router = APIRouter()


@router.get("")
async def get_access(
    name: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        return AccessService(db, current_user).get_access(name)
    except Exception as e:
        logger.error("Get access failed", type=type(e).__name__, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

