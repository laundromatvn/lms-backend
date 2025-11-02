import datetime
import uuid

from pydantic import BaseModel

from app.models.promotion_campaign import PromotionCampaignStatus
from app.schemas.pagination import Pagination
from app.schemas.promotion.base import Condition, Reward, Limit


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
    end_time: datetime.datetime
    conditions: list[Condition]
    rewards: list[Reward]
    limits: list[Limit]


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
