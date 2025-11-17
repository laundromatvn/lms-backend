from uuid import UUID

from sqlalchemy.orm import Session

from app.libs.database import with_db_session_for_class_instance
from app.models.controller import Controller
from app.models.user import User
from app.models.firmware import Firmware
from app.models.firmware_deployment import FirmwareDeployment
from app.models.store import Store
from app.models.tenant import Tenant
from app.schemas.firmware import ListProvisioningControllersQueryParams


class ListProvisioningControllersOperation:

    def __init__(self, current_user: User, firmware_id: UUID, query_params: ListProvisioningControllersQueryParams):
        self.current_user = current_user
        self.firmware_id = firmware_id
        self.query_params = query_params

        self._validate()
        self._preload()

    @with_db_session_for_class_instance
    def execute(self, db: Session):
        base_query = (
            db.query(
                *Controller.__table__.columns,
                FirmwareDeployment.id.label('deployment_id'),
                FirmwareDeployment.status.label('deployment_status'),
                Firmware.id.label('firmware_id'),
                Firmware.name.label('firmware_name'),
                Firmware.version.label('firmware_version'),
                Store.id.label('store_id'),
                Store.name.label('store_name'),
                Tenant.id.label('tenant_id'),
                Tenant.name.label('tenant_name'),
            )
            .outerjoin(FirmwareDeployment, Controller.id == FirmwareDeployment.controller_id)
            .outerjoin(Firmware, FirmwareDeployment.firmware_id == Firmware.id)
            .outerjoin(Store, Controller.store_id == Store.id)
            .outerjoin(Tenant, Store.tenant_id == Tenant.id)
            .filter(
                Controller.deleted_at.is_(None),
                FirmwareDeployment.id.isnot(None),
                FirmwareDeployment.firmware_id == self.firmware_id,
            )
        )

        if self.query_params.deployment_status:
            base_query = base_query.filter(FirmwareDeployment.status == self.query_params.deployment_status)
        
        if self.query_params.search:
            base_query = base_query.filter(Controller.name.ilike(f"%{self.query_params.search}%"))
        
        if self.query_params.order_by:
            if self.query_params.order_direction == "desc":
                base_query = base_query.order_by(getattr(Controller, self.query_params.order_by).desc())
            else:
                base_query = base_query.order_by(getattr(Controller, self.query_params.order_by).asc())
        else:
            base_query = base_query.order_by(Controller.created_at.desc())
            
        total = base_query.count()
        result = base_query.offset((self.query_params.page - 1) * self.query_params.page_size).limit(self.query_params.page_size).all()

        return total, result

    def _validate(self):
        if not self._has_permission(self.current_user):
            raise PermissionError("You are not allowed to list provisioning controllers")

    @with_db_session_for_class_instance
    def _preload(self, db: Session):
        self.firmware = self._get_firmware(db, self.firmware_id)

    def _has_permission(self, current_user: User) -> bool:
        return current_user.is_admin

    def _get_firmware(self, db: Session, firmware_id: UUID) -> Firmware:
        return db.get(Firmware, firmware_id)
