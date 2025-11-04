"""
Check and apply promotion operation.

This module contains the business logic for checking and applying promotions.

Rules:
1. Scope
- If the promotion is a global promotion, it will be applied to all orders.
- If the promotion is a tenant promotion, it will be applied to all orders in the tenant.

2. Reward
- Prioritize the most valuable reward.

For example:
- Promotion 1: 10% discount
- Promotion 2: 100,000 VND discount
- Promotion 3: 10% discount and 100,000 VND discount

If the order amount is 1,000,000 VND, the promotion 2 will be applied.

3. Limit
- If the promotion has a limit, it will be applied to the limit.

4. Conditions
- If the promotion has conditions, it will be applied to the conditions.
"""
import datetime
from decimal import Decimal
from typing import Optional, List, Dict, Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.libs.database import with_db_session_classmethod
from app.models.promotion_campaign import PromotionCampaign, PromotionCampaignStatus
from app.models.order import Order
from app.models.store import Store
from app.schemas.promotion.base import Condition, Reward, Limit

from .condition_checkers.base import OrderPromotionContext
from .condition_checkers.registry import PromotionConditionCheckerRegistry
from .reward_calculators.registry import RewardCalculatorRegistry
from .limit_checkers.registry import LimitCheckerRegistry
from .limit_checkers.context import LimitCheckContext


class PromotionApplicationResult:
    """Result of applying a promotion to an order."""
    
    def __init__(
        self,
        promotion_campaign: PromotionCampaign,
        discount_amount: Decimal,
        applied: bool = True,
        reason: Optional[str] = None,
    ):
        self.promotion_campaign = promotion_campaign
        self.discount_amount = discount_amount
        self.applied = applied
        self.reason = reason


class CheckAndApplyPromotionOperation:
    """Operation to check and apply promotions to an order."""

    @classmethod
    @with_db_session_classmethod
    def execute(
        cls,
        db: Session,
        order: Order,
    ) -> Optional[PromotionApplicationResult]:
        """
        Check and apply the best promotion for an order.
        
        Args:
            db: Database session
            order: Order to check promotions for
            
        Returns:
            PromotionApplicationResult if a promotion is applied, None otherwise
        """
        store = db.query(Store).filter(Store.id == order.store_id).first()
        if not store:
            return None

        context = OrderPromotionContext(
            order_total_amount=order.total_amount,
            store_id=str(order.store_id),
            tenant_id=str(store.tenant_id) if store.tenant_id else None,
            user_id=str(order.created_by) if order.created_by else None,
        )

        eligible_promotions = cls._get_eligible_promotions(db, store.tenant_id)
        valid_promotions: List[Dict[str, Any]] = []
        
        for promotion in eligible_promotions:
            if not cls._check_scope(promotion, store.tenant_id):
                continue

            if not cls._check_conditions(db, promotion, context):
                continue

            limit_context = LimitCheckContext(context)
            if not cls._check_limits(db, promotion, limit_context):
                continue

            reward_value = cls._calculate_reward_value(promotion, order.total_amount)
            
            valid_promotions.append({
                'promotion': promotion,
                'reward_value': reward_value,
            })

        if not valid_promotions:
            return None

        best_promotion_data = max(valid_promotions, key=lambda x: x['reward_value'])
        best_promotion = best_promotion_data['promotion']
        discount_amount = best_promotion_data['reward_value']

        return PromotionApplicationResult(
            promotion_campaign=best_promotion,
            discount_amount=discount_amount,
            applied=True,
        )

    @classmethod
    def _get_eligible_promotions(
        cls,
        db: Session,
        tenant_id: Optional[UUID],
    ) -> List[PromotionCampaign]:
        """
        Get eligible promotions based on status and time.
        
        Returns promotions that are:
        - Not deleted
        - Active or Scheduled
        - Within time range (start_time <= now <= end_time)
        - Global (tenant_id is None) or for the specific tenant
        """
        now = datetime.datetime.now(datetime.timezone.utc)
        
        query = (
            db.query(PromotionCampaign)
            .filter(
                PromotionCampaign.deleted_at.is_(None),
                PromotionCampaign.status.in_([
                    PromotionCampaignStatus.ACTIVE,
                    PromotionCampaignStatus.SCHEDULED,
                ]),
                PromotionCampaign.start_time <= now,
            )
        )

        query = query.filter(
            (PromotionCampaign.end_time.is_(None)) |
            (PromotionCampaign.end_time >= now)
        )

        if tenant_id:
            query = query.filter(
                (PromotionCampaign.tenant_id.is_(None)) |
                (PromotionCampaign.tenant_id == tenant_id)
            )
        else:
            query = query.filter(PromotionCampaign.tenant_id.is_(None))

        return query.all()

    @classmethod
    def _check_scope(
        cls,
        promotion: PromotionCampaign,
        order_tenant_id: Optional[UUID],
    ) -> bool:
        """
        Check if promotion scope matches the order.
        
        - Global promotion (tenant_id is None): applies to all orders
        - Tenant promotion: only applies to orders from that tenant
        """
        if promotion.tenant_id is None:
            return True
        
        if order_tenant_id is None:
            return False
        
        return promotion.tenant_id == order_tenant_id

    @classmethod
    def _check_conditions(
        cls,
        db: Session,
        promotion: PromotionCampaign,
        context: OrderPromotionContext,
    ) -> bool:
        """
        Check if all promotion conditions are satisfied.
        
        All conditions must be satisfied (AND logic).
        """
        if not promotion.conditions:
            return True

        conditions = [Condition(**cond) for cond in promotion.conditions]

        for condition in conditions:
            checker_cls = PromotionConditionCheckerRegistry.get_checker(condition.type)
            
            if not checker_cls:
                return False

            checker = checker_cls(db=db)
            
            if not checker.check(condition, context):
                return False

        return True

    @classmethod
    def _check_limits(
        cls,
        db: Session,
        promotion: PromotionCampaign,
        context: LimitCheckContext,
    ) -> bool:
        """
        Check if promotion limits are not exceeded.
        
        All limits must be satisfied (AND logic).
        """
        if not promotion.limits:
            return True

        limits = [Limit(**limit) for limit in promotion.limits]

        for limit in limits:
            checker_cls = LimitCheckerRegistry.get_checker(limit.type)
            
            if not checker_cls:
                continue

            checker = checker_cls(db=db, promotion_id=promotion.id)
            
            if not checker.check(limit, context):
                return False

        return True

    @classmethod
    def _calculate_reward_value(
        cls,
        promotion: PromotionCampaign,
        order_amount: Decimal,
    ) -> Decimal:
        """
        Calculate the total reward value for a promotion.
        
        Sums up all rewards and returns the total discount amount.
        """
        if not promotion.rewards:
            return Decimal(0)

        rewards = [Reward(**reward) for reward in promotion.rewards]
        total_discount = Decimal(0)

        for reward in rewards:
            calculator_cls = RewardCalculatorRegistry.get_calculator(reward.type)
            
            if not calculator_cls:
                continue

            calculator = calculator_cls()
            
            try:
                discount = calculator.calculate(reward, order_amount)
                total_discount += discount
            except ValueError:
                continue

        return min(total_discount, order_amount)
