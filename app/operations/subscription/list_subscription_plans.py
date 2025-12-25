from sqlalchemy.orm import Session, Query

from app.models.subscription_plan import SubscriptionPlan
from app.models.user import User
from app.schemas.subscription import ListSubscriptionPlansQueryParams


class ListSubscriptionPlansOperation:
    def __init__(self, db: Session, current_user: User, query_params: ListSubscriptionPlansQueryParams):
        self.db = db
        self.current_user = current_user
        self.query_params = query_params

    def execute(self):
        base_query = self._build_base_query()

        base_query = self._apply_filters(base_query)
        base_query = self._apply_ordering(base_query)

        total = base_query.count()
        subscription_plans = self._apply_pagination(base_query).all()

        return total, subscription_plans
    
    def _build_base_query(self) -> Query:
        base_query = (
            self.db.query(SubscriptionPlan)
            .filter(SubscriptionPlan.deleted_at.is_(None))
        )

        return base_query
    
    def _apply_filters(self, base_query: Query) -> Query:
        if self.query_params.is_enabled:
            base_query = base_query.filter(SubscriptionPlan.is_enabled == self.query_params.is_enabled)

        if self.query_params.is_default:
            base_query = base_query.filter(SubscriptionPlan.is_default == self.query_params.is_default)
            
        if self.query_params.search:
            base_query = base_query.filter(SubscriptionPlan.name.ilike(f"%{self.query_params.search}%"))

        return base_query
    
    def _apply_ordering(self, base_query: Query) -> Query:
        if self.query_params.order_by:
            if self.query_params.order_direction == "desc":
                base_query = base_query.order_by(getattr(SubscriptionPlan, self.query_params.order_by).desc())
            else:
                base_query = base_query.order_by(getattr(SubscriptionPlan, self.query_params.order_by).asc())
        else:
            base_query = base_query.order_by(SubscriptionPlan.created_at.desc())

        return base_query
    
    def _apply_pagination(self, base_query: Query) -> Query:
        return base_query.offset(
            (self.query_params.page - 1) * self.query_params.page_size
        ).limit(self.query_params.page_size)
