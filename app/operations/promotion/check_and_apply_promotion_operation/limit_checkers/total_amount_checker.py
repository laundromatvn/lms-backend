from decimal import Decimal
from uuid import UUID

from app.enums.promotion.limit_type import LimitType

from .base import BaseLimitChecker
from .registry import LimitCheckerRegistry
from .context import LimitCheckContext


LIMIT_TYPE = LimitType.TOTAL_AMOUNT


@LimitCheckerRegistry.register(LIMIT_TYPE)
class TotalAmountLimitChecker(BaseLimitChecker):
    limit_type = LIMIT_TYPE

    def check(
        self,
        limit: Limit,
        context: LimitCheckContext,
    ) -> bool:
        """
        Check if total amount limit is not exceeded.
        
        For TOTAL_AMOUNT limit:
        - value: Maximum total amount that can be discounted
        - unit: VND
        """
        if not self.db or not self.promotion_id:
            # If no DB or promotion_id, skip check (can't track amount)
            return True

        limit_value = Decimal(str(limit.value))
        
        # TODO: Query promotion usage tracking table for total amount
        # For now, return True (always pass)
        current_amount = Decimal(0)
        
        return current_amount < limit_value

