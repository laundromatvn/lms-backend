from app.enums.promotion.condition_type import ConditionType
from app.enums.promotion.operator import Operator

from .base import BasePromotionConditionChecker, OrderPromotionContext
from .registry import PromotionConditionCheckerRegistry


CONDITION_TYPE = ConditionType.TENANTS


@PromotionConditionCheckerRegistry.register(CONDITION_TYPE)
class TenantPromotionConditionChecker(BasePromotionConditionChecker):
    condition_type = CONDITION_TYPE

    def check(
        self,
        condition,
        context: OrderPromotionContext,
    ) -> bool:
        """
        Check if order's tenant matches the condition.
        
        For TENANTS condition:
        - value: List of tenant IDs (UUIDs as strings)
        - operator: IN, NOT_IN
        """
        if not context.tenant_id:
            return condition.operator == Operator.NOT_IN

        condition_value = condition.value
        if not isinstance(condition_value, list):
            condition_value = [condition_value]

        tenant_id_str = str(context.tenant_id)
        condition_tenant_ids = [str(tid) for tid in condition_value]

        if condition.operator == Operator.IN:
            return tenant_id_str in condition_tenant_ids
        elif condition.operator == Operator.NOT_IN:
            return tenant_id_str not in condition_tenant_ids
        else:
            raise ValueError(
                f"Unsupported operator {condition.operator} for TENANTS condition. "
                f"Only IN and NOT_IN are supported."
            )

