from enum import Enum


class OTPActionEnum(str, Enum):
    SIGN_IN = "sign_in"
    VERIFY_FOR_STORE_CONFIGURATION_ACCESS = "verify_for_store_configuration_access"
