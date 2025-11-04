from abc import ABC, abstractmethod
from typing import Any, Optional
from decimal import Decimal
from sqlalchemy.orm import Session

from app.enums.promotion.condition_type import ConditionType
from app.schemas.promotion.base import Condition


class OrderPromotionContext:
    """Context data structure for order promotion checking."""
    
    def __init__(
        self,
        order_total_amount: Decimal,
        store_id: str,
        tenant_id: str | None,
        user_id: str | None,
        # Additional context can be added here as needed
    ):
        self.order_total_amount = order_total_amount
        self.store_id = store_id
        self.tenant_id = tenant_id
        self.user_id = user_id


class BasePromotionConditionChecker(ABC):
    """Base class for promotion condition checkers."""
    
    condition_type: ConditionType

    def __init__(self, db: Optional[Session] = None):
        """
        Initialize the checker.
        
        Args:
            db: Optional database session for checkers that need DB access
        """
        self.db = db

    @abstractmethod
    def check(
        self,
        condition: Condition,
        context: OrderPromotionContext,
    ) -> bool:
        """
        Check if a condition is satisfied for the given order context.
        
        Args:
            condition: The condition to check
            context: The order context containing order data
            
        Returns:
            True if condition is satisfied, False otherwise
        """
        pass

