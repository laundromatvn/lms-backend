import datetime
from enum import Enum
from typing import Optional
import uuid

from sqlalchemy import (
    Column, Enum as SQLEnum,
    String, DateTime, Text, JSON,
    func, ForeignKey
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, validates

from app.libs.database import Base
from app.schemas.promotion.base import Condition, Reward, Limit
from app.utils.timezone import to_utc


class PromotionCampaignStatus(str, Enum):
    DRAFT = "DRAFT" # when admin is creating the campaign
    SCHEDULED = "SCHEDULED" # when campaign is scheduled to start and end
    ACTIVE = "ACTIVE" # when campaign is active and can be used
    PAUSED = "PAUSED" # when campaign is paused and cannot be used
    INACTIVE = "INACTIVE" # when campaign is inactive and cannot be used
    FINISHED = "FINISHED" # when campaign is finished and cannot be used


class PromotionCampaign(Base):
    __tablename__ = "promotion_campaigns"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)

    created_at = Column(DateTime(timezone=True),nullable=False, default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, default=func.now(), onupdate=func.now())
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    
    created_by = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=True, index=True)
    updated_by = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=True, index=True)
    deleted_by = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=True, index=True)

    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(
        SQLEnum(PromotionCampaignStatus, name="promotion_campaign_status", create_type=False),
        nullable=False,
        default=PromotionCampaignStatus.DRAFT,
        index=True)
    
    tenant_id = Column(UUID(as_uuid=True), ForeignKey('tenants.id'), nullable=True, index=True)

    start_time = Column(DateTime(timezone=True), nullable=False, index=True)
    end_time = Column(DateTime(timezone=True), nullable=True, index=True)
    
    conditions = Column(JSON, nullable=False, default=list) # JSON field to store list of Condition schemas
    rewards = Column(JSON, nullable=False, default=list) # JSON field to store list of Reward schemas
    limits = Column(JSON, nullable=False, default=list) # JSON field to store list of Limit schemas
    
    # Relationships
    tenant = relationship("Tenant", back_populates="promotion_campaigns")
    promotion_orders = relationship("PromotionOrder", back_populates="promotion_campaign")

    @validates('conditions')
    def validate_conditions(self, key: str, conditions) -> list:
        if not isinstance(conditions, list):
            try:
                conditions = list(conditions)
            except (ValueError, TypeError):
                raise ValueError("Conditions must be a list")
            
        for condition in conditions:
            try:
                _ = Condition(**condition)
            except ValueError as e:
                raise ValueError(f"Invalid condition: {condition}. {e}")

        return conditions
    
    @validates('rewards')
    def validate_rewards(self, key: str, rewards) -> list:
        if not isinstance(rewards, list):
            try:
                rewards = list(rewards)
            except (ValueError, TypeError):
                raise ValueError("Rewards must be a list")
            
        for reward in rewards:
            try:
                _ = Reward(**reward)
            except ValueError as e:
                raise ValueError(f"Invalid reward: {reward}. {e}")
        
        return rewards

    @validates('limits')
    def validate_limits(self, key: str, limits) -> list:
        if not isinstance(limits, list):
            try:
                limits = list(limits)
            except (ValueError, TypeError):
                raise ValueError("Limits must be a list")
            
        for limit in limits:
            try:
                _ = Limit(**limit)
            except ValueError as e:
                raise ValueError(f"Invalid limit: {limit}. {e}")
        
        return limits

    @validates('start_time')
    def validate_start_time(self, key: str, start_time) -> datetime.datetime:
        if not isinstance(start_time, datetime.datetime):
            try:
                start_time = datetime.datetime.fromisoformat(start_time)
            except (ValueError, TypeError):
                raise ValueError("Start time must be a datetime object")

        # Convert to UTC before storing in database
        return to_utc(start_time)
    
    @validates('end_time')
    def validate_end_time(self, key: str, end_time) -> datetime.datetime:
        if end_time is None:
            return end_time

        if not isinstance(end_time, datetime.datetime):
            try:
                end_time = datetime.datetime.fromisoformat(end_time)
            except (ValueError, TypeError):
                raise ValueError("End time must be a datetime object")

        # Convert to UTC before storing in database
        end_time_utc = to_utc(end_time)
        
        # Check if end time is in the future (compare in UTC)
        if end_time_utc < datetime.datetime.now(datetime.timezone.utc):
            raise ValueError("End time must be in the future")

        return end_time_utc

    @property
    def is_active(self) -> bool:
        return self.status == PromotionCampaignStatus.ACTIVE and self.deleted_at is None
    
    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None

    def soft_delete(self, deleted_by: Optional[uuid.UUID] = None) -> None:
        self.deleted_at = func.now()
        self.deleted_by = deleted_by
        self.status = PromotionCampaignStatus.INACTIVE

    def to_dict(self):
        return {
            "id": self.id,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "deleted_at": self.deleted_at,
            "name": self.name,
            "description": self.description,
            "status": self.status,
            "tenant_id": self.tenant_id,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "conditions": self.conditions,
            "rewards": self.rewards,
            "limits": self.limits
        }
