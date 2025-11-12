from uuid import UUID

from app.core.celery_app import celery_app
from app.core.logging import logger
from app.operations.firmware.handle_update_firmware_failed_operation import HandleUpdateFirmwareFailedOperation


@celery_app.task(name="app.tasks.firmware.handle_update_firmware_failed_task")
def handle_update_firmware_failed_task(deployment_id: UUID):
    logger.info(f"Handling update firmware failed", extra={"deployment_id": deployment_id})
    try:
        operation = HandleUpdateFirmwareFailedOperation(deployment_id)
        operation.execute()
    except Exception as e:
        logger.error(f"Error handling update firmware failed: {str(e)}")
        raise e
    logger.info("Update firmware failed handled")
