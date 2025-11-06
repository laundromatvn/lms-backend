"""
Check and apply promotion operation package.

This package automatically registers all condition checkers, reward calculators,
and limit checkers when imported.
"""
from .condition_checkers import *  # noqa: F401, F403 - Trigger checker registration
from .reward_calculators import *  # noqa: F401, F403 - Trigger calculator registration
from .limit_checkers import *  # noqa: F401, F403 - Trigger checker registration

from .check_and_apply_promotion_operation import (
    CheckAndApplyPromotionOperation,
)

__all__ = [
    "CheckAndApplyPromotionOperation",
]

