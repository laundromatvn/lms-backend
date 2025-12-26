from uuid import UUID

from sqlalchemy.orm import Session, Query

from app.models import Permission
from app.models.user import User
from app.models.subscription_plan import SubscriptionPlan
from app.models.permission_group_permission import PermissionGroupPermission
from app.schemas.subscription import ListSubscriptionPlansPermissionsQueryParams


class ListSubscriptionPlansPermissionsOperation:
    def __init__(
        self,
        db: Session,
        current_user: User,
        subscription_plan_id: UUID,
        query_params: ListSubscriptionPlansPermissionsQueryParams,
    ):
        self.db = db
        self.current_user = current_user
        self.subscription_plan_id = subscription_plan_id
        self.query_params = query_params

    def execute(self):
        self._get_subscription_plan()
        return self._list_permissions()

    def _get_subscription_plan(self) -> SubscriptionPlan:
        self.subscription_plan = (
            self.db.query(SubscriptionPlan)
            .filter(
                SubscriptionPlan.id == self.subscription_plan_id,
                SubscriptionPlan.deleted_at.is_(None),
            )
            .first()
        )
        if not self.subscription_plan:
            raise ValueError(
                f"Subscription plan with ID {self.subscription_plan_id} not found"
            )

    def _list_permissions(self) -> tuple[int, list[Permission]]:
        base_query = (
            self.db.query(Permission)
            .join(
                PermissionGroupPermission,
                Permission.id == PermissionGroupPermission.permission_id,
            )
            .filter(
                PermissionGroupPermission.permission_group_id
                == self.subscription_plan.permission_group_id,
            )
        )

        base_query = self._apply_filters(base_query)
        base_query = self._apply_ordering(base_query)

        total = base_query.count()
        permissions = self._apply_pagination(base_query).all()

        return total, permissions

    def _apply_filters(self, base_query: Query) -> Query:
        if self.query_params.search:
            base_query = base_query.filter(
                Permission.name.ilike(f"%{self.query_params.search}%")
            )

        return base_query

    def _apply_ordering(self, base_query: Query) -> Query:
        if self.query_params.order_by:
            if self.query_params.order_direction == "desc":
                base_query = base_query.order_by(
                    getattr(Permission, self.query_params.order_by).desc()
                )
            else:
                base_query = base_query.order_by(
                    getattr(Permission, self.query_params.order_by).asc()
                )
        else:
            base_query = base_query.order_by(Permission.code.asc())

        return base_query

    def _apply_pagination(self, base_query: Query) -> Query:
        return base_query.offset(
            (self.query_params.page - 1) * self.query_params.page_size
        ).limit(self.query_params.page_size)
