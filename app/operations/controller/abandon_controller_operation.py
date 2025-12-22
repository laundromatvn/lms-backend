from datetime import datetime
import uuid

from sqlalchemy.orm import Session

from app.libs.mqtt import mqtt_client
from app.libs.database import with_db_session_classmethod
from app.libs.cache import cache_manager
from app.models.controller import Controller, ControllerStatus
from app.enums.mqtt import MQTTEventTypeEnum


class AbandonControllerOperation:
    ABANDONED_CONTROLLERS_CACHE_KEY = "abandoned_controllers"
    WAIT_ADMIN_ASSIGN_STORE_TOPIC = "lms/controllers/{device_id}/wait_admin_assign_store"

    @classmethod
    def list(cls):
        result = cache_manager.get(cls.ABANDONED_CONTROLLERS_CACHE_KEY)
        if result:
            return result

    @classmethod
    def verify(cls, device_id: str):
        topic = cls.WAIT_ADMIN_ASSIGN_STORE_TOPIC.format(device_id=device_id)
        payload = {
            "version": "1.0.0",
            "event_type": MQTTEventTypeEnum.CONTROLLER_VERIFICATION.value,
            "timestamp": datetime.now().isoformat(),
            "correlation_id": str(uuid.uuid4()),
            "controller_id": str(device_id),
            "store_id": None,
            "payload": {
                "relay_id": 1,
                "pulse_duration": 50,
                "pulse_interval": 100,
                "value": 5,
            },
        }

        mqtt_client.publish(
            topic=topic,
            payload=payload,
        )

    @classmethod
    @with_db_session_classmethod
    def register(cls, db: Session, device_id: str):
        controller = (
            db.query(Controller)
            .filter(
                Controller.device_id == device_id,
                Controller.deleted_at.is_(None),
                Controller.status.in_([ControllerStatus.NEW, ControllerStatus.ACTIVE]),
            )
            .first()
        )
        if controller and controller.store_id:
            return controller

        abandon_controllers = cache_manager.get(cls.ABANDONED_CONTROLLERS_CACHE_KEY)
        if abandon_controllers:
            abandon_controllers = list(set(abandon_controllers + [device_id]))
        else:
            abandon_controllers = [device_id]

        cache_manager.set(
            cls.ABANDONED_CONTROLLERS_CACHE_KEY,
            abandon_controllers,
            ttl_seconds=60 * 15,
        )

    @classmethod
    def confirm_assignment(cls, controller: Controller):
        topic = cls.WAIT_ADMIN_ASSIGN_STORE_TOPIC.format(device_id=controller.device_id)
        payload = {
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

        mqtt_client.publish(
            topic=topic,
            payload=payload,
        )

    @classmethod
    def remove(cls, device_id: str):
        abandon_controllers = cache_manager.get(cls.ABANDONED_CONTROLLERS_CACHE_KEY)
        if abandon_controllers:
            abandon_controllers.remove(device_id)
        else:
            abandon_controllers = []

        cache_manager.set(cls.ABANDONED_CONTROLLERS_CACHE_KEY, abandon_controllers, ttl_seconds=60 * 15)
