from paho.mqtt.client import MQTTMessage

from app.libs import mqtt
from app.core.logging import logger
from app.schemas.mqtt import MessagePayload
from app.operations.controller.abandon_controller_operation import AbandonControllerOperation


TOPIC = "lms/controllers/initialization"


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
            logger.info("controller_initialization_received", payload=payload, topic=topic)
            result = AbandonControllerOperation.register(payload.controller_id)
            logger.info("controller_initialization_registered", result=result, topic=topic)
        except Exception as e:
            logger.error("controller_initialization_message_error", error=str(e), topic=topic)
