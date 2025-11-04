from app.enums.promotion.condition_type import ConditionType


class PromotionConditionCheckerRegistry:
    """Registry for promotion condition checkers."""
    
    _checkers = {}

    @classmethod
    def register(cls, condition_type: ConditionType):
        """Register a condition checker for a specific condition type."""
        def decorator(checker_cls):
            cls._checkers[condition_type] = checker_cls
            return checker_cls
        return decorator

    @classmethod
    def get_checker(cls, condition_type: ConditionType):
        """Get the checker for a specific condition type."""
        return cls._checkers.get(condition_type)

