from datetime import datetime, timedelta

from celery.app.base import to_utc
from celery.utils.time import ZoneInfo
from sqlalchemy import func
from sqlalchemy.orm import Session
from sqlalchemy.sql import or_

from app.core.logging import logger
from app.core.config import settings
from app.core.celery_app import celery_app
from app.libs.database import with_db_session_for_class_instance
from app.models.machine import Machine, MachineStatus
from app.models.datapoint import Datapoint, DatapointValueType
from app.models.store import Store
from app.models.store_member import StoreMember
from app.models.tenant import Tenant
from app.models.tenant_member import TenantMember
from app.services.notification_service import NotificationService


class ResetNoRespondingMachinesOperation:

    NO_RESPONSE_THRESHOLD = 5  # minutes

    """
    This operation resets the status of machines that have not responded in the last 10 minutes to IDLE.
    """

    @with_db_session_for_class_instance
    def __init__(self, db: Session):
        self.db = db
        self.notification_service = NotificationService(db)

    def execute(self):
        no_responding_machines = self._get_no_responding_machines()
        if not no_responding_machines:
            logger.info("No no responding machines found")
            return

        logger.info(f"Found {len(no_responding_machines)} no responding machines")

        self._update_machines_status(no_responding_machines)
        self._send_task_to_reset_no_responding_machines(no_responding_machines)

    def _get_no_responding_machines(self):
        threshold_datetime = to_utc(
            datetime.now(tz=ZoneInfo(settings.TIMEZONE_NAME))
            - timedelta(minutes=self.NO_RESPONSE_THRESHOLD)
        )

        """
        Filter machines don't have datapoints or don't receive any datapoints in the last 5 minutes.
        """
        return (
            self.db.query(Machine)
            .outerjoin(Datapoint, Machine.id == Datapoint.machine_id)
            .filter(
                Machine.status.in_(
                    [
                        MachineStatus.STARTING,
                        MachineStatus.BUSY,
                    ]
                ),
                or_(
                    Datapoint.value_type == DatapointValueType.MACHINE_STATE,
                    Datapoint.id.is_(None),
                ),
            )
            .group_by(Machine.id)
            .having(
                or_(
                    func.max(Datapoint.created_at) < threshold_datetime,
                    func.max(Datapoint.created_at).is_(None),
                )
            )
            .all()
        )

    def _update_machines_status(self, machines: list[Machine]) -> None:
        self.db.query(Machine).filter(
            Machine.id.in_([machine.id for machine in machines])
        ).update({Machine.status: MachineStatus.IDLE})
        self.db.commit()

    def _send_task_to_reset_no_responding_machines(
        self, machines: list[Machine]
    ) -> None:
        machine_ids = [machine.id for machine in machines]
        celery_app.send_task(
            name="app.tasks.machine.send_no_responding_machine_notifications_task",
            args=[machine_ids],
        )
