from decimal import Decimal

from app.enums.promotion.reward_type import RewardType
from app.enums.promotion.unit import Unit

from .base import BaseRewardCalculator
from .registry import RewardCalculatorRegistry


REWARD_TYPE = RewardType.PERCENTAGE_AMOUNT


@RewardCalculatorRegistry.register(REWARD_TYPE)
class PercentageAmountRewardCalculator(BaseRewardCalculator):
    reward_type = REWARD_TYPE

    def calculate(
        self,
        reward,
        order_amount: Decimal,
    ) -> Decimal:
        """
        Calculate percentage amount reward.
        
        For PERCENTAGE_AMOUNT reward:
        - value: Percentage value (e.g., 10 for 10%)
        - unit: Must be PERCENTAGE
        """
        if reward.unit != Unit.PERCENTAGE:
            raise ValueError(
                f"Invalid unit {reward.unit} for PERCENTAGE_AMOUNT reward. "
                f"Only PERCENTAGE is supported."
            )

        percentage = Decimal(str(reward.value))
        discount = order_amount * percentage / Decimal(100)
        return min(discount, order_amount)

