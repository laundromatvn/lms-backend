from typing import List

from pydantic import BaseModel, Field

from app.enums.promotion.limit_type import LimitType
from app.enums.promotion.unit import Unit
from app.models.user import UserRole


class LimitMetadata(BaseModel):
    limit_type: LimitType
    units: List[Unit]
    allowed_roles: List[UserRole] = Field(default_factory=list, exclude=True)


LIMIT_METADATA: List[LimitMetadata] = [
    ####################
    # Amount limits
    ####################
    LimitMetadata(
        limit_type=LimitType.AMOUNT_PER_ORDER,
        units=[Unit.VND],
        allowed_roles=[UserRole.ADMIN, UserRole.TENANT_ADMIN],
    ),
]
