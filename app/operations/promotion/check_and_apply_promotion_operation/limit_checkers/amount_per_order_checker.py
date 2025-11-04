from decimal import Decimal

from app.enums.promotion.limit_type import LimitType

from .base import BaseLimitChecker
from .registry import LimitCheckerRegistry
from .context import LimitCheckContext


LIMIT_TYPE = LimitType.AMOUNT_PER_ORDER


@LimitCheckerRegistry.register(LIMIT_TYPE)
class AmountPerOrderLimitChecker(BaseLimitChecker):
    limit_type = LIMIT_TYPE

    def check(
        self,
        limit: Limit,
        context: LimitCheckContext,
    ) -> bool:
        """
        Check if amount per order limit is not exceeded.
        
        For AMOUNT_PER_ORDER limit:
        - value: Maximum discount amount per order
        - unit: VND
        """
        limit_value = Decimal(str(limit.value))
        order_amount = context.order_total_amount
        return order_amount < limit_value

