from uuid import UUID

from minio.datatypes import Object
from sqlalchemy.orm import Session

from app.core.config import settings
from app.libs.database import with_db_session_for_class_instance
from app.libs.minio_client import MinioClient
from app.models.firmware import Firmware
from app.schemas.firmware import FirmwareUpdateSchema
from app.models.user import User


class UpdateFirmwareOperation:
    
    def __init__(self):
        self.minio_client = MinioClient()

    @with_db_session_for_class_instance
    def execute(
        self,
        db: Session,
        current_user: User,
        firmware_id: UUID,
        payload: FirmwareUpdateSchema,
    ) -> Firmware:
        if not self._has_permission(current_user):
            raise PermissionError("You are not allowed to update firmware")
        
        firmware = db.query(Firmware).filter(Firmware.id == firmware_id).first()
        if not firmware:
            raise ValueError("Firmware not found")
        
        for field, value in payload.model_dump(exclude_unset=True).items():
            if hasattr(firmware, field):
                setattr(firmware, field, value)

        firmware.updated_by = current_user.id

        db.commit()
        db.refresh(firmware)

        return firmware

    def _has_permission(self, current_user: User) -> bool:
        return current_user.is_admin
    
    def _get_firmware_metadata(self, object_name: str) -> Object:
        return self.minio_client.get_file_metadata(
            bucket_name=settings.BUCKET_NAME,
            object_name=object_name,
        )
