from uuid import UUID

from sqlalchemy.orm import Session

from app.libs.database import with_db_session_for_class_instance
from app.models.firmware_deployment import FirmwareDeployment, FirmwareDeploymentStatus


class HandleUpdateFirmwareCompletedOperation:

    def __init__(self, deployment_id: UUID):
        self.deployment_id = deployment_id

    @with_db_session_for_class_instance
    def execute(self, db: Session):
        deployment = db.get(FirmwareDeployment, self.deployment_id)
        if not deployment:
            raise ValueError("Deployment not found")

        deployment.status = FirmwareDeploymentStatus.COMPLETED
        db.add(deployment)
        
        controller = deployment.controller
        if not controller:
            raise ValueError("Controller not found")

        controller.provisioned_firmware_id = deployment.firmware_id
        db.add(controller)
        db.commit()


