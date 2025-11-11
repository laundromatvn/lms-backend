from uuid import UUID
from sqlalchemy.orm import Session
from app.libs.database import with_db_session_for_class_instance
from app.models.firmware import Firmware
from app.models.user import User
from app.schemas.firmware import ProvisionFirmwareSchema


class FlashFirmwareOperation:
    
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
        
        firmware = self._get_firmware(db, firmware_id)
        if not firmware:
            raise ValueError("Firmware not found")

    def _has_permission(self, current_user: User) -> bool:
        return current_user.is_admin
    
    def _get_firmware(self, db: Session, firmware_id: UUID) -> Firmware:
        return db.query(Firmware).filter(Firmware.id == firmware_id).first()


