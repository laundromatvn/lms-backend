from decimal import Decimal

from app.enums.promotion.condition_type import ConditionType
from app.enums.promotion.operator import Operator
from app.models.machine import Machine, MachineType
from app.models.order import Order, OrderDetail
from app.libs.database import get_db_session

from .base import BasePromotionConditionChecker, OrderPromotionContext
from .registry import PromotionConditionCheckerRegistry
from ..utils import apply_operator


CONDITION_TYPE = ConditionType.MACHINE_TYPES


@PromotionConditionCheckerRegistry.register(CONDITION_TYPE)
class MachineTypesPromotionConditionChecker(BasePromotionConditionChecker):
    condition_type = CONDITION_TYPE

    def check(
        self,
        condition,
        context: OrderPromotionContext,
    ) -> bool:
        """
        Check if order's machine types matches the condition.
        
        For MACHINE_TYPES condition:
        - value: List of machine type IDs (UUIDs as strings)
        - operator: IN, NOT_IN
        """
        if not context.order:
            return condition.operator == Operator.NOT_IN

        condition_machine_types = self.__format_condition_value(condition.value)

        if condition.operator == Operator.IN:
            if context.order.total_washer > 0 and MachineType.WASHER in condition_machine_types:
                return True
            elif context.order.total_dryer > 0 and MachineType.DRYER in condition_machine_types:
                return True
            else:
                return False
        elif condition.operator == Operator.NOT_IN:
            if context.order.total_washer > 0 and MachineType.WASHER in condition_machine_types:
                return False
            elif context.order.total_dryer > 0 and MachineType.DRYER in condition_machine_types:
                return False
            else:
                return True
        else:
            raise ValueError(
                f"Unsupported operator {condition.operator} for MACHINE_TYPES condition. "
                f"Only IN and NOT_IN are supported."
            )

    def __format_condition_value(self, condition_value: list) -> list:
        return [MachineType(machine_type) for machine_type in condition_value]
