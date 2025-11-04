from decimal import Decimal
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.enums.promotion.limit_type import LimitType
from app.models.order import Order
from app.models.payment import Payment, PaymentStatus
from app.models.store import Store

from .base import BaseLimitChecker
from .registry import LimitCheckerRegistry
from .context import LimitCheckContext


LIMIT_TYPE = LimitType.AMOUNT_PER_TENANT


@LimitCheckerRegistry.register(LIMIT_TYPE)
class AmountPerTenantLimitChecker(BaseLimitChecker):
    limit_type = LIMIT_TYPE

    def check(
        self,
        limit: Limit,
        context: LimitCheckContext,
    ) -> bool:
        """
        Check if amount per tenant limit is not exceeded.
        
        For AMOUNT_PER_TENANT limit:
        - value: Maximum total amount that can be discounted for a tenant
        - unit: VND
        """
        if not context.tenant_id:
            return False

        if not self.db:
            raise ValueError("Database session is required for AMOUNT_PER_TENANT limit checker")

        limit_value = Decimal(str(limit.value))
        tenant_id = UUID(context.tenant_id)

        # Calculate total amount for tenant from successful payments
        # Join through Store to get tenant_id
        total_amount_result = (
            self.db.query(func.sum(Payment.total_amount))
            .join(Order, Payment.order_id == Order.id)
            .join(Store, Order.store_id == Store.id)
            .filter(
                Store.tenant_id == tenant_id,
                Order.deleted_at.is_(None),
                Store.deleted_at.is_(None),
                Payment.status == PaymentStatus.SUCCESS,
                Payment.deleted_at.is_(None),
            )
            .scalar()
        )

        tenant_total_amount = Decimal(total_amount_result or 0)

        return tenant_total_amount < limit_value

