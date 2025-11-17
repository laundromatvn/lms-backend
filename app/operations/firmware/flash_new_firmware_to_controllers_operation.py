from uuid import UUID

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.logging import logger
from app.libs.database import with_db_session_for_class_instance
from app.libs.minio_client import MinioClient
from app.libs import mqtt
from app.models.controller import Controller
from app.models.firmware import Firmware
from app.models.firmware_deployment import FirmwareDeployment, FirmwareDeploymentStatus
from app.models.user import User
from app.enums.mqtt import MQTTEventTypeEnum
from app.utils.mqtt_payload_template import build_mqtt_payload_template


class FlashNewFirmwareToControllersOperation:
    
    CONTROLLER_ACTION_TOPIC = "lms/stores/{store_id}/controllers/{controller_id}/actions"

    def __init__(self, controller_ids: list[UUID], firmware_id: UUID):
        self.minio_client = MinioClient()

        logger.info("Starting MQTT client")
        mqtt.start()
        logger.info("MQTT client started")

        self.controller_ids = controller_ids
        self.firmware_id = firmware_id
        
    def __del__(self):
        logger.info("Stopping MQTT client")
        mqtt.stop()
        logger.info("MQTT client stopped")
        
    @with_db_session_for_class_instance
    def execute(self, db: Session, current_user_id: UUID) -> None:
        current_user = self._get_current_user(db, current_user_id)

        if not self._has_permission(current_user):
            raise PermissionError("You are not allowed to flash new firmware to controllers")
        
        firmware = self._get_firmware(db, self.firmware_id)
        if not firmware:
            raise ValueError("Firmware not found")
        
        controllers = self._get_controllers(db, self.controller_ids)
        if not controllers:
            raise ValueError("Controllers not found")
        
        existing_firmware_deployments = self._get_existing_firmware_deployment(
            db, firmware.id, [controller.id for controller in controllers],
        )
        
        for controller in controllers:
            if controller.id in existing_firmware_deployments:
                deployment = existing_firmware_deployments[controller.id]
                deployment.status = FirmwareDeploymentStatus.REBOOTING
                db.add(deployment)
            else:
                deployment = FirmwareDeployment(
                    firmware_id=firmware.id,
                    controller_id=controller.id,
                    status=FirmwareDeploymentStatus.NEW,
                )
                db.add(deployment)
                db.flush()

            self._publish_firmware_deployment(controller, firmware, deployment)
        db.commit()

    def _get_current_user(self, db: Session, current_user_id: UUID) -> User:
        return db.get(User, current_user_id)

    def _has_permission(self, current_user: User) -> bool:
        return current_user.is_admin

    def _get_firmware(self, db: Session, firmware_id: UUID) -> Firmware:
        return db.get(Firmware, firmware_id)

    def _get_controllers(self, db: Session, controller_ids: list[UUID]) -> list[Controller]:
        return (
            db.query(Controller)
            .filter(Controller.id.in_(controller_ids))
            .filter(Controller.deleted_at.is_(None))
            .all()
        )

    def _get_existing_firmware_deployment(self, db: Session, firmware_id: UUID, controller_ids: list[UUID]) -> FirmwareDeployment:
        deployments = (
            db.query(FirmwareDeployment)
            .filter(FirmwareDeployment.firmware_id == firmware_id)
            .filter(FirmwareDeployment.controller_id.in_(controller_ids))
            .all()
        )

        deployments_by_controller_id = {deployment.controller_id: deployment for deployment in deployments}
        return deployments_by_controller_id

    def _publish_firmware_deployment(
        self,
        controller: Controller,
        firmware: Firmware,
        deployment: FirmwareDeployment,
    ) -> None:
        topic = self._get_controller_action_topic(controller)
        payload = self._build_firmware_deployment_payload(controller, firmware, deployment)

        logger.info(f"Publishing firmware deployment to controller", topic=topic, payload=payload)

        mqtt.mqtt_client.publish(topic=topic, payload=payload)

    def _get_controller_action_topic(self, controller: Controller) -> str:
        return self.CONTROLLER_ACTION_TOPIC.format(
            store_id=controller.store_id,
            controller_id=controller.device_id,
        )
    
    def _build_firmware_deployment_payload(
        self,
        controller: Controller,
        firmware: Firmware,
        deployment: FirmwareDeployment,
    ) -> dict:
        file_url = self.minio_client.get_file_url(
            bucket_name=settings.BUCKET_NAME,
            object_name=firmware.object_name,
        )
        
        payload = build_mqtt_payload_template(
            event_type=MQTTEventTypeEnum.UPDATE_FIRMWARE.value,
            controller_id=str(controller.device_id),
            store_id=str(controller.store_id),
            payload={
                "deployment_id": str(deployment.id),
                "firmware_version": firmware.version,
                "file_url": file_url,
                "file_size": firmware.file_size,
                "checksum": firmware.checksum,
            },
        )

        return payload


