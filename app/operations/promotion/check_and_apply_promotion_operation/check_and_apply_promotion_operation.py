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

from app.libs.database import with_db_session_classmethod, get_db_session
from app.models import OrderStatus
from app.models.promotion_campaign import PromotionCampaign, PromotionCampaignStatus
from app.models.order import Order, PromotionOrder
from app.models.store import Store
from app.schemas.promotion.base import Condition, Reward, Limit

from .condition_checkers.base import OrderPromotionContext
from .condition_checkers.registry import PromotionConditionCheckerRegistry
from .reward_calculators.registry import RewardCalculatorRegistry
from .limit_checkers.registry import LimitCheckerRegistry
from .limit_checkers.context import LimitCheckContext


class CheckAndApplyPromotionOperation:
    """Operation to check and apply promotions to an order."""

    @classmethod
    def execute(
        cls,
        order: Order,
        db: Optional[Session] = None,
    ) -> Order:
        """
        Check and apply the best promotion for an order.
        
        Args:
            order: Order to check promotions for (will be modified in place)
            db: Optional database session. If provided, uses this session (no auto-commit).
                If None, creates a new session and auto-commits.
            
        Returns:
            Order with promotion applied (sub_total, discount_amount, promotion_summary, total_amount updated)
        """
        # If no session provided, create one with auto-commit (for backward compatibility)
        if db is None:
            with get_db_session() as session:
                return cls._execute_internal(session, order)
        else:
            # Use provided session (no auto-commit)
            return cls._execute_internal(db, order)
    
    @classmethod
    def _execute_internal(
        cls,
        db: Session,
        order: Order,
    ) -> Order:
        """
        Internal implementation of execute.
        
        Args:
            db: Database session
            order: Order to check promotions for (will be modified in place)
            
        Returns:
            Order with promotion applied (sub_total, discount_amount, promotion_summary, total_amount updated)
        """
        # Merge order into this session if it came from a different session
        order = db.merge(order)
        
        # Flush to ensure order is visible for subsequent queries
        db.flush()
        
        # Only check and apply promotions for NEW orders
        if order.status != OrderStatus.NEW:
            return order
        
        store = db.query(Store).filter(Store.id == order.store_id).first()
        if not store:
            return order

        sub_total = order.sub_total or order.total_amount
        context = OrderPromotionContext(
            order_total_amount=sub_total,
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

            # Calculate reward first
            calculated_reward = cls._calculate_reward_value(promotion, sub_total)
            
            # Then check and apply limits
            limit_context = LimitCheckContext(context)
            capped_reward = cls._check_and_apply_limits(
                db, promotion, limit_context, calculated_reward
            )
            
            # If limit check rejects the promotion (returns None), skip it
            if capped_reward is None:
                continue
            
            valid_promotions.append({
                'promotion': promotion,
                'reward_value': capped_reward,
            })
            
        if not valid_promotions:
            order.sub_total = sub_total
            order.discount_amount = Decimal("0.00")
            order.promotion_summary = {}
            order.total_amount = sub_total
            
            # Remove existing promotion order if no valid promotions found
            existing_promotion_order = (
                db.query(PromotionOrder)
                .filter(PromotionOrder.order_id == order.id)
                .first()
            )
            if existing_promotion_order:
                db.delete(existing_promotion_order)
            
            return order

        best_promotion_data = max(valid_promotions, key=lambda x: x['reward_value'])
        best_promotion = best_promotion_data['promotion']
        discount_amount = best_promotion_data['reward_value']
        final_amount = sub_total - discount_amount

        order.sub_total = sub_total
        order.discount_amount = discount_amount
        order.total_amount = max(final_amount, Decimal("0.00"))
        order.promotion_summary = {
            'conditions': best_promotion.conditions,
            'rewards': best_promotion.rewards,
            'limits': best_promotion.limits,
        }

        # Simplified query - no need to join Order since we already have order.id
        existing_promotion_order = (
            db.query(PromotionOrder)
            .filter(PromotionOrder.order_id == order.id)
            .first()
        )
        
        if existing_promotion_order:
            existing_promotion_order.promotion_id = best_promotion.id
        else:
            # Create new promotion order
            promotion_order = PromotionOrder(
                promotion_id=best_promotion.id,
                order_id=order.id,
            )
            db.add(promotion_order)


        return order

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
        
        If there is no condition, return True.
        If there is a condition, check if it is satisfied.
        If all conditions are satisfied, return True. If any condition is not satisfied, return False.
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
    def _check_and_apply_limits(
        cls,
        db: Session,
        promotion: PromotionCampaign,
        context: LimitCheckContext,
        calculated_reward: Decimal,
    ) -> Optional[Decimal]:
        """
        Check and apply promotion limits to the calculated reward.
        
        Two types of limits:
        1. Rejecting limits (usage/max budget): If exceeded, return None to reject promotion
        2. Capping limits (amount limits): If exceeded, return the maximum allowed discount
        
        Args:
            db: Database session
            promotion: The promotion campaign
            context: Limit check context
            calculated_reward: The calculated reward amount before limit checking
            
        Returns:
            The final discount amount after applying limits, or None if promotion should be rejected
        """
        if not promotion.limits:
            return calculated_reward

        limits = [Limit(**limit) for limit in promotion.limits]
        final_discount = calculated_reward
        max_discount_cap = None

        for limit in limits:
            checker_cls = LimitCheckerRegistry.get_checker(limit.type)
            
            if not checker_cls:
                continue

            checker = checker_cls(db=db, promotion_id=promotion.id)
            result = checker.check_and_apply(calculated_reward, limit, context)
            
            # If any limit rejects the promotion, return None
            if not result.allowed:
                return None
            
            # If this limit has a cap, track the minimum cap (most restrictive)
            if result.max_discount_cap is not None:
                if max_discount_cap is None:
                    max_discount_cap = result.max_discount_cap
                else:
                    max_discount_cap = min(max_discount_cap, result.max_discount_cap)
        
        # Apply the cap if there is one
        if max_discount_cap is not None:
            final_discount = min(final_discount, max_discount_cap)
        
        return final_discount

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
