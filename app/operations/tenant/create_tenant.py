from sqlalchemy.orm import Session

from app.models.user import User
from app.models.tenant import Tenant
from app.schemas.tenant import AddTenantRequest


class CreateTenantOperation:
    def __init__(
        self, db: Session, current_user: User, payload: AddTenantRequest
    ):
        self.db = db
        self.current_user = current_user
        self.payload = payload

    def execute(self) -> Tenant:
        tenant = Tenant(
            created_by=self.current_user.id,
            updated_by=self.current_user.id,
            name=self.payload.name,
            contact_email=self.payload.contact_email,
            contact_phone_number=self.payload.contact_phone_number,
            contact_full_name=self.payload.contact_full_name,
            contact_address=self.payload.contact_address,
        )
        self.db.add(tenant)
        self.db.commit()
        self.db.refresh(tenant)
        return tenant
