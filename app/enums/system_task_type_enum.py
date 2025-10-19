from enum import Enum


class SystemTaskTypeEnum(str, Enum):
    """Enum for system task types."""
    
    SIGN_IN = "SIGN_IN"
    VERIFY_FOR_STORE_CONFIGURATION_ACCESS = "VERIFY_FOR_STORE_CONFIGURATION_ACCESS"
