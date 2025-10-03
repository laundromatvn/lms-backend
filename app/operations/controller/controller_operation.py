from sqlalchemy.orm import Session
from uuid import UUID

from app.libs.database import with_db_session_classmethod
from app.models.controller import Controller
from app.models.store import Store
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
    def get(cls, db: Session, controller_id: UUID) -> Controller:
        controller = db.query(Controller).filter_by(id=controller_id).first()
        if not controller:
            raise ValueError("Controller not found")
        
        return controller
    
    @classmethod
    @with_db_session_classmethod
    def list(cls, db: Session, query_params: ListControllerQueryParams) -> tuple[int, list[dict]]:
        # Join with Store table to get store_name
        base_query = db.query(
            Controller,
            Store.name.label('store_name')
        ).outerjoin(Store, Controller.store_id == Store.id)

        if query_params.status:
            base_query = base_query.filter(Controller.status == query_params.status)
        if query_params.store_id:
            base_query = base_query.filter(Controller.store_id == query_params.store_id)

        total = base_query.count()
        results = (
            base_query
            .offset((query_params.page - 1) * query_params.page_size)
            .limit(query_params.page_size)
            .all()
        )
        
        # Convert results to dictionaries with store_name included
        controllers = []
        for controller, store_name in results:
            controller_dict = controller.to_dict()
            controller_dict['store_name'] = store_name
            controllers.append(controller_dict)
        
        return total, controllers
    
    @classmethod
    @with_db_session_classmethod
    def create(cls, db: Session, created_by: User, request: AddControllerRequest) -> Controller:
        if not cls._has_permission(created_by, request.store_id):
            raise PermissionError("You don't have permission to create controller")

        is_exist = db.query(Controller).filter(Controller.device_id == request.device_id).first()
        if is_exist:
            raise ValueError("Controller with this device ID already exists")
        
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
    def _handle_total_relays_change(cls, db: Session, controller: Controller, old_total_relays: int, new_total_relays: int) -> None:
        """Handle changes to total_relays by adding or removing machines"""
        
        if new_total_relays < old_total_relays:
            # Decrease: Soft delete excess machines (from highest relay numbers)
            cls._soft_delete_excess_machines(db, controller, new_total_relays)
        elif new_total_relays > old_total_relays:
            # Increase: Create new machines for additional relays
            cls._create_additional_machines(db, controller, old_total_relays, new_total_relays)
    
    @classmethod
    def _soft_delete_excess_machines(cls, db: Session, controller: Controller, new_total_relays: int) -> None:
        """Soft delete machines with relay_no > new_total_relays"""
        excess_machines = db.query(Machine).filter(
            Machine.controller_id == controller.id,
            Machine.relay_no > new_total_relays,
            Machine.deleted_at.is_(None)  # Only get non-deleted machines
        ).all()
        
        for machine in excess_machines:
            machine.soft_delete()
    
    @classmethod
    def _create_additional_machines(cls, db: Session, controller: Controller, old_total_relays: int, new_total_relays: int) -> None:        
        # Get existing machine relay numbers
        existing_machines = db.query(Machine).filter_by(controller_id=controller.id).all()
        existing_machine_relay_numbers = [machine.relay_no for machine in existing_machines]
        
        for existing_machine in existing_machines:
            existing_machine.restore()
            db.add(existing_machine)
        db.commit()
        
        """Create new machines for additional relays"""
        for relay_no in range(old_total_relays + 1, new_total_relays + 1):
            if relay_no in existing_machine_relay_numbers:
                continue
            
            # Default machine type - could be made configurable
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
    def _has_permission(cls, current_user: User, store_id_or_controller) -> bool:
        return True
