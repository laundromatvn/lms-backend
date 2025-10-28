from datetime import datetime
from decimal import Decimal
from typing import List
from uuid import UUID, uuid4

from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.core.logging import logger
from app.enums.mqtt import MQTTEventTypeEnum
from app.libs.database import with_db_session_classmethod
from app.libs.mqtt import mqtt_client
from app.models.machine import Machine, MachineType, MachineStatus
from app.models.controller import Controller
from app.models.store import Store
from app.models.tenant_member import TenantMember
from app.models.user import User
from app.schemas.machine import (
    AddMachineRequest,
    UpdateMachineRequest,
    ListMachineQueryParams,
)
from app.utils.coin import calculate_pulse_value


class MachineOperation:

    MACHINE_ACTION_TOPIC = "lms/stores/{store_id}/controllers/{controller_id}/actions"

    @classmethod
    @with_db_session_classmethod
    def get(cls, db: Session, current_user: User, machine_id: UUID) -> Machine:
        base_query = (
            db.query(
                *Machine.__table__.columns,
                Controller.device_id.label("controller_device_id"),
                Controller.store_id.label("store_id"),
                Store.name.label("store_name"),
            )
            .join(Controller, Machine.controller_id == Controller.id)
            .outerjoin(Store, Controller.store_id == Store.id)
            .filter(Machine.id == machine_id)
        )
        
        if not current_user.is_admin:
            authorized_store_ids = cls._get_authorized_store_ids(db, current_user)
            base_query = base_query.filter(Controller.store_id.in_(authorized_store_ids))

        machine = base_query.first()
        if not machine:
            raise ValueError("Machine not found")

        return machine

    @classmethod
    @with_db_session_classmethod
    def list(
        cls,
        db: Session,
        current_user: User,
        query_params: ListMachineQueryParams,
    ) -> tuple[int, List[Machine]]:
        base_query = (
            db.query(
                *Machine.__table__.columns,
                Controller.device_id.label("controller_device_id"),
                Controller.store_id.label("store_id"),
                Store.name.label("store_name"),
            )
            .join(Controller, Machine.controller_id == Controller.id)
            .outerjoin(Store, Controller.store_id == Store.id)
        )
        
        if not current_user.is_admin:
            authorized_store_ids = cls._get_authorized_store_ids(db, current_user)
            base_query = base_query.filter(Controller.store_id.in_(authorized_store_ids))
        
        if query_params.store_id:
            base_query = base_query.filter(
                Controller.store_id == query_params.store_id
            )

        if query_params.controller_id:
            base_query = base_query.filter(
                Machine.controller_id == query_params.controller_id
            )

        if query_params.machine_type:
            base_query = base_query.filter(
                Machine.machine_type == query_params.machine_type
            )

        if query_params.relay_no:
            base_query = base_query.filter(Machine.relay_no == query_params.relay_no)

        if query_params.machine_type:
            base_query = base_query.filter(Machine.machine_type == query_params.machine_type)

        if query_params.status:
            base_query = base_query.filter(Machine.status == query_params.status)

        if query_params.search:
            search = f"%{query_params.search}%"
            base_query = base_query.filter(Machine.name.like(search))
        
        if query_params.order_by:
            if query_params.order_direction == "desc":
                base_query = base_query.order_by(
                    getattr(Machine, query_params.order_by).desc(),
                )
            else:
                base_query = base_query.order_by(
                    getattr(Machine, query_params.order_by).asc(),
                )
        else:
            base_query = base_query.order_by(
                Machine.relay_no.asc(),
            )

        total = base_query.count()
        results = (
            base_query
            .offset((query_params.page - 1) * query_params.page_size)
            .limit(query_params.page_size)
            .all()
        )

        return total, results

    @classmethod
    @with_db_session_classmethod
    def create(
        cls,
        db: Session,
        created_by: User,
        request: AddMachineRequest,
    ) -> Machine:
        # Check if controller exists
        controller = db.query(Controller).filter_by(id=request.controller_id).first()
        if not controller:
            raise ValueError("Controller not found")

        # Check if relay number is already taken for this controller
        existing_machine = (
            db.query(Machine)
            .filter(
                Machine.controller_id == request.controller_id,
                Machine.relay_no == request.relay_no,
            )
            .first()
        )
        if existing_machine:
            raise ValueError(
                f"Relay {request.relay_no} is already in use for this controller"
            )

        # Check if machine name is already taken (only if name is provided)
        if request.name:
            existing_name = (
                db.query(Machine).filter(Machine.name == request.name).first()
            )
            if existing_name:
                raise ValueError(f"Machine name '{request.name}' is already in use")

        # Check if relay number is within controller's total_relays limit
        if request.relay_no > controller.total_relays:
            raise ValueError(
                f"Relay number {request.relay_no} exceeds controller's total relays ({controller.total_relays})"
            )

        machine = Machine(
            controller_id=request.controller_id,
            relay_no=request.relay_no,
            name=request.name,
            machine_type=request.machine_type,
            details=request.details,
            base_price=request.base_price,
            pulse_duration=request.pulse_duration,
            coin_value=request.coin_value,
            add_ons_options=request.add_ons_options,
        )
        db.add(machine)
        db.commit()
        db.refresh(machine)

        return machine

    @classmethod
    @with_db_session_classmethod
    def update_partially(
        cls,
        db: Session,
        updated_by: User,
        machine_id: UUID,
        request: UpdateMachineRequest,
    ) -> Machine:
        machine = db.query(Machine).filter_by(id=machine_id).first()
        if not machine:
            raise ValueError("Machine not found")

        update_data = request.model_dump(exclude_unset=True)

        # Check if name is being updated and if it's unique (only if name is provided)
        if "name" in update_data and update_data["name"] is not None:
            existing_name = (
                db.query(Machine)
                .filter(Machine.name == update_data["name"], Machine.id != machine_id)
                .first()
            )
            if existing_name:
                raise ValueError(
                    f"Machine name '{update_data['name']}' is already in use"
                )

        for field, value in update_data.items():
            if hasattr(machine, field):
                setattr(machine, field, value)

        db.commit()
        db.refresh(machine)

        return machine

    @classmethod
    @with_db_session_classmethod
    def delete(
        cls,
        db: Session,
        deleted_by: User,
        machine_id: UUID,
    ) -> bool:
        machine = db.query(Machine).filter_by(id=machine_id).first()
        if not machine:
            raise ValueError("Machine not found")

        machine.soft_delete()
        db.commit()

        return True

    @classmethod
    @with_db_session_classmethod
    def create_machines_for_controller(
        cls,
        db: Session,
        controller: Controller,
    ) -> List[Machine]:
        """Create machines for all relays when a controller is created"""
        machines = []

        # Get existing machine relay numbers
        existing_machines = (
            db.query(Machine).filter_by(controller_id=controller.id).all()
        )
        existing_machine_relay_numbers = [
            machine.relay_no for machine in existing_machines
        ]

        logger.info(f"Existing machine relay numbers: {existing_machine_relay_numbers}")

        for relay_no in range(1, controller.total_relays + 1):
            if relay_no in existing_machine_relay_numbers:
                continue

            # Default machine type - could be made configurable
            machine_type = (
                MachineType.WASHER if relay_no % 2 == 1 else MachineType.DRYER
            )

            machine = Machine(
                controller_id=controller.id,
                relay_no=relay_no,
                name=None,
                machine_type=machine_type,
                details={},
                base_price=Decimal("0.00"),
                pulse_duration=1000,
                coin_value=10,
                add_ons_options=[],
            )
            db.add(machine)
            machines.append(machine)

        db.commit()

        # Refresh all machines to get their IDs
        for machine in machines:
            db.refresh(machine)

        return machines

    @classmethod
    @with_db_session_classmethod
    def activate_machine(cls, db: Session, user: User, machine_id: UUID) -> Machine:
        machine = db.query(Machine).filter_by(id=machine_id).first()
        if not machine:
            raise ValueError("Machine not found")

        machine.activate()
        db.commit()
        db.refresh(machine)

        return machine

    @classmethod
    @with_db_session_classmethod
    def start(
        cls,
        db: Session,
        user: User,
        machine_id: UUID,
        total_amount: Decimal = None,
        pulse_value: int = 10,
    ) -> Machine:
        machine = db.query(Machine).filter_by(id=machine_id).first()
        if not machine:
            raise ValueError("Machine not found")

        machine.start()
        db.commit()
        db.refresh(machine)
        
        if total_amount:
            pulse_value = calculate_pulse_value(total_amount, machine.coin_value)

        topic = cls.MACHINE_ACTION_TOPIC.format(
            store_id=str(machine.controller.store_id),
            controller_id=str(machine.controller.device_id),
        )

        action_payload = {
            "machine_type": machine.machine_type.value,
            "relay_id": machine.relay_no,
            "pulse_duration": machine.pulse_duration,
            "pulse_interval": machine.pulse_interval,
            "value": pulse_value,
        }

        payload = {
            "version": "1.0.0",
            "event_type": MQTTEventTypeEnum.MACHINE_START.value,
            "timestamp": datetime.now().isoformat(),
            "correlation_id": str(uuid4()),
            "controller_id": str(machine.controller.device_id),
            "store_id": str(machine.controller.store_id),
            "payload": action_payload,
        }

        logger.info("Start machine operation", topic=topic, payload=payload)

        mqtt_client.publish(
            topic=topic,
            payload=payload,
        )

    @classmethod
    @with_db_session_classmethod
    def mark_as_in_progress(
        cls,
        db: Session,
        controller_device_id: str,
        machine_relay_no: int,
    ) -> Machine:
        machine = (
            db.query(Machine)
            .join(Controller, Machine.controller_id == Controller.id)
            .filter(
                Controller.device_id == controller_device_id,
                Machine.relay_no == machine_relay_no,
            )
            .first()
        )
        if not machine:
            raise ValueError("Machine not found")

        machine.mark_as_in_progress()
        db.commit()
        db.refresh(machine)

        logger.info("Marked machine as in progress", machine=machine)

        return machine

    @classmethod
    @with_db_session_classmethod
    def finish(
        cls,
        db: Session,
        controller_device_id: str,
        machine_relay_no: int,
    ) -> Machine:
        machine = (
            db.query(Machine)
            .join(Controller, Machine.controller_id == Controller.id)
            .filter(
                Controller.device_id == controller_device_id,
                Machine.relay_no == machine_relay_no,
            )
            .first()
        )
        if not machine:
            raise ValueError("Machine not found")

        machine.finish_operation()
        db.commit()
        db.refresh(machine)

        return machine

    @classmethod
    @with_db_session_classmethod
    def update_status(
        cls,
        db: Session,
        controller_device_id: str,
        machine_relay_no: int,
        status: MachineStatus,
    ) -> Machine:
        logger.info("Updating machine status", controller_device_id=controller_device_id, machine_relay_no=machine_relay_no, status=status)

        machine = (
            db.query(Machine)
            .join(Controller, Machine.controller_id == Controller.id)
            .filter(
                Controller.device_id == controller_device_id,
                Machine.relay_no == machine_relay_no,
            )
            .first()
        )

        if not machine:
            raise ValueError("Machine not found")

        machine.status = status.upper()
        db.commit()
        db.refresh(machine)

        return machine

    @classmethod
    def _get_authorized_store_ids(cls, db: Session, current_user: User):
        if current_user.is_admin:
            return [store.id for store in db.query(Store).all()]

        authorized_stores = (
            db.query(Store)
            .join(TenantMember, Store.tenant_id == TenantMember.tenant_id)
            .filter(TenantMember.user_id == current_user.id)
            .filter(TenantMember.is_enabled == True)
            .all()
        )

        return [store.id for store in authorized_stores]
