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
    DOWNLOAD_FIRMWARE = "download_firmware"
    DOWNLOAD_FIRMWARE_ACK = "download_firmware_ack"
    FLASHING_FIRMWARE = "flashing_firmware"
    FLASHING_FIRMWARE_ACK = "flashing_firmware_ack"
    FLASHED_FIRMWARE = "flashed_firmware"
    FLASHED_FIRMWARE_ACK = "flashed_firmware_ack"
    FAILED_TO_FLASH_FIRMWARE = "failed_to_flash_firmware"
    FAILED_TO_FLASH_FIRMWARE_ACK = "failed_to_flash_firmware_ack"
