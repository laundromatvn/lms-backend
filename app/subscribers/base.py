import json
from typing import Any

import paho.mqtt.client as mqtt

from app.core.logging import logger
from app.libs.mqtt import MQTTClient


class BaseSubscriber:
    """Base class for single-topic MQTT subscribers.

    Subclasses must set `TOPIC` and implement `handle(self, topic, payload)`.
    The base class will subscribe to the topic and dispatch messages to `handle`.
    If the payload is JSON, it is parsed and passed as a Python object; otherwise
    the UTF-8 decoded string (or raw payload) is passed.
    """

    TOPIC: str = ""
    QOS: int = 0

    def register(self, client: MQTTClient) -> None:
        if not self.TOPIC:
            raise ValueError(f"{self.__class__.__name__}.TOPIC must be set")
        client.subscribe(self.TOPIC, qos=self.QOS)
        logger.debug(
            "subscriber_topic",
            topic=self.TOPIC,
            qos=self.QOS,
            subscriber=self.__class__.__name__,
        )
        client.add_topic_listener(self.TOPIC, self._on_message)

    def _on_message(self, message: mqtt.MQTTMessage) -> None:
        topic = message.topic
        payload_raw = message.payload
        payload: Any
        try:
            payload_str = (
                payload_raw.decode("utf-8")
                if isinstance(payload_raw, (bytes, bytearray))
                else str(payload_raw)
            )
            try:
                payload = json.loads(payload_str)
            except Exception:
                payload = payload_str
        except Exception as exc:
            logger.error("subscriber_payload_decode_error", topic=topic, error=str(exc))
            payload = None
        try:
            self.handle(topic=topic, payload=payload)
        except Exception as exc:
            logger.error("subscriber_handle_error", topic=topic, error=str(exc))

    def handle(self, topic: str, payload: Any) -> None:  # noqa: ARG002
        """Process a message received on `TOPIC`.

        Subclasses must implement this.
        """
        raise NotImplementedError
