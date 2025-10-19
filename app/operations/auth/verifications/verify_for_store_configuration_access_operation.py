from uuid import UUID

from sqlalchemy.orm import Session

from app.libs.database import with_db_session_classmethod
from app.models.tenant import Tenant
from app.models.system_task import SystemTask
from app.models.user import User
from app.enums.system_task_type_enum import SystemTaskTypeEnum


class VerifyForStoreConfigurationAccessOperation:

    @classmethod
    @with_db_session_classmethod
    async def execute(cls, db: Session, _: User, tenant_id: UUID) -> SystemTask:
        tenant = (
            db.query(Tenant)
            .filter(Tenant.id == tenant_id)
            .first()
        )
        if not tenant:
            raise ValueError("Tenant not found")

        system_task = SystemTask(
            task_type=SystemTaskTypeEnum.VERIFY_FOR_STORE_CONFIGURATION_ACCESS.value,
            data={
                "tenant_id": str(tenant_id),
            },
        )
        db.add(system_task)
        db.commit()
        db.refresh(system_task)

        return system_task


