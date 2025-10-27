from app.core.celery_app import celery_app
from app.operations.order import SyncUpInProgressOrdersOperation


@celery_app.task(name="app.tasks.order.sync_up_in_progress_orders")
def sync_up_in_progress_orders():
    SyncUpInProgressOrdersOperation.execute()


