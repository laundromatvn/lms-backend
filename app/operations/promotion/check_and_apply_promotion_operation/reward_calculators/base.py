from abc import ABC, abstractmethod
from decimal import Decimal

from app.enums.promotion.reward_type import RewardType
from app.schemas.promotion.base import Reward


class BaseRewardCalculator(ABC):
    """Base class for reward calculators."""
    
    reward_type: RewardType

    @abstractmethod
    def calculate(
        self,
        reward: Reward,
        order_amount: Decimal,
    ) -> Decimal:
        """
        Calculate the reward value for a given reward and order amount.
        
        Args:
            reward: The reward to calculate
            order_amount: The order total amount
            
        Returns:
            The calculated discount amount
        """
        pass

