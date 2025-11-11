from uuid import UUID

from app.core.celery_app import celery_app
from app.core.logging import logger
from app.operations.firmware.flash_new_firmware_to_controllers_operation import FlashNewFirmwareToControllersOperation
from app.models.user import User


@celery_app.task(name="app.tasks.firmware.flash_new_firmware_to_controllers_task")
def flash_new_firmware_to_controllers_task(current_user_id: UUID, controller_ids: list[UUID], firmware_id: UUID):
    logger.info(f"Flashing new firmware to controllers", extra={"controller_ids": controller_ids, "firmware_id": firmware_id})
    try:
        flash_firmware_operation = FlashNewFirmwareToControllersOperation(controller_ids, firmware_id)
        flash_firmware_operation.execute(current_user_id)
    except Exception as e:
        logger.error(f"Error flashing new firmware to controllers: {str(e)}")
        raise e
    logger.info("New firmware flashed to controllers")
