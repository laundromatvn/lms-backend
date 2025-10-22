from paho.mqtt.client import MQTTMessage
from sqlalchemy import text

from app.core.logging import logger
from app.core.config import settings
from app.enums.mqtt import MQTTEventTypeEnum
from app.libs import mqtt
from app.models.controller import Controller
from app.models.datapoint import Datapoint, DatapointValueType
from app.operations.datapoint_operation import DatapointOperation
from app.operations.machine.machine_operation import MachineOperation
from app.schemas.mqtt import MessagePayload
from app.libs.database import get_session_factory

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
        db = get_session_factory()()

        try:
            machines = payload.payload.get("machines")
            if not machines:
                raise ValueError("Invalid payload: missing machines")

            controller = (
                db.query(Controller)
                .filter_by(device_id=payload.controller_id)
                .first()
            )
            if not controller:
                raise ValueError("Controller not found")

            new_datapoints = []
            for machine in machines:
                relay_no = machine.get("relay_id")
                status = machine.get("status")
                machine = MachineOperation.update_status(payload.controller_id, relay_no, status)

                new_datapoint = Datapoint(
                    tenant_id=controller.store.tenant_id,
                    store_id=controller.store_id,
                    controller_id=controller.id,
                    machine_id=machine.id,
                    relay_no=relay_no,
                    value=status.upper(),
                    value_type=DatapointValueType.MACHINE_STATE.value,
                )
                new_datapoints.append(new_datapoint)

            DatapointOperation.create_many(new_datapoints)
        except Exception as e:
            logger.error(f"{self.class_name}_message_error", error=str(e), topic=topic)
        finally:
            db.close()
