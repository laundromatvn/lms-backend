from datetime import datetime
import uuid

from paho.mqtt.client import MQTTMessage

from app.core.logging import logger
from app.enums.mqtt import MQTTEventTypeEnum
from app.libs import mqtt
from app.models.controller import Controller
from app.operations.controller.abandon_controller_operation import AbandonControllerOperation
from app.schemas.mqtt import MessagePayload


TOPIC = "lms/controllers/initialization"
RESPONSE_TOPIC = "lms/controllers/{device_id}/wait_admin_assign_store"


class RegisterControllerSubcriber:
    def __init__(self, mqtt_client: mqtt.MQTTClient):
        self.mqtt_client = mqtt_client
        
    def listen(self):
        """Subscribe to the controller initialization topic pattern"""
        # Subscribe to the topic pattern that matches any controller_id
        topic_pattern = "lms/controllers/initialization"
        self.mqtt_client.add_topic_listener(topic_pattern, self.on_message)

    def on_message(self, message: MQTTMessage):
        """Handle incoming controller initialization messages"""
        try:
            payload = MessagePayload.model_validate_json(message.payload)
            self.handle_message(payload, message.topic)
        except Exception as e:
            logger.error("controller_initialization_message_error", error=str(e), topic=message.topic)
            
    def handle_message(self, payload: MessagePayload, topic: str = TOPIC):
        """Handle incoming controller initialization messages"""
        try:
            controller = AbandonControllerOperation.register(payload.controller_id)
            response_topic = RESPONSE_TOPIC.format(device_id=payload.controller_id)
            if controller:
                payload = self.build_existing_controller_payload(controller)
            else:
                payload = self.build_pending_controller_payload(payload.controller_id)
            logger.info("controller_initialization_response_topic", response_topic=response_topic, controller=controller, payload=payload)
            self.mqtt_client.publish(topic=response_topic, payload=payload)
        except Exception as e:
            logger.error("controller_initialization_message_error", error=str(e), topic=topic)
            
    def build_existing_controller_payload(self, controller: Controller):
        """Build the existing controller response"""
        return {
            "version": "1.0.0",
            "event_type": MQTTEventTypeEnum.STORE_ASSIGNMENT.value,
            "timestamp": datetime.now().isoformat(),
            "correlation_id": str(uuid.uuid4()),
            "controller_id": str(controller.device_id),
            "store_id": str(controller.store_id),
            "payload": {
                "status": "ASSIGNED",
            },
        }

    def build_pending_controller_payload(self, controller_id: str):
        """Build the pending controller response"""
        return {
            "version": "1.0.0",
            "event_type": MQTTEventTypeEnum.CONTROLLER_INIT_RESPONSE.value,
            "timestamp": datetime.now().isoformat(),
            "correlation_id": str(uuid.uuid4()),
            "controller_id": str(controller_id),
            "store_id": None,
            "payload": {
                "status": "PENDING_ASSIGNMENT",
            },
        }
