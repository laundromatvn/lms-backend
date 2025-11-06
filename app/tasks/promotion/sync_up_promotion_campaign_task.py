from app.core.celery_app import celery_app
from app.core.logging import logger
from app.operations.promotion.sync_up_promotion_campaign_operation import SyncUpPromotionCampaignOperation


@celery_app.task(name="app.tasks.promotion.sync_up_promotion_campaign_task")
def sync_up_promotion_campaign_task():
    logger.info("Syncing up promotion campaigns")
    try:
        SyncUpPromotionCampaignOperation.execute()
    except Exception as e:
        logger.error(f"Error syncing up promotion campaigns: {str(e)}")
        raise e
    logger.info("Promotion campaigns synced up")


