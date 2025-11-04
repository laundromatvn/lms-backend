from decimal import Decimal

from app.enums.promotion.condition_type import ConditionType
from app.enums.promotion.operator import Operator

from .base import BasePromotionConditionChecker, OrderPromotionContext
from .registry import PromotionConditionCheckerRegistry
from ..utils import apply_operator


CONDITION_TYPE = ConditionType.TOTAL_AMOUNT


@PromotionConditionCheckerRegistry.register(CONDITION_TYPE)
class TotalAmountPromotionConditionChecker(BasePromotionConditionChecker):
    condition_type = CONDITION_TYPE

    def check(
        self,
        condition,
        context: OrderPromotionContext,
    ) -> bool:
        """
        Check if order's total amount matches the condition.
        
        For TOTAL_AMOUNT condition:
        - value: Numeric value (amount threshold)
        - operator: GREATER_THAN, GREATER_THAN_OR_EQUAL, LESS_THAN, 
                   LESS_THAN_OR_EQUAL, EQUAL, NOT_EQUAL, BETWEEN, NOT_BETWEEN
        """
        order_amount = context.order_total_amount
        condition_value = Decimal(str(condition.value))

        return apply_operator(condition.operator, order_amount, condition_value)

