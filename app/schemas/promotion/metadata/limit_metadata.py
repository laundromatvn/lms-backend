from typing import List

from pydantic import BaseModel

from app.enums.promotion.limit_type import LimitType
from app.enums.promotion.unit import Unit


class LimitMetadata(BaseModel):
    limit_type: LimitType
    units: List[Unit]


LIMIT_METADATA: List[LimitMetadata] = [
    ####################
    # Usage limits
    ####################
    LimitMetadata(
        limit_type=LimitType.TOTAL_USAGE,
        units=[Unit.ORDER]
    ),
    LimitMetadata(
        limit_type=LimitType.USAGE_PER_USER,
        units=[Unit.ORDER]
    ),
    LimitMetadata(
        limit_type=LimitType.USAGE_PER_STORE,
        units=[Unit.ORDER]
    ),
    LimitMetadata(
        limit_type=LimitType.USAGE_PER_TENANT,
        units=[Unit.ORDER]
    ),

    ####################
    # Amount limits
    ####################
    LimitMetadata(
        limit_type=LimitType.TOTAL_AMOUNT,
        units=[Unit.VND]
    ),
    LimitMetadata(
        limit_type=LimitType.AMOUNT_PER_USER,
        units=[Unit.VND]
    ),
    LimitMetadata(
        limit_type=LimitType.AMOUNT_PER_STORE,
        units=[Unit.VND]
    ),
    LimitMetadata(
        limit_type=LimitType.AMOUNT_PER_TENANT,
        units=[Unit.VND]
    ),
]
