from uuid import UUID

from sqlalchemy.orm import Session

from app.libs.database import with_db_session_for_class_instance
from app.models.controller import Controller
from app.models.notification import Notification, NotificationType, NotificationChannel
from app.models.user import User, UserRole
from app.models.machine import Machine
from app.models.tenant_member import TenantMember
from app.models.store import Store
from app.models.store_member import StoreMember
from app.services.notification_service import NotificationService


class SendNoRespondingMachineNotificationsOperation:
    """
    This operation sends notification to all users who have access to the machines.
    To notify them about the machine being no longer responding for a while.
    """
    
    CHUNK_SIZE = 100
    
    @with_db_session_for_class_instance
    def __init__(self, db: Session, machine_ids: list[UUID]):
        self.db = db
        self.notification_service = NotificationService(db)
        self.machine_ids = machine_ids

    def execute(self):
        # TODO: Refactor to process in chunks (idea: group by tenant/store)
        
        notifications = []
        
        for machine_id in self.machine_ids:
            notifications.extend(self._generate_notifications(machine_id))

        for i in range(0, len(notifications), self.CHUNK_SIZE):
            self.notification_service.add_bulk(notifications[i:i+self.CHUNK_SIZE])

    def _generate_notifications(self, machine_id: UUID):
        machine = self._get_machine_details(machine_id)
        if not machine: return []

        user_ids = []
        user_ids.extend(self._get_tenant_admin_user_ids(machine.tenant_id))
        user_ids.extend(self._get_store_member_user_ids(machine.store_id))

        title = "No responding machine"
        message = self._build_message(machine.store_name, machine.name)
        
        return [
            Notification(
                user_id=user_id,
                title=title,
                message=message,
                type=NotificationType.ERROR,
                channel=NotificationChannel.IN_APP,
            )
            for user_id in user_ids
            if user_id is not None
        ]

    def _get_machine_details(self, machine_id: UUID):
        return (
            self.db.query(
                *Machine.__table__.columns,
                Store.tenant_id.label("tenant_id"),
                Store.id.label("store_id"),
                Store.name.label("store_name"),
            )
            .join(Controller, Machine.controller_id == Controller.id)
            .join(Store, Controller.store_id == Store.id)
            .filter(Machine.id == machine_id)
            .first()
        )

    def _get_tenant_admin_user_ids(self, tenant_id: UUID):
        tenant_admins = (
            self.db.query(TenantMember.user_id)
            .join(User, TenantMember.user_id == User.id)
            .filter(TenantMember.tenant_id == tenant_id)
            .filter(User.role == UserRole.TENANT_ADMIN)
            .distinct()
        )
        
        return [tenant_admin.user_id for tenant_admin in tenant_admins]
        
    def _get_store_member_user_ids(self, store_id: UUID):
        store_members = (
            self.db.query(StoreMember.user_id)
            .filter(StoreMember.store_id == store_id)
            .distinct()
        )
        
        return [store_member.user_id for store_member in store_members]

    def _build_message(self, store_name: str, machine_name: str) -> str:
        return f"Machine {machine_name} in {store_name} is no longer responding. Please check the machine status."
