from app.core.celery_app import celery_app
from app.core.logging import logger
from app.operations.payment.sync_up_timeout_payment_operation import SyncUpTimeoutPaymentOperation


@celery_app.task(name="app.tasks.payment.sync_up_timeout_payments_task")
def sync_up_timeout_payments_task():
    logger.info("Syncing up timeout payments")
    try:
        SyncUpTimeoutPaymentOperation.execute()
    except Exception as e:
        logger.error(f"Error syncing up timeout payments: {str(e)}")
        raise e
    logger.info("Timeout payments synced up")


