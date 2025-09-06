from app.core.config import settings
from app.core.logging import logger
from app.libs.mqtt import mqtt_client


DEMO_TOPIC = f"{settings.topic_prefix}/demo"
ACK_TOPIC = f"{settings.topic_prefix}/demo/ack"


def turn_on_operation(relay_id: int):
    _publish_turn_on_action(relay_id)
    _wait_for_turn_on_ack(relay_id)


def _publish_turn_on_action(relay_id: int):
    payload = {
        "code": "10001",
        "controller_id": "1",
        "relay_id": relay_id,
        "value": 10,
        "pulse_duration": 50,
    }
    mqtt_client.publish(DEMO_TOPIC, payload)


def _wait_for_turn_on_ack(relay_id: int):
    ack_payload = mqtt_client.wait_for_json(
        ACK_TOPIC,
        timeout_seconds=settings.ack_timeout_seconds,
        match={"controller_id": "1", "relay_id": relay_id},
    )

    if ack_payload is None:
        raise Exception(f"turn on action for relay {relay_id} ack timeout")

    code = ack_payload.get("code") if isinstance(ack_payload, dict) else None
    if code == "20001":
        return

    if code == "21001":
        raise Exception(f"turn on action for relay {relay_id} error ack: {code}")
