from enum import Enum


class SystemTaskTypeEnum(str, Enum):
    """Enum for system task types."""
    
    SIGN_IN = "SIGN_IN"
    AUTHORIZE_STORE_CONFIGURATION_ACCESS = "AUTHORIZE_STORE_CONFIGURATION_ACCESS"
