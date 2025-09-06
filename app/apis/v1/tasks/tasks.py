from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.core.logging import logger
from app.libs.task_manager import task_manager

router = APIRouter()


@router.get("/{task_id}")
async def get_task(task_id: str):
    task = task_manager.get(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return task
