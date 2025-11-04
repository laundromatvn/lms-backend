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
    # Usage limits
    ####################
    # LimitMetadata(
    #     limit_type=LimitType.TOTAL_USAGE,
    #     units=[Unit.ORDER],
    #     allowed_roles=[UserRole.ADMIN, UserRole.TENANT_ADMIN],
    # ),
    # LimitMetadata(
    #     limit_type=LimitType.USAGE_PER_USER,
    #     units=[Unit.ORDER],
    #     allowed_roles=[UserRole.ADMIN, UserRole.TENANT_ADMIN],
    # ),
    # LimitMetadata(
    #     limit_type=LimitType.USAGE_PER_STORE,
    #     units=[Unit.ORDER],
    #     allowed_roles=[UserRole.ADMIN, UserRole.TENANT_ADMIN],
    # ),
    # LimitMetadata(
    #     limit_type=LimitType.USAGE_PER_TENANT,
    #     units=[Unit.ORDER],
    #     allowed_roles=[UserRole.ADMIN, UserRole.TENANT_ADMIN],
    # ),

    ####################
    # Amount limits
    ####################
    # LimitMetadata(
    #     limit_type=LimitType.TOTAL_AMOUNT,
    #     units=[Unit.VND],
    #     allowed_roles=[UserRole.ADMIN, UserRole.TENANT_ADMIN],
    # ),
    LimitMetadata(
        limit_type=LimitType.AMOUNT_PER_ORDER,
        units=[Unit.VND],
        allowed_roles=[UserRole.ADMIN, UserRole.TENANT_ADMIN],
    ),
    # LimitMetadata(
    #     limit_type=LimitType.AMOUNT_PER_USER,
    #     units=[Unit.VND],
    #     allowed_roles=[UserRole.ADMIN, UserRole.TENANT_ADMIN],
    # ),
    # LimitMetadata(
    #     limit_type=LimitType.AMOUNT_PER_STORE,
    #     units=[Unit.VND],
    #     allowed_roles=[UserRole.ADMIN, UserRole.TENANT_ADMIN],
    # ),
    # LimitMetadata(
    #     limit_type=LimitType.AMOUNT_PER_TENANT,
    #     units=[Unit.VND],
    #     allowed_roles=[UserRole.ADMIN, UserRole.TENANT_ADMIN],
    # ),
]
