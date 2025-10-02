from typing import Any
from pydantic import BaseModel


class MessagePayload(BaseModel):
  version: str
  event_type: str
  timestamp: str | None = None
  correlation_id: str | None = None
  controller_id: str 
  store_id: str | None = None
  payload: Any | None = None
