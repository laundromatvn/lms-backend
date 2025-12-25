from sqlalchemy.orm import Session, Query

from app.models.tenant_member import TenantMember
from app.models.user import User, UserRole, UserStatus
from app.schemas.user import ListAvailableUserTenantAdminsRequest


class ListAvailableUserTenantAdminsOperation:

    def __init__(
        self,
        db: Session,
        current_user: User,
        request: ListAvailableUserTenantAdminsRequest,
    ):
        self.db = db
        self.current_user = current_user
        self.request = request

    def execute(self) -> tuple[int, list[User]]:
        base_query = self._build_base_query()
        
        base_query = self._apply_ordering(base_query)

        total = base_query.count()
        users = self._apply_pagination(base_query).all()

        return total, users

    def _build_base_query(self) -> Query:
        tenant_member_user_ids_subquery = (
            self.db.query(TenantMember.user_id)
            .distinct()
            .subquery()
        )

        return (
            self.db.query(User)
            .filter(
                User.role == UserRole.TENANT_ADMIN,
                User.status == UserStatus.ACTIVE,
                User.deleted_at.is_(None),
                User.id.notin_(tenant_member_user_ids_subquery),
            )
        )

    def _apply_ordering(self, base_query: Query) -> Query:
        base_query = base_query.order_by(User.email.asc())

        return base_query

    def _apply_pagination(self, base_query: Query) -> Query:
        return base_query.offset(
            (self.request.page - 1) * self.request.page_size
        ).limit(self.request.page_size)

