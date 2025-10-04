from datetime import datetime
import uuid

from paho.mqtt.client import MQTTMessage

from app.core.logging import logger
from app.enums.mqtt import MQTTEventTypeEnum
from app.libs import mqtt
from app.models.controller import Controller
from app.operations.controller.abandon_controller_operation import AbandonControllerOperation
from app.operations.machine.machine_operation import MachineOperation
from app.schemas.mqtt import MessagePayload


TOPIC_PATTERN = "lms/stores/+/controllers/+/ack"


class MachineAckSubscriber:

    def __init__(self, mqtt_client: mqtt.MQTTClient):
        self.mqtt_client = mqtt_client
        
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
            logger.error("controller_initialization_message_error", error=str(e), topic=message.topic)
            
    def handle_message(self, payload: MessagePayload, topic: str = TOPIC_PATTERN):
        """Handle incoming controller initialization messages"""
        try:
            # Parse topic: lms/stores/{store_id}/controllers/{controller_id}/ack
            topic_parts = topic.split("/")
            if len(topic_parts) < 6:
                raise ValueError(f"Invalid topic format: {topic}")
            
            store_id = topic_parts[2]
            controller_device_id = topic_parts[4]
            machine_relay_no = payload.payload.get("relay_id")
            
            logger.info(
                "Processing machine ack message",
                store_id=store_id,
                controller_device_id=controller_device_id,
                machine_relay_no=machine_relay_no,
                event_type=payload.event_type,
                topic=topic
            )
            
            if not controller_device_id or not machine_relay_no:
                raise ValueError("Invalid payload: missing controller_device_id or relay_id")
            
            # Handle different event types
            if payload.event_type == "start_ack":
                MachineOperation.mark_as_in_progress(controller_device_id, machine_relay_no)
            else:
                logger.warning("Unhandled event type", event_type=payload.event_type, topic=topic)
                
        except Exception as e:
            logger.error("machine_ack_message_error", error=str(e), topic=topic)
