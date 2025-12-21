from sqlalchemy.orm import Session

from app.models.user import User
from app.models.tenant import Tenant


class GetTenantOperation:
    def __init__(
        self, db: Session, current_user: User, tenant_id: str
    ):
        self.db = db
        self.current_user = current_user
        self.tenant_id = tenant_id

    def execute(self) -> Tenant:
        tenant = self.db.query(Tenant).filter(Tenant.id == self.tenant_id).first()
        if not tenant:
            raise ValueError("Tenant not found")

        return tenant
