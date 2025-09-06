import json
import threading
import time
import uuid
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional

import paho.mqtt.client as mqtt

from app.core.config import settings
from app.core.logging import logger


MessageHandler = Callable[[mqtt.MQTTMessage], None]


@dataclass
class BrokerConfig:
    host: str
    port: int
    client_id: str


class MQTTClient:
    def __init__(
        self,
        broker: BrokerConfig,
        username: Optional[str],
        password: Optional[str],
        tls: bool,
    ):
        self.broker = broker
        self.username = username
        self.password = password

        self.connected_event = threading.Event()
        self._lock = threading.Lock()
        self._subscriptions: Dict[str, int] = {}
        # Waiters keyed by topic, each waiter contains a predicate, an event and a captured message
        self._waiters: Dict[str, List[Dict[str, Any]]] = {}

        self.client = mqtt.Client(client_id=broker.client_id, clean_session=True)
        if username or password:
            self.client.username_pw_set(
                username=username or "",
                password=password or "",
            )
                
        if tls:
            self.client.tls_set()

        self.client.reconnect_delay_set(
            min_delay=settings.mqtt_reconnect_delay,
            max_delay=settings.mqtt_reconnect_delay_max,
        )

        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.client.on_log = self._on_log
        self.client.on_message = self._on_message
        self.client.on_subscribe = self._on_subscribe

    def initialize(self):
        self.client.connect(
            self.broker.host,
            self.broker.port,
            keepalive=settings.mqtt_keepalive,
        )

    def _on_connect(self, _client, _userdata, _flags, rc):
        if rc == 0:
            logger.info(
                "mqtt_connected",
                host=self.broker.host,
                port=self.broker.port,
                client_id=self.broker.client_id,
            )
            self.connected_event.set()
            # Re-subscribe to all known topics upon (re)connect
            with self._lock:
                for topic, qos in self._subscriptions.items():
                    try:
                        self.client.subscribe(topic, qos=qos)
                        logger.debug("mqtt_resubscribe", topic=topic, qos=qos)
                    except Exception as exc:
                        logger.error("mqtt_resubscribe_error", topic=topic, error=str(exc))
        else:
            logger.warning(
                "mqtt_connect_failed",
                rc=rc,
                host=self.broker.host,
                port=self.broker.port,
            )

    def _on_disconnect(self, _client, _userdata, rc):
        self.connected_event.clear()
        logger.warning(
            "mqtt_disconnected",
            rc=rc,
            host=self.broker.host,
            port=self.broker.port,
        )

    def _on_log(self, _client, _userdata, level, buf):
        logger.debug(
            "mqtt_log",
            host=self.broker.host,
            port=self.broker.port,
            level=level,
            msg=buf,
        )
        
    def _on_message(self, _client, _userdata, message):
        logger.info(
            "mqtt_message",
            topic=message.topic,
            payload=message.payload,
        )
        # Notify any waiters for this topic
        with self._lock:
            waiters = self._waiters.get(message.topic, [])
            if not waiters:
                return
            to_remove: List[Dict[str, Any]] = []
            for waiter in waiters:
                predicate: Callable[[mqtt.MQTTMessage], bool] = waiter["predicate"]
                try:
                    if predicate(message):
                        waiter["captured_message"] = message
                        waiter["event"].set()
                        to_remove.append(waiter)
                except Exception as exc:
                    logger.error("mqtt_waiter_predicate_error", topic=message.topic, error=str(exc))
            if to_remove:
                # Remove completed waiters
                self._waiters[message.topic] = [w for w in waiters if w not in to_remove]

    def _on_subscribe(self, _client, _userdata, mid, granted_qos):
        logger.debug(
            "mqtt_subscribed",
            host=self.broker.host,
            port=self.broker.port,
            mid=mid,
            qos=granted_qos,
        )

    def connect(self):
        self.client.connect(
            self.broker.host,
            self.broker.port,
            keepalive=settings.mqtt_keepalive,
        )

    def loop_start(self):
        self.client.loop_start()

    def loop_stop(self):
        self.client.loop_stop()

    def disconnect(self):
        try:
            self.client.disconnect()
        except Exception as exc:
            logger.error(
                "mqtt_disconnect_error",
                error=str(exc),
                host=self.broker.host,
                port=self.broker.port,
            )

    def publish(self, topic: str, payload: dict, qos: int = 0, retain: bool = False) -> bool:
        if not self.connected_event.is_set():
            return False
        try:
            payload = json.dumps(payload)   
            result = self.client.publish(topic, payload=payload, qos=qos, retain=retain)
            return result.rc == mqtt.MQTT_ERR_SUCCESS
        except Exception as exc:
            logger.error(
                "mqtt_publish_error",
                error=str(exc),
                host=self.broker.host,
                port=self.broker.port,
            )
            return False

    def subscribe(self, topic: str, qos: int = 0) -> bool:
        with self._lock:
            self._subscriptions[topic] = qos
        try:
            if self.connected_event.is_set():
                self.client.subscribe(topic, qos=qos)
            logger.debug("mqtt_subscribe_initiated", topic=topic, qos=qos)
            return True
        except Exception as exc:
            logger.error("mqtt_subscribe_error", topic=topic, error=str(exc))
            return False

    def wait_for_json(
        self,
        topic: str,
        timeout_seconds: Optional[int] = None,
        match: Optional[Dict[str, Any]] = None,
    ) -> Optional[Dict[str, Any]]:
        self.subscribe(topic, qos=0)

        event = threading.Event()
        waiter: Dict[str, Any] = {
            "predicate": lambda msg: self._json_predicate(msg, match),
            "event": event,
            "captured_message": None,
        }
        with self._lock:
            self._waiters.setdefault(topic, []).append(waiter)

        timeout = timeout_seconds if timeout_seconds is not None else settings.ack_timeout_seconds
        signaled = event.wait(timeout=timeout)
        if not signaled:
            with self._lock:
                waiters = self._waiters.get(topic, [])
                if waiter in waiters:
                    self._waiters[topic] = [w for w in waiters if w is not waiter]
            logger.warning("mqtt_wait_for_json_timeout", topic=topic, timeout_seconds=timeout)
            return None

        message: Optional[mqtt.MQTTMessage] = waiter.get("captured_message")
        if not message:
            return None
        try:
            payload_str = message.payload.decode("utf-8") if isinstance(message.payload, (bytes, bytearray)) else str(message.payload)
            return json.loads(payload_str)
        except Exception as exc:
            logger.error("mqtt_wait_for_json_parse_error", topic=topic, error=str(exc))
            return None

    def _json_predicate(self, message: mqtt.MQTTMessage, match: Optional[Dict[str, Any]]) -> bool:
        try:
            payload_str = message.payload.decode("utf-8") if isinstance(message.payload, (bytes, bytearray)) else str(message.payload)
            data = json.loads(payload_str)
        except Exception:
            return False
        if not match:
            return True
        for key, expected in match.items():
            if key not in data or data[key] != expected:
                return False
        return True

_unique_client_id = f"{settings.mqtt_client_id_prefix}-{uuid.uuid4().hex[:8]}"

mqtt_client = MQTTClient(
    broker=BrokerConfig(
        host=settings.mqtt_host,
        port=settings.mqtt_port,
        client_id=_unique_client_id,
    ),
    username=settings.mqtt_username,
    password=settings.mqtt_password,
    tls=False,
)


def start():
    mqtt_client.initialize()
    mqtt_client.loop_start()


def stop():
    mqtt_client.loop_stop()
