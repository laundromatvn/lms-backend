from typing import Any, List

from pydantic import BaseModel

from app.enums.promotion.condition_type import ConditionType
from app.enums.promotion.operator import Operator


class ConditionMetadata(BaseModel):
    condition_type: ConditionType
    operators: List[Operator]
    options: List[Any] | None = None


CONDITION_METADATA: List[ConditionMetadata] = [
    ConditionMetadata(
        condition_type=ConditionType.TENANTS,
        operators=[Operator.IN, Operator.NOT_IN]
    ),
    ConditionMetadata(
        condition_type=ConditionType.STORES,
        operators=[Operator.IN, Operator.NOT_IN]
    ),
    ConditionMetadata(
        condition_type=ConditionType.USERS,
        operators=[Operator.IN, Operator.NOT_IN]
    ),
]
