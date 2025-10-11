from paho.mqtt.client import MQTTMessage

from app.core.logging import logger
from app.enums.mqtt import MQTTEventTypeEnum
from app.libs import mqtt
from app.operations.machine.machine_operation import MachineOperation
from app.schemas.mqtt import MessagePayload


TOPIC_PATTERN = "lms/stores/+/controllers/+/metrics"


class MachineMetricSubscriber:

    def __init__(self, mqtt_client: mqtt.MQTTClient):
        self.mqtt_client = mqtt_client
        self.class_name = self.__class__.__name__.lower()
        
    def listen(self):
        self.mqtt_client.add_topic_listener(TOPIC_PATTERN, self.on_message)

    def on_message(self, message: MQTTMessage):
        try:
            payload = MessagePayload.model_validate_json(message.payload)
            self.handle_message(payload, message.topic)
        except Exception as e:
            logger.error(f"{self.class_name}_message_error", error=str(e), topic=message.topic)

    def handle_message(self, payload: MessagePayload, topic: str = TOPIC_PATTERN):
        try:
            event_type = payload.event_type
            if event_type == MQTTEventTypeEnum.MACHINE_STATE.value:
                self._handle_machine_state(payload, topic)
            else:
                raise ValueError(f"Unsupported event type: {event_type}")
        except Exception as e:
            logger.error(f"{self.class_name}_message_error", error=str(e), topic=topic)


    def _handle_machine_state(self, payload: MessagePayload, topic: str = TOPIC_PATTERN):
        try:
            machines = payload.payload.get("machines")
            if not machines:
                raise ValueError("Invalid payload: missing machines")

            for machine in machines:
                relay_no = machine.get("relay_id")
                status = machine.get("status")
                MachineOperation.update_status(payload.controller_id, relay_no, status)
        except Exception as e:
            logger.error(f"{self.class_name}_message_error", error=str(e), topic=topic)