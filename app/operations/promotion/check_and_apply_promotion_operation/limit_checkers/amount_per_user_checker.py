from decimal import Decimal
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.enums.promotion.limit_type import LimitType
from app.models.order import Order
from app.models.payment import Payment, PaymentStatus

from .base import BaseLimitChecker
from .registry import LimitCheckerRegistry
from .context import LimitCheckContext


LIMIT_TYPE = LimitType.AMOUNT_PER_USER


@LimitCheckerRegistry.register(LIMIT_TYPE)
class AmountPerUserLimitChecker(BaseLimitChecker):
    limit_type = LIMIT_TYPE

    def check(
        self,
        limit: Limit,
        context: LimitCheckContext,
    ) -> bool:
        """
        Check if amount per user limit is not exceeded.
        
        For AMOUNT_PER_USER limit:
        - value: Maximum total amount that can be discounted for a user
        - unit: VND
        """
        if not context.user_id:
            return False

        if not self.db:
            raise ValueError("Database session is required for AMOUNT_PER_USER limit checker")

        limit_value = Decimal(str(limit.value))
        user_id = UUID(context.user_id)

        # Calculate total amount for user from successful payments
        total_amount_result = (
            self.db.query(func.sum(Payment.total_amount))
            .join(Order, Payment.order_id == Order.id)
            .filter(
                Order.created_by == user_id,
                Order.deleted_at.is_(None),
                Payment.status == PaymentStatus.SUCCESS,
                Payment.deleted_at.is_(None),
            )
            .scalar()
        )

        user_total_amount = Decimal(total_amount_result or 0)

        return user_total_amount < limit_value

