from sqlalchemy.orm import Session
from uuid import UUID
from typing import List

from app.libs.database import with_db_session_classmethod
from app.models.machine import Machine, MachineType
from app.models.controller import Controller


class StoreMachineOperation:

    @classmethod
    @with_db_session_classmethod
    def classify_machines(
        cls, db: Session, store_id: UUID
    ) -> tuple[int, List[Machine]]:
        machines = (
            db.query(Machine)
            .join(Controller, Machine.controller_id == Controller.id)
            .filter(Controller.store_id == store_id)
            .order_by(Machine.relay_no.asc())
            .all()
        )

        washers = []
        dryers = []

        for machine in machines:
            if machine.machine_type == MachineType.WASHER:
                washers.append(machine)
            else:
                dryers.append(machine)

        return washers, dryers
