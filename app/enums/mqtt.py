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
    
    # Flash Firmware
    UPDATE_FIRMWARE = "update_firmware"
    UPDATE_FIRMWARE_ACK = "update_firmware_ack"
    UPDATE_FIRMWARE_FAILED = "update_firmware_failed"
    UPDATE_FIRMWARE_FAILED_ACK = "update_firmware_failed_ack"
    UPDATE_FIRMWARE_COMPLETED = "update_firmware_completed"
    UPDATE_FIRMWARE_COMPLETED_ACK = "update_firmware_completed_ack"
    CANCEL_UPDATE_FIRMWARE = "cancel_update_firmware"
    CANCEL_UPDATE_FIRMWARE_ACK = "cancel_update_firmware_ack"
