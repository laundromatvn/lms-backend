from sqlalchemy import func
from sqlalchemy.orm import Session, Query

from app.models.user import User
from app.models.tenant import Tenant
from app.schemas.tenant import UpdateTenantRequest


class UpdateTenantOperation:
    def __init__(
        self, db: Session, current_user: User, tenant_id: str, request: UpdateTenantRequest
    ):
        self.db = db
        self.current_user = current_user
        self.tenant_id = tenant_id
        self.request = request

    def execute(self) -> Tenant:
        tenant = self.db.query(Tenant).filter(Tenant.id == self.tenant_id).first()
        if not tenant:
            raise ValueError("Tenant not found")

        tenant.name = self.request.name
        tenant.contact_email = self.request.contact_email
        tenant.contact_phone_number = self.request.contact_phone_number
        tenant.contact_full_name = self.request.contact_full_name
        tenant.contact_address = self.request.contact_address
        tenant.status = self.request.status
        
        tenant.updated_by = self.current_user.id
        tenant.updated_at = func.now()

        self.db.add(tenant)
        self.db.commit()
        self.db.refresh(tenant)

        return tenant
