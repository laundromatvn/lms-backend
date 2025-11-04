from typing import List

from app.enums.promotion.condition_type import ConditionType
from app.enums.promotion.operator import Operator

from .base import BasePromotionConditionChecker, OrderPromotionContext
from .registry import PromotionConditionCheckerRegistry


CONDITION_TYPE = ConditionType.STORES


@PromotionConditionCheckerRegistry.register(CONDITION_TYPE)
class StorePromotionConditionChecker(BasePromotionConditionChecker):
    condition_type = CONDITION_TYPE

    def check(
        self,
        condition,
        context: OrderPromotionContext,
    ) -> bool:
        """
        Check if order's store matches the condition.
        
        For STORES condition:
        - value: List of store IDs (UUIDs as strings)
        - operator: IN, NOT_IN
        """
        if not context.store_id:
            return False

        condition_value = condition.value
        if not isinstance(condition_value, list):
            condition_value = [condition_value]

        # Convert both to strings for comparison
        store_id_str = str(context.store_id)
        condition_store_ids = [str(sid) for sid in condition_value]

        if condition.operator == Operator.IN:
            return store_id_str in condition_store_ids
        elif condition.operator == Operator.NOT_IN:
            return store_id_str not in condition_store_ids
        else:
            raise ValueError(
                f"Unsupported operator {condition.operator} for STORES condition. "
                f"Only IN and NOT_IN are supported."
            )

