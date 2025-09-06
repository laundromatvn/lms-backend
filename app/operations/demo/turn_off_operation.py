from app.core.config import settings
from app.core.logging import logger
from app.libs.mqtt import mqtt_client


DEMO_TOPIC = f"{settings.topic_prefix}/demo"
ACK_TOPIC = f"{settings.topic_prefix}/demo/ack"


def turn_off_operation(relay_id: int):
    _publish_turn_off_action(relay_id)
    _wait_for_turn_off_ack(relay_id)

def _publish_turn_off_action(relay_id: int):
    payload = {
        "code": "10002",
        "controller_id": "1",
        "relay_id": relay_id,
        "value": 0,
        "pulse_duration": 5,
    }
    mqtt_client.publish(DEMO_TOPIC, payload)


def _wait_for_turn_off_ack(relay_id: int):
    ack_payload = mqtt_client.wait_for_json(
        ACK_TOPIC,
        timeout_seconds=settings.ack_timeout_seconds,
        match={"controller_id": "1", "relay_id": relay_id},
    )

    if ack_payload is None:
        raise Exception(f"turn off action for relay {relay_id} ack timeout")

    code = ack_payload.get("code") if isinstance(ack_payload, dict) else None
    if code == "20002":
        return

    if code == "21001":
        raise Exception(f"turn off action for relay {relay_id} error ack: {code}")
