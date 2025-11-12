from uuid import UUID

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, status
from sqlalchemy.orm import Session

from app.apis.deps import get_current_user
from app.core.logging import logger
from app.libs.database import get_db
from app.models.firmware import Firmware, FirmwareStatus
from app.models.user import User
from app.operations.file.upload_file_operation import UploadFileOperation
from app.operations.firmware.create_firmware_operation import CreateFirmwareOperation
from app.operations.firmware.list_firmware_operation import ListFirmwareOperation
from app.operations.firmware.list_provisioned_controller_operation import ListProvisionedControllersOperation
from app.operations.firmware.flash_firmware_operation import FlashFirmwareOperation
from app.operations.firmware.list_provisioning_controller_operation import ListProvisioningControllersOperation
from app.operations.firmware.update_firmware_operation import UpdateFirmwareOperation
from app.schemas.firmware import (
    FirmwareSerializer,
    FirmwareCreateSchema,
    FirmwareUpdateSchema,
    ListFirmwareQueryParams,
    ListProvisionedControllersQueryParams,
    ProvisionedControllerSerializer,
    ProvisionFirmwareSchema,
    ListProvisioningControllersQueryParams,
    ProvisioningControllerSerializer,
)
from app.schemas.pagination import PaginatedResponse
from app.utils.pagination import get_total_pages

router = APIRouter()


@router.post("/upload")
async def upload_firmware(
    file: UploadFile = File(...),
):
    try:
        upload_operation = UploadFileOperation(file.filename)
        for chunk in file.file:
            upload_operation.execute(chunk)

        return upload_operation.result
    except Exception as e:
        logger.error(f"Error uploading firmware: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("", response_model=PaginatedResponse[FirmwareSerializer])
async def list_firmware(
    query_params: ListFirmwareQueryParams = Depends(),
    current_user: User = Depends(get_current_user),
):
    try:
        total, firmware = ListFirmwareOperation().execute(current_user, query_params)
        return {
            "page": query_params.page,
            "page_size": query_params.page_size,
            "total": total,
            "total_pages": get_total_pages(total, query_params.page_size),
            "data": firmware,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("", response_model=FirmwareSerializer)
async def create_firmware(
    payload: FirmwareCreateSchema,
    current_user: User = Depends(get_current_user),
):
    try:
        create_firmware_operation = CreateFirmwareOperation()
        firmware = create_firmware_operation.execute(current_user, payload)
        return firmware
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{firmware_id}", response_model=FirmwareSerializer)
async def get_firmware(
    firmware_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        if not current_user.is_admin:
            raise PermissionError("You are not allowed to get firmware")
        
        firmware = (
            db.query(Firmware)
            .filter(Firmware.id == firmware_id)
            .filter(Firmware.deleted_at.is_(None))
            .first()
        )
        if not firmware:
            raise ValueError("Firmware not found")

        return firmware
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/{firmware_id}", response_model=FirmwareSerializer)
async def update_firmware(
    firmware_id: UUID,
    payload: FirmwareUpdateSchema,
    current_user: User = Depends(get_current_user),
):
    try:
        update_firmware_operation = UpdateFirmwareOperation()
        firmware = update_firmware_operation.execute(current_user, firmware_id, payload)

        return firmware
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{firmware_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_firmware(
    firmware_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        if not current_user.is_admin:
            raise PermissionError("You are not allowed to delete firmware")
        
        firmware = db.query(Firmware).filter(Firmware.id == firmware_id).first()
        if not firmware:
            raise ValueError("Firmware not found")
        
        firmware.soft_delete(current_user.id)
        db.add(firmware)
        db.commit()
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{firmware_id}/provisioned-controllers", response_model=PaginatedResponse[ProvisionedControllerSerializer])
async def list_provisioned_controllers(
    firmware_id: UUID,
    current_user: User = Depends(get_current_user),
    query_params: ListProvisionedControllersQueryParams = Depends(),
):
    try:
        list_provisioned_controllers_operation = ListProvisionedControllersOperation()
        total, controllers = list_provisioned_controllers_operation.execute(current_user, firmware_id, query_params)
        return {
            "page": query_params.page,
            "page_size": query_params.page_size,
            "total": total,
            "total_pages": get_total_pages(total, query_params.page_size),
            "data": controllers,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{firmware_id}/flash", status_code=status.HTTP_204_NO_CONTENT)
async def flash_firmware(
    firmware_id: UUID,
    payload: ProvisionFirmwareSchema,
    current_user: User = Depends(get_current_user),
):
    try:
        flash_firmware_operation = FlashFirmwareOperation()
        flash_firmware_operation.execute(current_user, firmware_id, payload)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{firmware_id}/release", status_code=status.HTTP_204_NO_CONTENT)
async def release_firmware(
    firmware_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        firmware = (
            db.query(Firmware)
            .filter(Firmware.id == firmware_id)
            .filter(Firmware.deleted_at.is_(None))
            .first()
        )
        if not firmware:
            raise ValueError("Firmware not found")
        
        if firmware.status == FirmwareStatus.RELEASED:
            raise ValueError("Firmware is not in draft status")
        
        firmware.release(current_user.id)
        db.add(firmware)
        db.commit()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{firmware_id}/deprecate", status_code=status.HTTP_204_NO_CONTENT)
async def deprecate_firmware(
    firmware_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        firmware = (
            db.query(Firmware)
            .filter(Firmware.id == firmware_id)
            .filter(Firmware.deleted_at.is_(None))
            .first()
        )
        if not firmware:
            raise ValueError("Firmware not found")
        
        if firmware.status == FirmwareStatus.DRAFT:
            raise ValueError("Cannot deprecate draft firmware")
        
        firmware.deprecate(current_user.id)
        db.add(firmware)
        db.commit()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{firmware_id}/provisioning-controllers", response_model=PaginatedResponse[ProvisioningControllerSerializer])
async def list_provisioning_controllers(
    firmware_id: UUID,
    current_user: User = Depends(get_current_user),
    query_params: ListProvisioningControllersQueryParams = Depends(),
):
    try:
        list_provisioning_controllers_operation = ListProvisioningControllersOperation(current_user, firmware_id, query_params)
        total, controllers = list_provisioning_controllers_operation.execute()
        return {
            "page": query_params.page,
            "page_size": query_params.page_size,
            "total": total,
            "total_pages": get_total_pages(total, query_params.page_size),
            "data": controllers,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))