from fastapi import APIRouter, HTTPException
from sqlalchemy.exc import IntegrityError

from app.core.logging import logger
from app.schemas.auth import RegisterLMSUserRequest
from app.operations.auth.register_lms_user_operation import RegisterLMSUserOperation


router = APIRouter()


@router.post("/lms/register")
def register(request: RegisterLMSUserRequest):
    try:
        user = RegisterLMSUserOperation.execute(request)
        return user.to_dict()
    except IntegrityError as e:
        logger.error("User registration failed", error=str(e))
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("User registration failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))
