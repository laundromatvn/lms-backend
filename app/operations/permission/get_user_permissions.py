from typing import List

from sqlalchemy.orm import Session

from app.models.permission import Permission
from app.models.user import User, UserRole

TENANT_STAFF_EXCLUDED_PERMISSIONS = [
    "permission.list",
    "permission.get",
    "permission.create",
    "permission.update",
    "permission.delete",
    "tenant.list",
    "tenant.get",
    "tenant.create",
    "tenant.update",
    "tenant.delete",
    "firmware.list",
    "firmware.get",
    "firmware.create",
    "firmware.update",
    "firmware.delete",
    "firmware_deployment.list",
    "firmware_deployment.get",
    "firmware_deployment.create",
    "firmware_deployment.update",
    "firmware_deployment.delete",
    "store.get_payment_methods",
    "store.update_payment_methods",
    "dashboard.overview.view",
    "machine.create",
    "machine.update",
    "machine.delete",
    "tenant_member.list",
    "tenant_member.get",
    "tenant_member.create",
    "tenant_member.update",
    "tenant_member.delete",
    "promotion_campaign.list",
    "promotion_campaign.get",
    "promotion_campaign.create",
    "promotion_campaign.update",
    "promotion_campaign.delete",
    "store.create",
    "store.update",
    "store.delete",
    "store.get_payment_methods",
    "store.update_payment_methods",
]

TENANT_ADMIN_EXCLUDED_PERMISSIONS = [
    "permission.list",
    "permission.get",
    "permission.create",
    "permission.update",
    "permission.delete",
    "tenant.list",
    "tenant.create",
    "tenant.delete",
    "firmware.list",
    "firmware.get",
    "firmware.create",
    "firmware.update",
    "firmware.delete",
    "firmware_deployment.create",
    "firmware_deployment.update",
    "firmware_deployment.delete",
]


class GetUserPermissionsOperation:
    def execute(self, db: Session, current_user: User) -> List[str]:
        # TODO: Update logic after plan and user permission implementation

        base_query = (
            db.query(Permission.code)
            .filter(Permission.is_enabled == True)
        )
        
        if current_user.role == UserRole.CUSTOMER:
            return []

        if current_user.role == UserRole.TENANT_STAFF:
            base_query = base_query.filter(Permission.code.not_in(TENANT_STAFF_EXCLUDED_PERMISSIONS))
        
        if current_user.role == UserRole.TENANT_ADMIN:
            base_query = base_query.filter(Permission.code.not_in(TENANT_ADMIN_EXCLUDED_PERMISSIONS))
        
        return [permission[0] for permission in base_query.all()]
