from datetime import datetime, timezone
from typing import List

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.logging import logger
from app.libs.database import with_db_session_classmethod
from app.models.promotion_campaign import PromotionCampaign, PromotionCampaignStatus


class SyncUpPromotionCampaignOperation:

    @classmethod
    @with_db_session_classmethod
    def execute(cls, db: Session) -> None:
        """
        Sync up promotion campaigns.
        """
        cls.__clean_up_promotion_campaigns(db)
        cls.__activate_promotion_campaigns(db)
    
    @classmethod
    def __clean_up_promotion_campaigns(cls, db: Session) -> None:
        expired_promotion_campaigns = cls.__get_expired_promotion_campaigns(db)
        
        logger.info(f"Found {len(expired_promotion_campaigns)} expired promotion campaigns to finish")
        if not expired_promotion_campaigns:
            return
        
        for promotion_campaign in expired_promotion_campaigns:
            logger.info(f"Finishing promotion campaign: {promotion_campaign.name}")
            promotion_campaign.status = PromotionCampaignStatus.FINISHED
            promotion_campaign.updated_at = datetime.now(tz=timezone.utc)
            db.add(promotion_campaign)
        db.commit()

    @classmethod
    def __get_expired_promotion_campaigns(cls, db: Session) -> List[PromotionCampaign]:
        return (
            db.query(PromotionCampaign)
            .filter(PromotionCampaign.deleted_at.is_(None))
            .filter(PromotionCampaign.end_time < datetime.now(tz=timezone.utc))
            .all()
        )
        
    @classmethod
    def __activate_promotion_campaigns(cls, db: Session) -> None:
        scheduled_promotion_campaigns = cls.__get_scheduled_promotion_campaigns(db)
        
        logger.info(f"Found {len(scheduled_promotion_campaigns)} scheduled promotion campaigns to activate")
        
        if not scheduled_promotion_campaigns:
            return

        for promotion_campaign in scheduled_promotion_campaigns:
            logger.info(f"Activating promotion campaign: {promotion_campaign.name}")
            promotion_campaign.status = PromotionCampaignStatus.ACTIVE
            promotion_campaign.updated_at = datetime.now(tz=timezone.utc)
            db.add(promotion_campaign)

        db.commit()

    @classmethod
    def __get_scheduled_promotion_campaigns(cls, db: Session) -> List[PromotionCampaign]:
        now = datetime.now(tz=timezone.utc)

        return (
            db.query(PromotionCampaign)
            .filter(PromotionCampaign.deleted_at.is_(None))
            .filter(PromotionCampaign.start_time <= now)
            .filter(
                or_(PromotionCampaign.end_time.is_(None), PromotionCampaign.end_time >= now)
            )
            .filter(PromotionCampaign.status == PromotionCampaignStatus.SCHEDULED)
            .all())
