from uuid import UUID

from sqlalchemy.orm import Session

from app.libs.database import with_db_session_for_class_instance
from app.models.firmware import Firmware
from app.models.controller import Controller
from app.models.store import Store
from app.models.tenant import Tenant
from app.schemas.firmware import ListProvisionedControllersQueryParams
from app.models.user import User


class ListProvisionedControllersOperation:
    
    @with_db_session_for_class_instance
    def execute(
        self,
        db: Session,
        current_user: User,
        firmware_id: UUID,
        query_params: ListProvisionedControllersQueryParams,
    ) -> tuple[int, list[Firmware]]:
        if not self._has_permission(current_user):
            raise PermissionError("You are not allowed to list firmware")

        query = (
            db.query(
                *Controller.__table__.columns,
                Store.id.label('store_id'),
                Store.name.label('store_name'),
                Tenant.id.label('tenant_id'),
                Tenant.name.label('tenant_name'),
                Firmware.id.label('firmware_id'),
                Firmware.name.label('firmware_name'),
                Firmware.version.label('firmware_version'),
            )
            .outerjoin(Store, Controller.store_id == Store.id)
            .outerjoin(Tenant, Store.tenant_id == Tenant.id)
            .outerjoin(Firmware, Controller.provisioned_firmware_id == Firmware.id)
            .filter(
                Controller.deleted_at.is_(None),
                Controller.provisioned_firmware_id == firmware_id,
            )
        )

        if query_params.tenant_id:
            query = query.filter(Tenant.id == query_params.tenant_id)

        if query_params.store_id:
            query = query.filter(Store.id == query_params.store_id)

        if query_params.search:
            query = query.filter(Controller.name.ilike(f"%{query_params.search}%"))
            
        if query_params.order_by:
            if query_params.order_direction == "desc":
                query = query.order_by(getattr(Controller, query_params.order_by).desc())
            else:
                query = query.order_by(getattr(Controller, query_params.order_by).asc())
        else:
            query = query.order_by(Controller.created_at.desc())
            
        total = query.count()
        result = query.offset((query_params.page - 1) * query_params.page_size).limit(query_params.page_size).all()

        return total, result

    def _has_permission(self, current_user: User) -> bool:
        return current_user.is_admin


