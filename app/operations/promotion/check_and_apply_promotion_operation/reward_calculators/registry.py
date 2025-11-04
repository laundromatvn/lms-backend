from app.enums.promotion.reward_type import RewardType


class RewardCalculatorRegistry:
    """Registry for reward calculators."""
    
    _calculators = {}

    @classmethod
    def register(cls, reward_type: RewardType):
        """Register a reward calculator for a specific reward type."""
        def decorator(calculator_cls):
            cls._calculators[reward_type] = calculator_cls
            return calculator_cls
        return decorator

    @classmethod
    def get_calculator(cls, reward_type: RewardType):
        """Get the calculator for a specific reward type."""
        return cls._calculators.get(reward_type)

