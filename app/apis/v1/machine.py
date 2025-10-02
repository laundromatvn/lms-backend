from fastapi import APIRouter, Depends, HTTPException, status
from uuid import UUID

from app.apis.deps import get_current_user
from app.models.user import User
from app.operations.machine import MachineOperation
from app.schemas.machine import (
    MachineSerializer,
    AddMachineRequest,
    UpdateMachineRequest,
    ListMachineQueryParams,
)
from app.schemas.pagination import PaginatedResponse
from app.utils.pagination import get_total_pages

router = APIRouter()


@router.get("", response_model=PaginatedResponse[MachineSerializer])
async def list_machines(
    query_params: ListMachineQueryParams = Depends(),
    current_user: User = Depends(get_current_user),
):
    """List machines with pagination and filtering"""
    try:
        total, machines = MachineOperation.list(query_params)
        # Convert dictionaries to MachineSerializer objects
        serialized_machines = [MachineSerializer(**machine) for machine in machines]

        return {
            "page": query_params.page,
            "page_size": query_params.page_size,
            "total": total,
            "total_pages": get_total_pages(total, query_params.page_size),
            "data": serialized_machines
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("", response_model=MachineSerializer, status_code=status.HTTP_201_CREATED)
async def create_machine(
    request: AddMachineRequest,
    current_user: User = Depends(get_current_user),
):
    """Create a new machine"""
    try:
        machine = MachineOperation.create(current_user, request)
        return MachineSerializer.model_validate(machine)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/{machine_id}", response_model=MachineSerializer)
async def get_machine(
    machine_id: UUID,
    current_user: User = Depends(get_current_user),
):
    """Get a specific machine by ID"""
    try:
        machine = MachineOperation.get(machine_id)
        return MachineSerializer.model_validate(machine)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.patch("/{machine_id}", response_model=MachineSerializer)
async def update_machine(
    machine_id: UUID,
    request: UpdateMachineRequest,
    current_user: User = Depends(get_current_user),
):
    """Update a machine partially"""
    try:
        machine = MachineOperation.update_partially(current_user, machine_id, request)
        return MachineSerializer.model_validate(machine)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.delete("/{machine_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_machine(
    machine_id: UUID,
    current_user: User = Depends(get_current_user),
):
    """Soft delete a machine"""
    try:
        MachineOperation.delete(current_user, machine_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/{machine_id}/restore", response_model=MachineSerializer)
async def restore_machine(
    machine_id: UUID,
    current_user: User = Depends(get_current_user),
):
    """Restore a soft-deleted machine"""
    try:
        machine = MachineOperation.restore(current_user, machine_id)
        return MachineSerializer.model_validate(machine)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/{machine_id}/start", response_model=MachineSerializer)
async def start_machine_operation(
    machine_id: UUID,
    current_user: User = Depends(get_current_user),
):
    """Start machine operation (set status to BUSY)"""
    try:
        machine = MachineOperation.start_operation(current_user, machine_id)
        return MachineSerializer.model_validate(machine)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/{machine_id}/finish", response_model=MachineSerializer)
async def finish_machine_operation(
    machine_id: UUID,
    current_user: User = Depends(get_current_user),
):
    """Finish machine operation (set status to IDLE)"""
    try:
        machine = MachineOperation.finish_operation(current_user, machine_id)
        return MachineSerializer.model_validate(machine)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/{machine_id}/out-of-service", response_model=MachineSerializer)
async def set_machine_out_of_service(
    machine_id: UUID,
    current_user: User = Depends(get_current_user),
):
    """Set machine out of service"""
    try:
        machine = MachineOperation.set_out_of_service(current_user, machine_id)
        return MachineSerializer.model_validate(machine)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/{machine_id}/mark-ready", response_model=MachineSerializer)
async def mark_machine_ready(
    machine_id: UUID,
    current_user: User = Depends(get_current_user),
):
    """Mark machine as ready for use after setup is complete"""
    try:
        machine = MachineOperation.mark_as_ready(current_user, machine_id)
        return MachineSerializer.model_validate(machine)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
