from app.core.celery_app import celery_app
from app.core.logging import logger
from app.operations.order.sync_up_in_progress_orders_operation import SyncUpInProgressOrdersOperation


@celery_app.task(name="app.tasks.order.sync_up_in_progress_orders_task")
def sync_up_in_progress_orders_task():
    logger.info("Syncing up in progress orders")
    
    try:
        SyncUpInProgressOrdersOperation.execute()
    except Exception as e:
        logger.error(f"Error syncing up in progress orders: {str(e)}")
        raise e

    logger.info("In progress orders synced up")


