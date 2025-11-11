from datetime import datetime
from uuid import uuid4


def build_mqtt_payload_template(
    event_type: str,
    controller_id: str,
    store_id: str | None = None,
    payload: dict | None = None,
) -> dict:
    result = {
        "version": "1.0.0",
        "event_type": event_type,
        "timestamp": datetime.now().isoformat(),
        "correlation_id": str(uuid4()),
        "controller_id": None,
        "store_id": None,
        "payload": None,
    }
    
    if controller_id:
        result["controller_id"] = controller_id

    if store_id:
        result["store_id"] = store_id

    if payload:
        result["payload"] = payload
        
    return result
    