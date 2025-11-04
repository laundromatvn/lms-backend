from typing import List

from pydantic import BaseModel, Field

from app.enums.promotion.reward_type import RewardType
from app.enums.promotion.unit import Unit
from app.models.user import UserRole


class RewardMetadata(BaseModel):
    reward_type: RewardType
    units: List[Unit]
    allowed_roles: List[UserRole] = Field(default_factory=list, exclude=True)

REWARD_METADATA: List[RewardMetadata] = [
    ################
    # Amount rewards
    ################
    RewardMetadata(
        reward_type=RewardType.FIXED_AMOUNT,
        units=[Unit.VND],
        allowed_roles=[UserRole.ADMIN, UserRole.TENANT_ADMIN],
    ),
    RewardMetadata(
        reward_type=RewardType.PERCENTAGE_AMOUNT,
        units=[Unit.PERCENTAGE],
        allowed_roles=[UserRole.ADMIN, UserRole.TENANT_ADMIN],
    ),
]
