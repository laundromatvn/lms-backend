from uuid import UUID

from app.core.celery_app import celery_app
from app.core.logging import logger
from app.operations.machine.send_no_responding_machine_notifications import SendNoRespondingMachineNotificationsOperation


@celery_app.task(name="app.tasks.machine.send_no_responding_machine_notifications_task")
def send_no_responding_machine_notifications_task(machine_ids: list[UUID]):
    logger.info("Starting send no responding machine notifications task")
    
    try:
        operation = SendNoRespondingMachineNotificationsOperation(machine_ids=machine_ids)
        operation.execute()
    except Exception as e:
        logger.error(f"Error sending no responding machine notifications: {str(e)}")

    logger.info("Finished send no responding machine notifications task")
