from uuid import UUID

from sqlalchemy.orm import Session

from app.core.logging import logger
from app.libs.database import with_db_session_for_class_instance
from app.libs import mqtt
from app.models.controller import Controller
from app.models.firmware_deployment import FirmwareDeployment
from app.enums.mqtt import MQTTEventTypeEnum
from app.models.user import User
from app.utils.mqtt_payload_template import build_mqtt_payload_template


class CancelUpdateFirmwareOperation:
    
    CONTROLLER_ACTION_TOPIC = "lms/stores/{store_id}/controllers/{controller_id}/actions"

    def __init__(self, current_user:User, deployment_id: UUID):
        logger.info("Starting MQTT client")
        mqtt.start()
        logger.info("MQTT client started")

        self.deployment_id = deployment_id
        self.current_user = current_user
        
    def __del__(self):
        logger.info("Stopping MQTT client")
        mqtt.stop()
        logger.info("MQTT client stopped")
        
    @with_db_session_for_class_instance
    def execute(self, db: Session) -> None:
        if not self._has_permission(self.current_user):
            raise PermissionError("You are not allowed to cancel update firmware")
        
        deployment = db.get(FirmwareDeployment, self.deployment_id)
        if not deployment:
            raise ValueError("Deployment not found")

        controller = deployment.controller
        if not controller:
            raise ValueError("Controller not found")

        self._publish(controller, deployment)

    def _has_permission(self, current_user: User) -> bool:
        return current_user.is_admin

    def _publish(
        self,
        controller: Controller,
        deployment: FirmwareDeployment,
    ) -> None:
        topic = self._get_topic(controller)
        payload = self._build_payload(controller, deployment)

        logger.info(f"Publishing cancel update firmware to controller", topic=topic, payload=payload)

        mqtt.mqtt_client.publish(topic=topic, payload=payload)

    def _get_topic(self, controller: Controller) -> str:
        return self.CONTROLLER_ACTION_TOPIC.format(
            store_id=controller.store_id,
            controller_id=controller.id,
        )
    
    def _build_payload(
        self,
        controller: Controller,
        deployment: FirmwareDeployment,
    ) -> dict:
        payload = build_mqtt_payload_template(
            event_type=MQTTEventTypeEnum.CANCEL_UPDATE_FIRMWARE.value,
            controller_id=str(controller.id),
            store_id=str(controller.store_id),
            payload={
                "deployment_id": str(deployment.id),
            },
        )

        return payload


