"""
Utility functions for promotion condition checking.
"""
from decimal import Decimal
from typing import Any

from app.enums.promotion.operator import Operator


def apply_operator(
    operator: Operator,
    left_value: Decimal | Any,
    right_value: Decimal | Any,
    right_value_2: Decimal | Any | None = None,
) -> bool:
    """
    Apply an operator to compare two values.
    
    Args:
        operator: The operator to apply
        left_value: The left operand (typically the actual value)
        right_value: The right operand (typically the condition value)
        right_value_2: Optional second right operand for BETWEEN/NOT_BETWEEN
        
    Returns:
        True if condition is satisfied, False otherwise
    """
    # Convert to Decimal for numeric comparisons
    if isinstance(left_value, (int, float, str)):
        left_value = Decimal(str(left_value))
    if isinstance(right_value, (int, float, str)):
        right_value = Decimal(str(right_value))
    if right_value_2 is not None and isinstance(right_value_2, (int, float, str)):
        right_value_2 = Decimal(str(right_value_2))

    if operator == Operator.EQUAL:
        return left_value == right_value
    elif operator == Operator.NOT_EQUAL:
        return left_value != right_value
    elif operator == Operator.GREATER_THAN:
        return left_value > right_value
    elif operator == Operator.LESS_THAN:
        return left_value < right_value
    elif operator == Operator.GREATER_THAN_OR_EQUAL:
        return left_value >= right_value
    elif operator == Operator.LESS_THAN_OR_EQUAL:
        return left_value <= right_value
    elif operator == Operator.BETWEEN:
        if right_value_2 is None:
            raise ValueError("BETWEEN operator requires two values")
        return right_value <= left_value <= right_value_2
    elif operator == Operator.NOT_BETWEEN:
        if right_value_2 is None:
            raise ValueError("NOT_BETWEEN operator requires two values")
        return not (right_value <= left_value <= right_value_2)
    else:
        raise ValueError(f"Unsupported operator: {operator}")

