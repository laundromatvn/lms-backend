from abc import ABC, abstractmethod
from typing import Optional
from decimal import Decimal
from uuid import UUID
from sqlalchemy.orm import Session

from app.enums.promotion.limit_type import LimitType
from app.models.order import Order
from app.schemas.promotion.base import Limit

from .context import LimitCheckContext
from .result import LimitCheckResult


class BaseLimitChecker(ABC):
    """Base class for limit checkers."""
    
    limit_type: LimitType

    def __init__(self, db: Optional[Session] = None, promotion_id: Optional[UUID] = None):
        """
        Initialize the checker.
        
        Args:
            db: Optional database session for checkers that need DB access
            promotion_id: Optional promotion ID for usage tracking
        """
        self.db = db
        self.promotion_id = promotion_id

    @abstractmethod
    def check_and_apply(
        self,
        calculated_reward: Decimal,
        limit: Limit,
        context: LimitCheckContext,
    ) -> LimitCheckResult:
        """
        Check if a limit is not exceeded and apply it to the calculated reward.
        
        Args:
            calculated_reward: The calculated reward amount before limit checking
            limit: The limit to check
            context: The context containing order data
            
        Returns:
            LimitCheckResult indicating if promotion is allowed and any discount cap
        """
        pass

