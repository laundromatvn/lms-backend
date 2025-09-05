import json
import threading
import time
import uuid
from dataclasses import dataclass
from typing import Callable, Dict, List, Optional

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


mqtt_client = MQTTClient(
    broker=BrokerConfig(
        host=settings.mqtt_host,
        port=settings.mqtt_port,
        client_id=settings.mqtt_client_id_prefix,
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
