from uuid import UUID

from fastapi import APIRouter, HTTPException, Depends, status

from app.apis.deps import get_current_user
from app.models.user import User
from app.operations.firmware.cancel_update_firmware_operation import CancelUpdateFirmwareOperation


router = APIRouter()


@router.post("/{firmware_deployment_id}/cancel", status_code=status.HTTP_204_NO_CONTENT)
async def cancel_update_firmware(
    firmware_deployment_id: UUID,
    current_user: User = Depends(get_current_user),
):
    try:
        cancel_update_firmware_operation = CancelUpdateFirmwareOperation(current_user, firmware_deployment_id)
        cancel_update_firmware_operation.execute()
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


