from sqlalchemy.orm import Session

from app.models.permission import Permission
from app.models.user import User
from app.schemas.permission import ListPermissionQueryParams


class ListPermissionsOperation:

    def execute(
        self,
        db: Session,
        current_user: User,
        query_params: ListPermissionQueryParams,
    ) -> tuple[int, list[Permission]]:
        if not self._has_permission(current_user):
            raise PermissionError("You are not allowed to list permissions")
        
        base_query = db.query(Permission)

        if query_params.is_enabled:
            base_query = base_query.filter(Permission.is_enabled == query_params.is_enabled)

        if query_params.search:
            base_query = base_query.filter(Permission.name.ilike(f"%{query_params.search}%"))

        if query_params.order_by:
            if query_params.order_direction == "desc":
                base_query = base_query.order_by(getattr(Permission, query_params.order_by).desc())
            else:
                base_query = base_query.order_by(getattr(Permission, query_params.order_by).asc())
        else:
            base_query = base_query.order_by(Permission.id.desc())

        total = base_query.count()
        permissions = base_query.offset((query_params.page - 1) * query_params.page_size).limit(query_params.page_size).all()
        return total, permissions
    
    def _has_permission(self, current_user: User) -> bool:
        return current_user.is_admin
