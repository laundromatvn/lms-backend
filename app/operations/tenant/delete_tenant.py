from sqlalchemy.orm import Session, Query

from app.models.user import User
from app.models.tenant import Tenant
from app.schemas.tenant import ListTenantQueryParams


class DeleteTenantOperation:
    def __init__(
        self, db: Session, current_user: User, tenant_id: str
    ):
        self.db = db
        self.current_user = current_user
        self.tenant_id = tenant_id

    def execute(self) -> None:
        tenant = self.db.query(Tenant).filter(Tenant.id == self.tenant_id).first()
        if not tenant:
            raise ValueError("Tenant not found")

        tenant.soft_delete(self.current_user.id)
        self.db.add(tenant)
        self.db.commit()
