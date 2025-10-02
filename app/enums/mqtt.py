from enum import Enum


class MQTTEventTypeEnum(str, Enum):
    # Assignment
    CONTROLLER_INIT_REQUEST = "controller_init_request"
    CONTROLLER_VERIFICATION = "controller_verification"
    STORE_ASSIGNMENT = "store_assignment"
