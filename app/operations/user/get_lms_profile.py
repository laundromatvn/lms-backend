from sqlalchemy.orm import Session

from app.models.tenant import Tenant
from app.models.tenant_member import TenantMember
from app.models.user import User

class GetLMSProfileOperation:
    def __init__(
        self, db: Session, current_user: User
    ):
        self.db = db
        self.current_user = current_user

    def execute(self) -> tuple[User, Tenant]:
        tenant = (
            self.db.query(Tenant)
            .join(TenantMember, Tenant.id == TenantMember.tenant_id)
            .filter(TenantMember.user_id == self.current_user.id)
            .first()
        )

        if not tenant:
            raise ValueError("This user is not a member of any tenant")

        return self.current_user, tenant
