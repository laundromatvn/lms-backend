from fastapi import APIRouter, HTTPException

from pydantic import BaseModel

from app.operations.demo.turn_on_operation import turn_on_operation
from app.operations.demo.turn_off_operation import turn_off_operation


router = APIRouter()


class TurnOnRequest(BaseModel):
    relay_id: int


@router.post("/turn-on")
async def turn_on(request: TurnOnRequest):
    try:
        turn_on_operation(request.relay_id)
    except Exception as e:
        raise HTTPException(status_code=422, detail=str(e))

    return {"message": f"turn on action for device {request.relay_id}", "ack": True}


class TurnOffRequest(BaseModel):
    relay_id: int


@router.post("/turn-off")
async def turn_off(request: TurnOffRequest):
    try:
        turn_off_operation(request.relay_id)
    except Exception as e:
        raise HTTPException(status_code=422, detail=str(e))

    return {"message": f"turn off action for device {request.relay_id}", "ack": True}
