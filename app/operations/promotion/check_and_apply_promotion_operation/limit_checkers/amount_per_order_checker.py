from decimal import Decimal

from app.enums.promotion.limit_type import LimitType
from app.schemas.promotion.base import Limit

from .base import BaseLimitChecker
from .registry import LimitCheckerRegistry
from .context import LimitCheckContext
from .result import LimitCheckResult


LIMIT_TYPE = LimitType.AMOUNT_PER_ORDER


@LimitCheckerRegistry.register(LIMIT_TYPE)
class AmountPerOrderLimitChecker(BaseLimitChecker):
    limit_type = LIMIT_TYPE

    def check_and_apply(
        self,
        calculated_reward: Decimal,
        limit: Limit,
        context: LimitCheckContext,
    ) -> LimitCheckResult:
        """
        Check and apply amount per order limit.
        
        For AMOUNT_PER_ORDER limit:
        - value: Maximum discount amount per order (cap)
        - unit: VND
        
        This is a capping limit, not a rejecting limit.
        It always allows the promotion, but returns the maximum discount cap.
        """
        max_discount_cap = Decimal(str(limit.value))
        # This is a capping limit - always allow but return the cap
        return LimitCheckResult.allow_with_cap(max_discount_cap)
