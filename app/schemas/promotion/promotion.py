import datetime
from typing import List
import uuid

from pydantic import BaseModel, field_serializer

from app.models.promotion_campaign import PromotionCampaignStatus
from app.schemas.pagination import Pagination
from app.schemas.promotion.base import Condition, Reward, Limit
from app.schemas.promotion.metadata import (
    ConditionMetadata,
    RewardMetadata,
    LimitMetadata,
)
from app.utils.timezone import to_local


class PromotionCampaignSerializer(BaseModel):
    id: uuid.UUID
    created_at: datetime.datetime
    updated_at: datetime.datetime
    deleted_at: datetime.datetime | None = None
    created_by: uuid.UUID | None = None
    updated_by: uuid.UUID | None = None
    deleted_by: uuid.UUID | None = None
    name: str
    description: str | None = None
    status: PromotionCampaignStatus
    tenant_id: uuid.UUID | None = None
    start_time: datetime.datetime
    end_time: datetime.datetime | None = None
    conditions: list[Condition]
    rewards: list[Reward]
    limits: list[Limit]

    @field_serializer('start_time')
    def serialize_start_time(self, dt: datetime.datetime | None, _info) -> datetime.datetime | None:
        """Convert UTC datetime to local timezone (Vietnam) for API responses."""
        if dt is None:
            return None
        return to_local(dt)
    
    @field_serializer('end_time')
    def serialize_end_time(self, dt: datetime.datetime | None, _info) -> datetime.datetime | None:
        """Convert UTC datetime to local timezone (Vietnam) for API responses."""
        if dt is None:
            return None
        return to_local(dt)
    
    @field_serializer('created_at')
    def serialize_created_at(self, dt: datetime.datetime | None, _info) -> datetime.datetime | None:
        """Convert UTC datetime to local timezone (Vietnam) for API responses."""
        if dt is None:
            return None
        return to_local(dt)
    
    @field_serializer('updated_at')
    def serialize_updated_at(self, dt: datetime.datetime | None, _info) -> datetime.datetime | None:
        """Convert UTC datetime to local timezone (Vietnam) for API responses."""
        if dt is None:
            return None
        return to_local(dt)
    
    @field_serializer('deleted_at')
    def serialize_deleted_at(self, dt: datetime.datetime | None, _info) -> datetime.datetime | None:
        """Convert UTC datetime to local timezone (Vietnam) for API responses."""
        if dt is None:
            return None
        return to_local(dt)


class PromotionCampaignCreate(BaseModel):
    name: str
    description: str | None = None
    status: PromotionCampaignStatus
    start_time: datetime.datetime
    end_time: datetime.datetime | None = None
    conditions: list[Condition]
    rewards: list[Reward]
    limits: list[Limit]


class PromotionCampaignUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    status: PromotionCampaignStatus | None = None
    start_time: datetime.datetime | None = None
    end_time: datetime.datetime | None = None
    conditions: list[Condition] | None = None
    rewards: list[Reward] | None = None
    limits: list[Limit] | None = None


class ListPromotionCampaignQueryParams(Pagination):
    tenant_id: uuid.UUID | None = None
    status: PromotionCampaignStatus | None = None
    start_time: datetime.datetime | None = None
    end_time: datetime.datetime | None = None
    query: str | None = None
    order_by: str | None = "created_at"
    order_direction: str | None = "desc"


class PromotionMetadata(BaseModel):
    conditions: List[ConditionMetadata]
    rewards: List[RewardMetadata]
    limits: List[LimitMetadata]


