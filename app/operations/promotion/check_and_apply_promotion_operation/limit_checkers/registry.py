from app.enums.promotion.limit_type import LimitType


class LimitCheckerRegistry:
    """Registry for limit checkers."""
    
    _checkers = {}

    @classmethod
    def register(cls, limit_type: LimitType):
        """Register a limit checker for a specific limit type."""
        def decorator(checker_cls):
            cls._checkers[limit_type] = checker_cls
            return checker_cls
        return decorator

    @classmethod
    def get_checker(cls, limit_type: LimitType):
        """Get the checker for a specific limit type."""
        return cls._checkers.get(limit_type)

