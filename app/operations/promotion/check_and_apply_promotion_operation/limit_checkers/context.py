"""
Context data structure for limit checking.
"""
from decimal import Decimal
from typing import Optional

from app.operations.promotion.check_and_apply_promotion_operation.condition_checkers.base import OrderPromotionContext


class LimitCheckContext:
    """Context data structure for limit checking."""
    
    def __init__(
        self,
        order_context: OrderPromotionContext,
    ):
        self.order_context = order_context
    
    @property
    def order_total_amount(self) -> Decimal:
        return self.order_context.order_total_amount
    
    @property
    def store_id(self) -> Optional[str]:
        return self.order_context.store_id
    
    @property
    def tenant_id(self) -> Optional[str]:
        return self.order_context.tenant_id
    
    @property
    def user_id(self) -> Optional[str]:
        return self.order_context.user_id

