from app.core.config import settings
from app.core.logging import logger
from app.libs.mqtt import mqtt_client


DEMO_TOPIC = f"{settings.topic_prefix}/demo"


def turn_on_operation(relay_id: int):
    try:
        payload = {
            "code": "10001",
            "controller_id": "1",
            "relay_id": relay_id,
            "value": 10,
            "pulse_duration": 5,
        }
        mqtt_client.publish(DEMO_TOPIC, payload)
        logger.info(f"turn on action for relay {relay_id} success")
    except Exception as e:
        logger.error(f"turn on action for relay {relay_id} failed: {e}")
