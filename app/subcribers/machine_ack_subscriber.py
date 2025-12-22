from paho.mqtt.client import MQTTMessage

from app.core.celery_app import celery_app
from app.core.logging import logger
from app.enums.mqtt import MQTTEventTypeEnum
from app.libs import mqtt
from app.operations.machine.machine_operation import MachineOperation
from app.schemas.mqtt import MessagePayload


TOPIC_PATTERN = "lms/stores/+/controllers/+/ack"


class MachineAckSubscriber:

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
            logger.error(
                f"{self.class_name}_message_error", error=str(e), topic=message.topic
            )

    def handle_message(self, payload: MessagePayload, topic: str = TOPIC_PATTERN):
        """Handle incoming controller initialization messages"""
        logger.info(f"{self.class_name}_processing_message", payload=payload)

        try:
            # Handle different event types
            if payload.event_type == MQTTEventTypeEnum.MACHINE_START_ACK.value:
                self._handle_machine_start_ack(payload)
            elif payload.event_type == MQTTEventTypeEnum.UPDATE_FIRMWARE_ACK.value:
                self._handle_update_firmware_ack(payload)
            elif payload.event_type == MQTTEventTypeEnum.CANCEL_UPDATE_FIRMWARE_ACK.value:
                self._handle_cancel_update_firmware_ack(payload)
            else:
                logger.warning(
                    f"{self.class_name}_unhandled_event_type",
                    event_type=payload.event_type,
                    topic=topic,
                )

        except Exception as e:
            logger.error(f"{self.class_name}_message_error", error=str(e), topic=topic)

    def _handle_machine_start_ack(self, payload: MessagePayload):
        """Handle incoming machine start ack messages"""
        # Parse topic: lms/stores/{store_id}/controllers/{controller_id}/ack
        controller_device_id = payload.controller_id
        machine_relay_no = payload.payload.get("relay_id")

        if not controller_device_id or not machine_relay_no:
            raise ValueError("Controller device ID and machine relay no are required")

        MachineOperation.mark_as_in_progress(controller_device_id, machine_relay_no)

    def _handle_update_firmware_ack(self, payload: MessagePayload):
        """Handle incoming update firmware ack messages"""
        
        deployment_id = payload.payload.get("deployment_id")
        if not deployment_id:
            raise ValueError("Deployment ID is required")

        celery_app.send_task(
            "app.tasks.firmware.handle_update_firmware_ack_task",
            kwargs={"deployment_id": deployment_id},
        )

    def _handle_cancel_update_firmware_ack(self, payload: MessagePayload):
        """Handle incoming cancel update firmware ack messages"""
        
        deployment_id = payload.payload.get("deployment_id")
        if not deployment_id:
            raise ValueError("Deployment ID is required")

        celery_app.send_task(
            "app.tasks.firmware.handle_cancel_update_firmware_ack_task",
            kwargs={"deployment_id": deployment_id},
        )