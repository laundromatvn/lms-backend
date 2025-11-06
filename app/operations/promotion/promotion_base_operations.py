import datetime
from typing import List
from uuid import UUID

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.libs.database import with_db_session_classmethod
from app.models.user import User
from app.models.promotion_campaign import PromotionCampaign, PromotionCampaignStatus
from app.models.tenant_member import TenantMember
from app.schemas.promotion.promotion import (
    ListPromotionCampaignQueryParams,
    PromotionCampaignCreate,
    PromotionCampaignUpdate
)
from app.utils.timezone import to_utc


class PromotionBaseOperations:

    @classmethod
    @with_db_session_classmethod
    def list(
        cls,
        db: Session,
        current_user: User,
        query_params: ListPromotionCampaignQueryParams,
    ) -> tuple[int, list[PromotionCampaign]]:
        base_query = (
            db.query(PromotionCampaign)
            .filter(
                PromotionCampaign.deleted_at.is_(None),
                PromotionCampaign.status.not_in([PromotionCampaignStatus.INACTIVE])
            )
        )
        
        # Get system and tenant promotion campaigns
        if not current_user.is_admin:
            tenant_ids = cls._get_tenant_ids(db, current_user)

            base_query = base_query.filter(
                or_(PromotionCampaign.tenant_id.in_(tenant_ids), 
                    PromotionCampaign.tenant_id == None))
            
        if query_params.status:
            base_query = base_query.filter(PromotionCampaign.status == query_params.status)
        
        if query_params.start_time:
            start_time_utc = to_utc(query_params.start_time)
            base_query = base_query.filter(PromotionCampaign.start_time >= start_time_utc)
        
        if query_params.end_time:
            end_time_utc = to_utc(query_params.end_time)
            base_query = base_query.filter(PromotionCampaign.end_time <= end_time_utc)

        if query_params.query:
            base_query = base_query.filter(
                PromotionCampaign.name.ilike(f"%{query_params.query}%"),
            )
        
        if query_params.order_by:
            if query_params.order_direction == "asc":
                base_query = base_query.order_by(getattr(PromotionCampaign, query_params.order_by).asc())
            else:
                base_query = base_query.order_by(getattr(PromotionCampaign, query_params.order_by).desc())
        else:
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
        
        if not current_user.is_admin:
            tenant_member = db.query(TenantMember).filter(TenantMember.user_id == current_user.id).first()
            promotion_campaign.tenant_id = tenant_member.tenant_id

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

        update_data = payload.model_dump(exclude_unset=True, exclude={"conditions", "rewards", "limits"})

        # accept [] as empty list
        if isinstance(payload.conditions, list):
            update_data["conditions"] = [condition.model_dump(mode='json') for condition in payload.conditions]
        if isinstance(payload.rewards, list):
            update_data["rewards"] = [reward.model_dump(mode='json') for reward in payload.rewards]
        if isinstance(payload.limits, list):
            update_data["limits"] = [limit.model_dump(mode='json') for limit in payload.limits]
        
        for field, value in update_data.items():
            if hasattr(promotion_campaign, field):
                setattr(promotion_campaign, field, value)
                
        update_data["updated_by"] = current_user.id

        db.commit()
        db.refresh(promotion_campaign)
        
        return promotion_campaign

    @classmethod
    @with_db_session_classmethod
    def delete(
        cls,
        db: Session,
        current_user: User,
        promotion_campaign_id: UUID,
    ) -> None:
        promotion_campaign = cls._get_promotion_campaign(db, current_user, promotion_campaign_id)

        promotion_campaign.soft_delete(current_user.id)
        db.add(promotion_campaign)
        db.commit()

    @classmethod
    @with_db_session_classmethod
    def schedule(
        cls,
        db: Session,
        current_user: User,
        promotion_campaign_id: UUID,
    ) -> PromotionCampaign:
        promotion_campaign = cls._get_promotion_campaign(db, current_user, promotion_campaign_id)
        
        if promotion_campaign.deleted_at is not None:
            raise ValueError("Cannot schedule a deleted promotion campaign")
        
        if promotion_campaign.status != PromotionCampaignStatus.DRAFT:
            raise ValueError(f"Cannot schedule promotion campaign with status {promotion_campaign.status.value}. Only DRAFT campaigns can be scheduled.")
        
        promotion_campaign.status = PromotionCampaignStatus.SCHEDULED
        promotion_campaign.updated_by = current_user.id
        db.commit()
        db.refresh(promotion_campaign)
        
        return promotion_campaign

    @classmethod
    @with_db_session_classmethod
    def pause(
        cls,
        db: Session,
        current_user: User,
        promotion_campaign_id: UUID,
    ) -> PromotionCampaign:
        promotion_campaign = cls._get_promotion_campaign(db, current_user, promotion_campaign_id)
        
        if promotion_campaign.deleted_at is not None:
            raise ValueError("Cannot pause a deleted promotion campaign")
        
        if promotion_campaign.status not in [PromotionCampaignStatus.ACTIVE, PromotionCampaignStatus.SCHEDULED]:
            raise ValueError(f"Cannot pause promotion campaign with status {promotion_campaign.status.value}. Only ACTIVE or SCHEDULED campaigns can be paused.")
        
        promotion_campaign.status = PromotionCampaignStatus.PAUSED
        promotion_campaign.updated_by = current_user.id
        db.commit()
        db.refresh(promotion_campaign)
        
        return promotion_campaign

    @classmethod
    @with_db_session_classmethod
    def resume(
        cls,
        db: Session,
        current_user: User,
        promotion_campaign_id: UUID,
    ) -> PromotionCampaign:
        promotion_campaign = cls._get_promotion_campaign(db, current_user, promotion_campaign_id)
        
        if promotion_campaign.deleted_at is not None:
            raise ValueError("Cannot resume a deleted promotion campaign")
        
        if promotion_campaign.status != PromotionCampaignStatus.PAUSED:
            raise ValueError(f"Cannot resume promotion campaign with status {promotion_campaign.status.value}. Only PAUSED campaigns can be resumed.")
        
        # Determine the appropriate status based on current time
        now = datetime.datetime.now(datetime.timezone.utc)
        if promotion_campaign.start_time <= now:
            # Campaign should be active if start time has passed
            promotion_campaign.status = PromotionCampaignStatus.ACTIVE
        else:
            # Campaign should be scheduled if start time is in the future
            promotion_campaign.status = PromotionCampaignStatus.SCHEDULED
        
        promotion_campaign.updated_by = current_user.id
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
