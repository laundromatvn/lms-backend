from typing import List

from pydantic import BaseModel

from app.enums.promotion.reward_type import RewardType
from app.enums.promotion.unit import Unit


class RewardMetadata(BaseModel):
    reward_type: RewardType
    units: List[Unit]


REWARD_METADATA: List[RewardMetadata] = [
    RewardMetadata(
        reward_type=RewardType.FIXED_AMOUNT,
        units=[Unit.VND]
    ),
    RewardMetadata(
        reward_type=RewardType.PERCENTAGE_AMOUNT,
        units=[Unit.PERCENTAGE]
    ),
]
