from typing import Any

from app.core.config import settings
from app.core.logging import logger
from app.subscribers.base import BaseSubscriber


TOPIC_PREFIX = settings.topic_prefix


class DemoTurnOnSubscriber(BaseSubscriber):
    TOPIC = f"{TOPIC_PREFIX}/demo"
    QOS = 1

    def handle(self, topic: str, payload: Any) -> None:
        logger.info("demo", topic=topic, payload=payload)
