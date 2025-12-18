from app.core.celery_app import celery_app
from app.core.logging import logger
from app.operations.machine.reset_no_responding_machines import ResetNoRespondingMachinesOperation


@celery_app.task(name="app.tasks.machine.reset_no_responding_machines_task")
def reset_no_responding_machines_task():
    logger.info("Starting reset no responding machines task")
    
    try:
        operation = ResetNoRespondingMachinesOperation()
        operation.execute()
    except Exception as e:
        logger.error(f"Error resetting no responding machines: {str(e)}")

    logger.info("Finished reset no responding machines task")
