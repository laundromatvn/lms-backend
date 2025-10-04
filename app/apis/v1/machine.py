from fastapi import APIRouter, Depends, HTTPException, Path, status
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

        return {
            "page": query_params.page,
            "page_size": query_params.page_size,
            "total": total,
            "total_pages": get_total_pages(total, query_params.page_size),
            "data": machines,
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
        return machine
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
        return machine
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


@router.post("/{machine_id}/start")
async def start_machine_operation(
    machine_id: UUID,
    current_user: User = Depends(get_current_user),
):
    """Start machine operation (set status to BUSY)"""
    try:
        MachineOperation.start(current_user, machine_id)
        return {"message": "Machine operation started"}
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


@router.post("/{machine_id}/activate")
async def activate_machine(
    machine_id: UUID,
    current_user: User = Depends(get_current_user),
):
    """Activate machine (set status to IDLE)"""
    try:
        MachineOperation.activate_machine(current_user, machine_id)
        return {"message": "Machine activated"}
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
