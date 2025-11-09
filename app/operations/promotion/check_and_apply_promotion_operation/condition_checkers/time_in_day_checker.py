from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo

from app.enums.promotion.condition_type import ConditionType
from app.enums.promotion.operator import Operator
from app.models.machine import Machine, MachineType
from app.models.order import Order, OrderDetail
from app.libs.database import get_db_session

from .base import BasePromotionConditionChecker, OrderPromotionContext
from .registry import PromotionConditionCheckerRegistry
from ..utils import apply_operator


CONDITION_TYPE = ConditionType.TIME_IN_DAY


@PromotionConditionCheckerRegistry.register(CONDITION_TYPE)
class TimeInDayPromotionConditionChecker(BasePromotionConditionChecker):
    condition_type = CONDITION_TYPE

    def check(
        self,
        condition,
        context: OrderPromotionContext,
    ) -> bool:
        """
        Check if order's time in day matches the condition.

        Checker will extract the time from the order's created_at and compare it with the condition's value.

        For TIME_IN_DAY condition:
        - value: ["2025-11-06T17:00:00.000Z", "2025-11-06T23:00:00.000Z"],
        - operator: BETWEEN, NOT_BETWEEN
        """
        if not context.order:
            return condition.operator == Operator.NOT_BETWEEN

        condition_time_in_day = self.__format_condition_value(condition.value, context.time_zone)
        order_time = context.order.created_at.astimezone(context.time_zone).time()

        if condition.operator == Operator.BETWEEN:
            return (
                condition_time_in_day[0] <= order_time
                and order_time <= condition_time_in_day[1]
            )
        elif condition.operator == Operator.NOT_BETWEEN:
            return not (
                condition_time_in_day[0] <= order_time
                and order_time <= condition_time_in_day[1]
            )
        else:
            raise ValueError(
                f"Unsupported operator {condition.operator} for TIME_IN_DAY condition. "
                f"Only BETWEEN and NOT_BETWEEN are supported."
            )

    def __format_condition_value(
        self, condition_value: list, time_zone: ZoneInfo = timezone(timedelta(hours=7))
    ) -> list:
        """
        Parse ISO datetime strings and extract time components.

        Args:
            condition_value: List of ISO datetime strings like ["2025-11-08T02:00:00.000Z", ...]
            time_zone: Time zone to use for parsing the datetime strings
        Returns:
            List of time objects
        """
        result = []
        for time_str in condition_value:
            # Handle ISO format with 'Z' suffix (UTC) - replace Z with +00:00 for fromisoformat
            normalized_str = time_str.replace("Z", "+00:00")
            # Parse ISO datetime and extract time component
            dt = datetime.fromisoformat(normalized_str)
            dt = dt.astimezone(time_zone)
            result.append(dt.time())
        return result
