from minio.datatypes import Object
from sqlalchemy.orm import Session

from app.core.config import settings
from app.libs.database import with_db_session_for_class_instance
from app.libs.minio_client import MinioClient
from app.models.firmware import Firmware
from app.schemas.firmware import FirmwareCreateSchema
from app.models.user import User


class CreateFirmwareOperation:
    
    def __init__(self):
        self.minio_client = MinioClient()

    @with_db_session_for_class_instance
    def execute(
        self,
        db: Session,
        current_user: User,
        payload: FirmwareCreateSchema,
    ) -> Firmware:
        if not self._has_permission(current_user):
            raise PermissionError("You are not allowed to create firmware")
        
        metadata = self._get_firmware_metadata(payload.object_name)

        # check if version is unique
        if not self._is_version_unique(db, payload.version):
            raise ValueError(f"Version {payload.version} is already in use")

        firmware = Firmware(
            name=payload.name,
            version=payload.version,
            description=payload.description,
            status=payload.status,
            version_type=payload.version_type,
            object_name=metadata.object_name,
            file_size=metadata.size,
            checksum=metadata.etag,
            created_by=current_user.id,
            updated_by=current_user.id,
        )

        db.add(firmware)
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
        
    def _is_version_unique(self, db: Session, version: str) -> bool:
        return (
            db.query(Firmware)
            .filter(Firmware.version == version)
            .filter(Firmware.deleted_at.is_(None))
            .first()
            is None
        )
