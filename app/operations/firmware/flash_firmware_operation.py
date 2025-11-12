from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy.orm.query import Query

from app.core.celery_app import celery_app
from app.libs.database import with_db_session_for_class_instance
from app.models.controller import Controller, ControllerStatus
from app.models.firmware import Firmware
from app.models.user import User
from app.schemas.firmware import ProvisionFirmwareSchema


class FlashFirmwareOperation:
    
    CHUNK_SIZE = 10 # number of controllers to flash at a time
    
    def __init__(self):
        pass

    @with_db_session_for_class_instance
    def execute(
        self,
        db: Session,
        current_user: User,
        firmware_id: UUID,
        payload: ProvisionFirmwareSchema,
    ):
        if not self._has_permission(current_user):
            raise PermissionError("You are not allowed to flash firmware")
        
        if not payload.controller_ids and not payload.all_controllers:
            raise ValueError("Controller IDs or all_controllers are required")
        
        firmware = self._get_firmware(db, firmware_id)
        if not firmware:
            raise ValueError("Firmware not found")

        total_controllers = self._count_controllers(db, payload.controller_ids)
        if total_controllers == 0:
            raise ValueError("No controllers found")
        
        for offset in range(0, total_controllers, self.CHUNK_SIZE):
            controllers = self._get_controllers(
                db=db,
                controller_ids=payload.controller_ids,
                all_controllers=payload.all_controllers,
                offset=offset,
                limit=self.CHUNK_SIZE,
            )
            
            celery_app.send_task(
                "app.tasks.firmware.flash_new_firmware_to_controllers_task",
                kwargs={
                    "current_user_id": current_user.id,
                    "controller_ids": [controller.id for controller in controllers],
                    "firmware_id": firmware.id,
                },
            )
            
    def _has_permission(self, current_user: User) -> bool:
        return current_user.is_admin
    
    def _get_firmware(self, db: Session, firmware_id: UUID) -> Firmware:
        return db.query(Firmware).filter(Firmware.id == firmware_id).first()

    def _get_controllers(
        self,
        db: Session,
        controller_ids: list[UUID] | None = None,
        all_controllers: bool = False,
        offset: int = 0,
        limit: int = CHUNK_SIZE,
    ) -> list[Controller]:
        base_query = self._get_controllers_base_query(db, controller_ids, all_controllers)
        results = base_query.offset(offset).limit(limit).all()
        return results
        
    def _count_controllers(
        self,
        db: Session,
        controller_ids: list[UUID] | None = None,
    ) -> int:
        base_query = self._get_controllers_base_query(db, controller_ids)
        return base_query.count()

    def _get_controllers_base_query(
        self,
        db: Session,
        controller_ids: list[UUID] | None = None,
        all_controllers: bool = False,
    ) -> Query:
        base_query = (
            db.query(Controller)
            .filter(
                Controller.deleted_at.is_(None),
                Controller.status.not_in([ControllerStatus.INACTIVE]),
            )
        )

        if controller_ids:
            base_query = base_query.filter(Controller.id.in_(controller_ids))

        return base_query
