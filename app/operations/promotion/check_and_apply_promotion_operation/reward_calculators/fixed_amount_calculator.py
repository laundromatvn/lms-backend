from decimal import Decimal

from app.enums.promotion.reward_type import RewardType
from app.enums.promotion.unit import Unit

from .base import BaseRewardCalculator
from .registry import RewardCalculatorRegistry


REWARD_TYPE = RewardType.FIXED_AMOUNT


@RewardCalculatorRegistry.register(REWARD_TYPE)
class FixedAmountRewardCalculator(BaseRewardCalculator):
    reward_type = REWARD_TYPE

    def calculate(
        self,
        reward,
        order_amount: Decimal,
    ) -> Decimal:
        """
        Calculate fixed amount reward.
        
        For FIXED_AMOUNT reward:
        - value: Fixed discount amount
        - unit: Must be VND
        """
        if reward.unit != Unit.VND:
            raise ValueError(
                f"Invalid unit {reward.unit} for FIXED_AMOUNT reward. "
                f"Only VND is supported."
            )

        discount = Decimal(str(reward.value))
        return min(discount, order_amount)

