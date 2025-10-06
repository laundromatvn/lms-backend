import math
from typing import Any


def calculate_pulse_value(total_amount: Any, coin_value: int) -> int:
    return math.ceil(total_amount / coin_value)
