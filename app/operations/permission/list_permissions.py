from sqlalchemy.orm import Session

from app.models.permission import Permission
from app.schemas.permission import ListPermissionQueryParams


class ListPermissionsOperation:

    def execute(
        self,
        db: Session,
        query_params: ListPermissionQueryParams,
    ) -> tuple[int, list[Permission]]:
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

