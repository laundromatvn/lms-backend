from uuid import UUID
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.libs.database import with_db_session_classmethod
from app.models.controller import Controller
from app.models.machine import Machine
from app.models.store import Store
from app.models.datapoint import Datapoint, DatapointValueType


class GetOverviewMachineStatusLineChartOperation:
    
    @classmethod
    @with_db_session_classmethod
    def execute(cls, db: Session, store_id: UUID, machine_id: UUID, start_date: datetime = None, end_date: datetime = None):
        if not store_id and not machine_id:
            raise ValueError("Either store_id or machine_id must be provided")
        
        if not start_date:
            start_date = datetime.now() - timedelta(hours=24)

        if not end_date:
            end_date = datetime.now()
        
        base_query = (
            db.query(Machine)
            .join(Controller, Machine.controller_id == Controller.id)
            .join(Store, Controller.store_id == Store.id)
            .filter(
                Machine.deleted_at.is_(None),
                Controller.deleted_at.is_(None),
                Store.deleted_at.is_(None)
            )
            .order_by(Machine.name)
        )
        
        if store_id:
            base_query = base_query.filter(Store.id == store_id)

        if machine_id:
            base_query = base_query.filter(Machine.id == machine_id)
        
        machines = base_query.all()
        
        if not machines:
            return {
                "labels": [],
                "datasets": []
            }
        
        datapoints = (
            db.query(Datapoint)
            .join(Machine, Datapoint.machine_id == Machine.id)
            .filter(
                Machine.id.in_([m.id for m in machines]),
                Datapoint.created_at >= start_date,
                Datapoint.created_at <= end_date,
                Datapoint.value_type == DatapointValueType.MACHINE_STATE
            )
            .order_by(Datapoint.created_at)
            .all()
        )
        
        data = []
        for dp in datapoints:
            label = f"{dp.machine.controller.device_id} - {dp.machine.relay_no}"
            data.append({
                "date": dp.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                "label": label,
                "value": dp.value,
            })
        
        return data
