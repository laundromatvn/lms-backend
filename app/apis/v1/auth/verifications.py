from fastapi import APIRouter, HTTPException, Depends

from app.apis.deps import get_current_user
from app.core.logging import logger
from app.models.user import User
from app.schemas.auth import (
    VerifyStoreConfigurationAccessRequest,
    VerifyStoreConfigurationAccessResponse
)
from app.operations.auth.verifications.verify_for_store_configuration_access_operation import (
    VerifyForStoreConfigurationAccessOperation,
)


router = APIRouter()


@router.post(
    "/store-configuration-access", 
    response_model=VerifyStoreConfigurationAccessResponse,
)
async def verify_store_configuration_access(
    request: VerifyStoreConfigurationAccessRequest,
    current_user: User = Depends(get_current_user),
):
    try:
        system_task = await VerifyForStoreConfigurationAccessOperation.execute(current_user, request.tenant_id)
        return {
            "system_task_id": system_task.id,
        }
    except Exception as e:
        logger.error("Verify store configuration access failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


