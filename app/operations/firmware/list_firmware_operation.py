from uuid import UUID

from sqlalchemy.orm import Session

from app.libs.database import with_db_session_for_class_instance
from app.libs.minio_client import MinioClient
from app.models.firmware import Firmware
from app.schemas.firmware import ListFirmwareQueryParams
from app.models.user import User


class ListFirmwareOperation:
    
    def __init__(self):
        self.minio_client = MinioClient()

    @with_db_session_for_class_instance
    def execute(
        self,
        db: Session,
        current_user: User,
        query_params: ListFirmwareQueryParams,
    ) -> tuple[int, list[Firmware]]:
        if not self._has_permission(current_user):
            raise PermissionError("You are not allowed to list firmware")

        query = (
            db.query(Firmware)
            .filter(Firmware.deleted_at.is_(None))
        )

        if query_params.status:
            query = query.filter(Firmware.status == query_params.status)

        if query_params.version_type:
            query = query.filter(Firmware.version_type == query_params.version_type)

        if query_params.search:
            query = query.filter(Firmware.name.ilike(f"%{query_params.search}%"))
            
        if query_params.order_by:
            if query_params.order_direction == "desc":
                query = query.order_by(getattr(Firmware, query_params.order_by).desc())
            else:
                query = query.order_by(getattr(Firmware, query_params.order_by).asc())
        else:
            query = query.order_by(Firmware.created_at.desc())

        total = query.count()
        result = query.offset((query_params.page - 1) * query_params.page_size).limit(query_params.page_size).all()

        return total, result

    def _has_permission(self, current_user: User) -> bool:
        return current_user.is_admin
