from enum import Enum


class MQTTEventTypeEnum(str, Enum):
    # Assignment
    CONTROLLER_INIT_REQUEST = "controller_init_request"
    CONTROLLER_INIT_RESPONSE = "controller_init_response"
    CONTROLLER_VERIFICATION = "controller_verification"
    STORE_ASSIGNMENT = "store_assignment"

    # Machine
    MACHINE_START = "start"
    MACHINE_START_ACK = "start_ack"
    MACHINE_FINISH = "finish"
    MACHINE_FINISH_ACK = "finish_ack"
    MACHINE_STATE = "machine_state"
