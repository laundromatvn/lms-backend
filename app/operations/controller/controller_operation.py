from sqlalchemy.orm import Session
from uuid import UUID

from app.libs.database import with_db_session_classmethod
from app.models.controller import Controller, ControllerStatus
from app.models.store import Store
from app.models.firmware import Firmware
from app.models.tenant_member import TenantMember
from app.models.user import User
from app.schemas.controller import (
    AddControllerRequest,
    UpdateControllerRequest,
    ListControllerQueryParams,
)
from app.operations.machine import MachineOperation
from app.models.machine import Machine, MachineType
from decimal import Decimal


class ControllerOperation:

    @classmethod
    @with_db_session_classmethod
    def get(cls, db: Session, current_user: User, controller_id: UUID) -> Controller:
        controller = (
            db.query(
                *Controller.__table__.columns,
                Store.id.label('store_id'),
                Store.name.label('store_name'),
                Firmware.id.label('firmware_id'),
                Firmware.name.label('firmware_name'),
                Firmware.version.label('firmware_version'),
            )
            .join(Store, Controller.store_id == Store.id)
            .join(Firmware, Controller.provisioned_firmware_id == Firmware.id)
            .filter(
                Controller.deleted_at.is_(None),
                Controller.id == controller_id,
            )
            .first()
        )
        if not controller:
            raise ValueError("Controller not found")
        
        if not current_user.is_admin:
            authorized_store_ids = cls._get_authorized_store_ids(db, current_user)
            if controller.store_id not in authorized_store_ids:
                raise PermissionError("You don't have permission to get this controller")

        return controller

    @classmethod
    @with_db_session_classmethod
    def list(cls, db: Session, current_user: User, query_params: ListControllerQueryParams) -> tuple[int, list[dict]]:
        base_query = (
            db.query(
                *Controller.__table__.columns,
                Store.id.label('store_id'),
                Store.name.label('store_name'),
                Firmware.id.label('firmware_id'),
                Firmware.name.label('firmware_name'),
                Firmware.version.label('firmware_version'),
            )
            .outerjoin(Store, Controller.store_id == Store.id)
            .outerjoin(Firmware, Controller.provisioned_firmware_id == Firmware.id)
            .filter(
                Controller.deleted_at.is_(None),
                Controller.status.notin_([ControllerStatus.INACTIVE]),
                Firmware.id.isnot(None),
            )
        )
        
        if not current_user.is_admin:
            authorized_store_ids = cls._get_authorized_store_ids(db, current_user)
            base_query = base_query.filter(Controller.store_id.in_(authorized_store_ids))

        if query_params.status:
            base_query = base_query.filter(Controller.status == query_params.status)
        if query_params.store_id:
            base_query = base_query.filter(Controller.store_id == query_params.store_id)
            
        base_query = base_query.order_by(Controller.created_at.desc())

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
    def create(cls, db: Session, created_by: User, request: AddControllerRequest) -> Controller:
        if not cls._has_permission(created_by, request.store_id):
            raise PermissionError("You don't have permission to create controller")

        existing_controllers = db.query(Controller).filter(
            Controller.device_id == request.device_id,
            Controller.deleted_at.is_(None)  # Only get non-deleted controllers
        ).all()
        
        for existing_controller in existing_controllers:
            existing_controller.soft_delete()
            for machine in existing_controller.machines:
                machine.soft_delete()
        
        controller = Controller(
            device_id=request.device_id,
            name=request.name,
            store_id=request.store_id,
            total_relays=request.total_relays,
            status=request.status,
        )
        db.add(controller)
        db.commit()
        db.refresh(controller)

        MachineOperation.create_machines_for_controller(controller)

        return controller
    
    @classmethod
    @with_db_session_classmethod
    def update_partially(cls, db: Session, updated_by: User, controller_id: UUID, request: UpdateControllerRequest) -> Controller:
        controller = db.query(Controller).filter_by(id=controller_id).first()
        if not controller:
            raise ValueError("Controller not found")
        
        if not cls._has_permission(updated_by, controller):
            raise PermissionError("You don't have permission to update this controller")
        
        update_data = request.model_dump(exclude_unset=True)
        
        # Handle device_id changes - ensure only one active controller per device_id
        if 'device_id' in update_data:
            new_device_id = update_data['device_id']
            if new_device_id != controller.device_id:
                # Find and soft delete existing controllers with the new device_id
                existing_controllers = db.query(Controller).filter(
                    Controller.device_id == new_device_id,
                    Controller.deleted_at.is_(None),
                    Controller.id != controller.id  # Don't delete the current controller
                ).all()
                
                for existing_controller in existing_controllers:
                    existing_controller.soft_delete()
                    # Also soft delete all machines associated with these controllers
                    for machine in existing_controller.machines:
                        machine.soft_delete()
        
        # Handle total_relays changes before updating the controller
        if 'total_relays' in update_data:
            new_total_relays = update_data['total_relays']
            old_total_relays = controller.total_relays
            
            if new_total_relays != old_total_relays:
                cls._handle_total_relays_change(db, controller, old_total_relays, new_total_relays)

        for field, value in update_data.items():
            if hasattr(controller, field):
                setattr(controller, field, value)
        
        db.commit()
        db.refresh(controller)
        
        return controller

    @classmethod
    @with_db_session_classmethod
    def delete(cls, db: Session, deleted_by: User, controller_id: UUID) -> None:
        controller = db.query(Controller).filter_by(id=controller_id).first()
        if not controller:
            raise ValueError("Controller not found")
        
        if not cls._has_permission(deleted_by, controller):
            raise PermissionError("You don't have permission to delete this controller")

        # delete all machines
        for machine in controller.machines:
            machine.soft_delete()

        controller.soft_delete()
        db.commit()

    @classmethod
    @with_db_session_classmethod
    def activate_controller_machines(cls, db: Session, user: User, controller_id: UUID) -> None:
        controller = db.query(Controller).filter_by(id=controller_id).first()
        if not controller:
            raise ValueError("Controller not found")

        machines = controller.machines
        for machine in machines:
            if machine.relay_no > controller.total_relays:
                machine.out_of_service()
            else:
                machine.activate()
        db.commit()
        db.refresh(controller)

        return controller

    @classmethod
    def _handle_total_relays_change(cls, db: Session, controller: Controller, old_total_relays: int, new_total_relays: int) -> None:
        """Handle changes to total_relays by managing machines according to the new requirements"""
        
        if new_total_relays == old_total_relays:
            # Case 1: new_total_relays = old_total_relays
            # Activate machines from relay_no = 1 to relay_no = new_total_relays
            cls._activate_machines_range(db, controller, 1, new_total_relays)
            
        elif new_total_relays < old_total_relays:
            # Case 2: new_total_relays < old_total_relays
            # Activate machines from relay_no = 1 to relay_no = new_total_relays
            cls._activate_machines_range(db, controller, 1, new_total_relays)
            # Soft delete machines from relay_no = new_total_relays + 1 to old_total_relays
            cls._soft_delete_excess_machines(db, controller, new_total_relays, old_total_relays)
            
        else:  # new_total_relays > old_total_relays
            # Case 3: new_total_relays > old_total_relays
            # Check if number of existing machines is enough, activate
            cls._activate_machines_range(db, controller, 1, new_total_relays)
            # Create if need
            cls._create_additional_machines(db, controller, old_total_relays, new_total_relays)
    
    @classmethod
    def _soft_delete_excess_machines(cls, db: Session, controller: Controller, new_total_relays: int, old_total_relays: int) -> None:
        """Soft delete machines with relay_no from new_total_relays + 1 to old_total_relays"""
        excess_machines = db.query(Machine).filter(
            Machine.controller_id == controller.id,
            Machine.relay_no > new_total_relays,
            Machine.relay_no <= old_total_relays,
            Machine.deleted_at.is_(None)  # Only get non-deleted machines
        ).all()
        
        for machine in excess_machines:
            machine.soft_delete()
    
    @classmethod
    def _create_additional_machines(cls, db: Session, controller: Controller, old_total_relays: int, new_total_relays: int) -> None:        
        # Get existing machine relay numbers
        existing_machines = db.query(Machine).filter_by(controller_id=controller.id).all()
        existing_machine_relay_numbers = [machine.relay_no for machine in existing_machines]
        
        # Create machines only for relay numbers that don't exist
        for relay_no in range(old_total_relays + 1, new_total_relays + 1):
            if relay_no in existing_machine_relay_numbers:
                continue

            machine_type = MachineType.WASHER if relay_no % 2 == 1 else MachineType.DRYER
            
            machine = Machine(
                controller_id=controller.id,
                relay_no=relay_no,
                name=None,
                machine_type=machine_type,
                details={},
                base_price=Decimal('0.00'),
            )
            db.add(machine)
    
    @classmethod
    def _activate_machines_range(cls, db: Session, controller: Controller, start_relay: int, end_relay: int) -> None:
        """Activate machines from start_relay to end_relay (inclusive)"""
        machines = db.query(Machine).filter(
            Machine.controller_id == controller.id,
            Machine.relay_no >= start_relay,
            Machine.relay_no <= end_relay
        ).all()
        
        for machine in machines:
            machine.restore()  # This will set deleted_at to None and status to IDLE if it was OUT_OF_SERVICE
            db.add(machine)
    
    @classmethod
    def _has_permission(cls, current_user: User, store_id_or_controller) -> bool:
        return True

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