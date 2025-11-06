"""
Result class for limit checking operations.
"""
from decimal import Decimal
from typing import Optional
from dataclasses import dataclass


@dataclass
class LimitCheckResult:
    """
    Result of a limit check operation.
    
    Attributes:
        allowed: True if the promotion can be applied, False if it should be rejected
        max_discount_cap: Optional maximum discount amount if this is a capping limit.
                         If None, this is a rejecting limit (usage/budget limits).
                         If set, this is a capping limit (amount limits).
    """
    allowed: bool
    max_discount_cap: Optional[Decimal] = None
    
    @classmethod
    def reject(cls) -> "LimitCheckResult":
        """Create a result that rejects the promotion."""
        return cls(allowed=False, max_discount_cap=None)
    
    @classmethod
    def allow(cls) -> "LimitCheckResult":
        """Create a result that allows the promotion without any cap."""
        return cls(allowed=True, max_discount_cap=None)
    
    @classmethod
    def allow_with_cap(cls, max_discount: Decimal) -> "LimitCheckResult":
        """Create a result that allows the promotion with a maximum discount cap."""
        return cls(allowed=True, max_discount_cap=max_discount)

