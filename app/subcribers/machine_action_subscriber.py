from paho.mqtt.client import MQTTMessage

from app.core.celery_app import celery_app
from app.core.logging import logger
from app.enums.mqtt import MQTTEventTypeEnum
from app.libs import mqtt
from app.operations.machine.machine_operation import MachineOperation
from app.schemas.mqtt import MessagePayload


TOPIC_PATTERN = "lms/stores/+/controllers/+/actions"


class MachineActionSubscriber:

    def __init__(self, mqtt_client: mqtt.MQTTClient):
        self.mqtt_client = mqtt_client
        self.class_name = self.__class__.__name__.lower()
        
    def listen(self):
        """Subscribe to the controller initialization topic pattern"""
        # Subscribe to the topic pattern that matches any controller_id
        self.mqtt_client.add_topic_listener(TOPIC_PATTERN, self.on_message)

    def on_message(self, message: MQTTMessage):
        """Handle incoming controller initialization messages"""
        try:
            payload = MessagePayload.model_validate_json(message.payload)
            self.handle_message(payload, message.topic)
        except Exception as e:
            logger.error(f"{self.class_name}_message_error", error=str(e), topic=message.topic)

    def handle_message(self, payload: MessagePayload, topic: str = TOPIC_PATTERN):
        """Handle incoming controller initialization messages"""
        try:
            event_type = payload.event_type

            if event_type == MQTTEventTypeEnum.MACHINE_FINISH.value:
                self._handle_machine_finish(payload)
            elif event_type == MQTTEventTypeEnum.UPDATE_FIRMWARE_FAILED.value:
                self._handle_update_firmware_failed(payload)
            elif event_type == MQTTEventTypeEnum.UPDATE_FIRMWARE_COMPLETED.value:
                self._handle_update_firmware_completed(payload)
            else:
                logger.warning(f"{self.class_name}_unhandled_event_type", event_type=event_type, topic=topic)
        except Exception as e:
            logger.error(f"{self.class_name}_message_error", error=str(e), topic=topic)

    def _handle_machine_finish(self, payload: MessagePayload):
        """Handle incoming machine finish messages"""
        controller_device_id = payload.controller_id
        machine_relay_no = payload.payload.get("relay_id")

        if not controller_device_id or not machine_relay_no:
            raise ValueError("Controller device ID and machine relay no are required")

        MachineOperation.finish(payload.controller_id, payload.payload.get("relay_id"))

    def _handle_update_firmware_failed(self, payload: MessagePayload):
        """Handle incoming update firmware failed messages"""
        deployment_id = payload.payload.get("deployment_id")
        if not deployment_id:
            raise ValueError("Deployment ID is required")

        celery_app.send_task(
            "app.tasks.firmware.handle_update_firmware_failed_task",
            kwargs={"deployment_id": deployment_id},
        )
        
    def _handle_update_firmware_completed(self, payload: MessagePayload):
        """Handle incoming update firmware completed messages"""
        deployment_id = payload.payload.get("deployment_id")
        if not deployment_id:
            raise ValueError("Deployment ID is required")

        celery_app.send_task(
            "app.tasks.firmware.handle_update_firmware_completed_task",
            kwargs={"deployment_id": deployment_id},
        )
