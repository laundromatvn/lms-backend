from decimal import Decimal
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.enums.promotion.condition_type import ConditionType
from app.models.order import Order
from app.models.payment import Payment, PaymentStatus

from .base import BasePromotionConditionChecker, OrderPromotionContext
from .registry import PromotionConditionCheckerRegistry
from ..utils import apply_operator


CONDITION_TYPE = ConditionType.AMOUNT_PER_USER


@PromotionConditionCheckerRegistry.register(CONDITION_TYPE)
class AmountPerUserPromotionConditionChecker(BasePromotionConditionChecker):
    condition_type = CONDITION_TYPE

    def check(
        self,
        condition,
        context: OrderPromotionContext,
    ) -> bool:
        """
        Check if user's total order amount matches the condition.
        
        For AMOUNT_PER_USER condition:
        - value: Numeric value (amount threshold)
        - operator: GREATER_THAN, GREATER_THAN_OR_EQUAL, LESS_THAN, 
                   LESS_THAN_OR_EQUAL, EQUAL, NOT_EQUAL, BETWEEN, NOT_BETWEEN
        
        This checks the total amount of all successful orders for the user.
        """
        if not context.user_id:
            return False

        user_id = UUID(context.user_id)
        condition_value = Decimal(str(condition.value))

        if not self.db:
            raise ValueError("Database session is required for AMOUNT_PER_USER condition checker")

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

        return apply_operator(condition.operator, user_total_amount, condition_value)

