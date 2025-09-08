"""MQTT consumers package.

Modules in this package define subscribers that register MQTT topic
subscriptions and message handlers. The worker entrypoint dynamically
discovers and loads all modules matching "*_subscriber.py".
"""

from typing import List

from app.subscribers.demo_subscriber import DemoTurnOnSubscriber

from app.subscribers.subscriber import SubscriberManager


subscriber_list: List = [
    DemoTurnOnSubscriber(),
]

__all__ = [
    "subscriber_list",
    "SubscriberManager",
]
