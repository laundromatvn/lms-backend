from datetime import datetime, timedelta

from celery.app.base import to_utc
from celery.utils.time import ZoneInfo
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.logging import logger
from app.core.config import settings
from app.libs.database import with_db_session_for_class_instance
from app.models.machine import Machine, MachineStatus
from app.models.datapoint import Datapoint, DatapointValueType


class ResetNoRespondingMachinesOperation:

    NO_RESPONSE_THRESHOLD = 5  # minutes

    """
    This operation resets the status of machines that have not responded in the last 10 minutes to IDLE.
    """

    @with_db_session_for_class_instance
    def __init__(self, db: Session):
        self.db = db

    def execute(self):
        no_responding_machines = self._get_no_responding_machines()
        logger.info(f"Found {len(no_responding_machines)} no responding machines")

        # update a bulk
        (
            self.db.query(Machine)
            .filter(Machine.id.in_([machine.id for machine in no_responding_machines]))
            .update({Machine.status: MachineStatus.IDLE})
        )
        self.db.commit()

    def _get_no_responding_machines(self):
        threshold_datetime = to_utc(
            datetime.now(tz=ZoneInfo(settings.TIMEZONE_NAME)) - timedelta(minutes=self.NO_RESPONSE_THRESHOLD)
        )

        return (
            self.db.query(Machine)
            .join(Datapoint, Machine.id == Datapoint.machine_id)
            .filter(
                Machine.status.in_(
                    [
                        MachineStatus.STARTING,
                        MachineStatus.BUSY,
                    ]
                ),
                Datapoint.value_type == DatapointValueType.MACHINE_STATE,
            )
            .group_by(Machine.id)
            .having(func.max(Datapoint.created_at) < threshold_datetime)
            .all()
        )
