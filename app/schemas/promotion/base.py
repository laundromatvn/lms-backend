from typing import Any

from pydantic import BaseModel

from app.enums.promotion.condition_type import ConditionType
from app.enums.promotion.operator import Operator
from app.enums.promotion.reward_type import RewardType
from app.enums.promotion.limit_type import LimitType
from app.enums.promotion.unit import Unit


class Condition(BaseModel):
    type: ConditionType
    operator: Operator
    value: Any
    display_value: str | None = None


class Reward(BaseModel):
    type: RewardType
    value: Any
    unit: Unit


class Limit(BaseModel):
    type: LimitType
    value: Any
    unit: Unit
