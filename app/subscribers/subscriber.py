from typing import List

from app.core.logging import logger
from app.libs.mqtt import MQTTClient
from app.subscribers.base import BaseSubscriber


class SubscriberManager:
    def __init__(self, client: MQTTClient, subscribers: List[BaseSubscriber]):
        self._client = client
        self._subscribers = subscribers
        self._started = False

    def start(self) -> None:
        logger.info("starting subscriber manager")
        
        if self._started:
            return
        
        logger.info("registering subscribers", subscribers=self._subscribers)

        for subscriber in self._subscribers:
            try:
                subscriber.register(self._client)
                logger.info(
                    "subscriber_registered",
                    topic=subscriber.TOPIC,
                    subscriber=subscriber.__class__.__name__,
                )
            except Exception as exc:
                logger.error(
                    "subscriber_register_error",
                    error=str(exc),
                    subscriber=subscriber.__class__.__name__,
                )
        self._started = True

    def stop(self) -> None:
        if not self._started:
            return
        for subscriber in self._subscribers:
            try:
                self._client.remove_topic_listener(subscriber.TOPIC, subscriber._on_message)
                logger.info(
                    "subscriber_unregistered",
                    topic=subscriber.TOPIC,
                    subscriber=subscriber.__class__.__name__,
                )
            except Exception as exc:
                logger.error(
                    "subscriber_unregister_error",
                    error=str(exc),
                    subscriber=subscriber.__class__.__name__,
                )
        self._started = False
