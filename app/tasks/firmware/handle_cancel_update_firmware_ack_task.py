from uuid import UUID

from app.core.celery_app import celery_app
from app.core.logging import logger
from app.operations.firmware.handle_cancel_update_firmware_ack_operation import HandleCancelUpdateFirmwareAckOperation


@celery_app.task(name="app.tasks.firmware.handle_cancel_update_firmware_ack_task")
def handle_cancel_update_firmware_ack_task(deployment_id: UUID):
    logger.info(f"Handling cancel update firmware ack", extra={"deployment_id": deployment_id})
    try:
        operation = HandleCancelUpdateFirmwareAckOperation(deployment_id)
        operation.execute()
    except Exception as e:
        logger.error(f"Error handling update firmware ack: {str(e)}")
        raise e
    logger.info("Update firmware ack handled")
