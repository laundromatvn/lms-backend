from abc import ABC, abstractmethod
from typing import Optional
from decimal import Decimal
from uuid import UUID
from sqlalchemy.orm import Session

from app.enums.promotion.limit_type import LimitType
from app.schemas.promotion.base import Limit
from .context import LimitCheckContext


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
    def check(
        self,
        limit: Limit,
        context: LimitCheckContext,
    ) -> bool:
        """
        Check if a limit is not exceeded.
        
        Args:
            limit: The limit to check
            context: The context containing order data
            
        Returns:
            True if limit is not exceeded, False otherwise
        """
        pass

