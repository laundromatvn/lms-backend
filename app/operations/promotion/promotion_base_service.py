from typing import List
from uuid import UUID

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.libs.database import with_db_session_classmethod
from app.models.user import User
from app.models.promotion_campaign import PromotionCampaign
from app.models.tenant_member import TenantMember
from app.schemas.promotion.promotion import (
    ListPromotionCampaignQueryParams,
    PromotionCampaignCreate,
    PromotionCampaignUpdate
)


class PromotionBaseService:

    @classmethod
    @with_db_session_classmethod
    def list(
        cls,
        db: Session,
        current_user: User,
        query_params: ListPromotionCampaignQueryParams,
    ) -> tuple[int, list[PromotionCampaign]]:
        base_query = db.query(PromotionCampaign)

        # Get system and tenant promotion campaigns
        if not current_user.is_admin:
            tenant_ids = cls._get_tenant_ids(db, current_user)

            base_query = base_query.filter(
                or_(PromotionCampaign.tenant_id.in_(tenant_ids), 
                    PromotionCampaign.tenant_id == None))

        # Order
        base_query = base_query.order_by(PromotionCampaign.created_at.desc())

        total = base_query.count()
        promotion_campaigns = base_query.all()

        return total, promotion_campaigns

    @classmethod
    @with_db_session_classmethod
    def get(
        cls,
        db: Session,
        current_user: User,
        promotion_campaign_id: UUID,
    ) -> PromotionCampaign:
        return cls._get_promotion_campaign(db, current_user, promotion_campaign_id)

    @classmethod
    @with_db_session_classmethod
    def create(
        cls,
        db: Session,
        current_user: User,
        payload: PromotionCampaignCreate,
    ) -> tuple[int, List[PromotionCampaign]]:
        conditions_json = [condition.model_dump(mode='json') for condition in payload.conditions]
        rewards_json = [reward.model_dump(mode='json') for reward in payload.rewards]
        limits_json = [limit.model_dump(mode='json') for limit in payload.limits]
        
        promotion_campaign = PromotionCampaign(
            created_by=current_user.id,
            updated_by=current_user.id,
            name=payload.name,
            description=payload.description,
            status=payload.status,
            start_time=payload.start_time,
            end_time=payload.end_time,
            conditions=conditions_json,
            rewards=rewards_json,
            limits=limits_json,
        )

        db.add(promotion_campaign)
        db.commit()
        db.refresh(promotion_campaign)

        return promotion_campaign

    @classmethod
    @with_db_session_classmethod
    def update_partially(
        cls,
        db: Session,
        current_user: User,
        promotion_campaign_id: UUID,
        payload: PromotionCampaignUpdate,
    ) -> PromotionCampaign:
        promotion_campaign = cls._get_promotion_campaign(db, current_user, promotion_campaign_id)
        
        update_data = payload.model_dump(exclude_unset=True)
        
        for field, value in update_data.items():
            if hasattr(promotion_campaign, field):
                setattr(promotion_campaign, field, value)

        db.commit()
        db.refresh(promotion_campaign)
        
        return promotion_campaign
    
    @classmethod
    def _get_promotion_campaign(
        cls,
        db: Session,
        current_user: User,
        promotion_campaign_id: UUID,
    ) -> PromotionCampaign:
        base_query = (
            db.query(PromotionCampaign).filter(PromotionCampaign.id == promotion_campaign_id)
        )
        
        if not current_user.is_admin:
            tenant_ids = cls._get_tenant_ids(db, current_user)
            base_query = base_query.filter(
                or_(PromotionCampaign.tenant_id.in_(tenant_ids), 
                    PromotionCampaign.tenant_id == None))
            
        promotion_campaign = base_query.first()
        if not promotion_campaign:
            raise ValueError("Promotion campaign not found")
        
        return promotion_campaign

    @classmethod
    def _get_tenant_ids(cls, db: Session, current_user: User) -> List[UUID]:
        result = (
            db.query(TenantMember.tenant_id)
            .filter(TenantMember.user_id == current_user.id)
            .distinct()
            .all()
        )
        return [tenant.tenant_id for tenant in result]
