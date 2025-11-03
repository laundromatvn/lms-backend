from typing import Any, List

from pydantic import BaseModel, Field

from app.enums.promotion.condition_type import ConditionType
from app.enums.promotion.operator import Operator
from app.models.user import UserRole


class ConditionMetadata(BaseModel):
    condition_type: ConditionType
    operators: List[Operator]
    options: List[Any] | None = None
    allowed_roles: List[UserRole] = Field(default_factory=list, exclude=True)


CONDITION_METADATA: List[ConditionMetadata] = [
    ConditionMetadata(
        condition_type=ConditionType.TENANTS,
        operators=[Operator.IN, Operator.NOT_IN],
        allowed_roles=[UserRole.ADMIN],
    ),
    ConditionMetadata(
        condition_type=ConditionType.STORES,
        operators=[Operator.IN, Operator.NOT_IN],
        allowed_roles=[UserRole.ADMIN, UserRole.TENANT_ADMIN],
    )
]
