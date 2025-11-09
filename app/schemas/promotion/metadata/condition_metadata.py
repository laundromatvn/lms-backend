from typing import Any, List

from pydantic import BaseModel, Field

from app.enums.promotion.condition_type import ConditionType, ConditionValueType
from app.enums.promotion.operator import Operator
from app.models.machine import MachineType
from app.models.user import UserRole


class ConditionMetadata(BaseModel):
    condition_type: ConditionType
    operators: List[Operator]
    options: List[Any] | None = None
    allowed_roles: List[UserRole] = Field(default_factory=list, exclude=True)
    value_type: str | None = None


CONDITION_METADATA: List[ConditionMetadata] = [
    # Object conditions
    ConditionMetadata(
        condition_type=ConditionType.TENANTS,
        operators=[Operator.IN, Operator.NOT_IN],
        allowed_roles=[UserRole.ADMIN],
        value_type=ConditionValueType.OPTIONS,
    ),
    ConditionMetadata(
        condition_type=ConditionType.STORES,
        operators=[Operator.IN, Operator.NOT_IN],
        allowed_roles=[UserRole.ADMIN, UserRole.TENANT_ADMIN],
        value_type=ConditionValueType.OPTIONS,
    ),
    # Amount conditions
    ConditionMetadata(
        condition_type=ConditionType.TOTAL_AMOUNT,
        operators=[
            Operator.EQUAL, Operator.NOT_EQUAL,
            Operator.GREATER_THAN, Operator.GREATER_THAN_OR_EQUAL,
            Operator.LESS_THAN, Operator.LESS_THAN_OR_EQUAL,
        ],
        allowed_roles=[UserRole.ADMIN, UserRole.TENANT_ADMIN],
        value_type=ConditionValueType.NUMBER,
    ),
    # Machine conditions
    ConditionMetadata(
        condition_type=ConditionType.MACHINE_TYPES,
        operators=[Operator.IN, Operator.NOT_IN],
        allowed_roles=[UserRole.ADMIN, UserRole.TENANT_ADMIN],
        value_type=ConditionValueType.OPTIONS,
        options=[
            { "value": MachineType.WASHER.value, "label": MachineType.WASHER.value },
            { "value": MachineType.DRYER.value, "label": MachineType.DRYER.value },
        ],
    ),
    # Time range conditions
    # Example 1: "09:00 - 18:00"
    ConditionMetadata(
        condition_type=ConditionType.TIME_IN_DAY,
        operators=[Operator.BETWEEN, Operator.NOT_BETWEEN],
        allowed_roles=[UserRole.ADMIN, UserRole.TENANT_ADMIN],
        value_type=ConditionValueType.TIME_IN_DAY,
    ),
]
