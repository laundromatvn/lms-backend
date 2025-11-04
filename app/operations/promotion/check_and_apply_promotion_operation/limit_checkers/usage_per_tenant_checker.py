from decimal import Decimal
from uuid import UUID

from app.enums.promotion.limit_type import LimitType

from .base import BaseLimitChecker
from .registry import LimitCheckerRegistry
from .context import LimitCheckContext


LIMIT_TYPE = LimitType.USAGE_PER_TENANT


@LimitCheckerRegistry.register(LIMIT_TYPE)
class UsagePerTenantLimitChecker(BaseLimitChecker):
    limit_type = LIMIT_TYPE

    def check(
        self,
        limit: Limit,
        context: LimitCheckContext,
    ) -> bool:
        """
        Check if usage per tenant limit is not exceeded.
        
        For USAGE_PER_TENANT limit:
        - value: Maximum number of times the promotion can be used by a tenant
        - unit: ORDER
        """
        if not context.tenant_id:
            return False

        if not self.db or not self.promotion_id:
            # If no DB or promotion_id, skip check (can't track usage)
            return True

        limit_value = Decimal(str(limit.value))
        
        # TODO: Query promotion usage tracking table for this tenant
        # For now, return True (always pass)
        current_usage = Decimal(0)
        
        return current_usage < limit_value

