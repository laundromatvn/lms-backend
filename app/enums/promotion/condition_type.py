from enum import Enum


class ConditionType(Enum):
    # Object conditions
    TENANTS = "TENANTS"
    STORES = "STORES"

    # Amount conditions
    TOTAL_AMOUNT = "TOTAL_AMOUNT"
    
    # Machine conditions
    MACHINE_TYPES = "MACHINE_TYPES"
    
    # Time range conditions
    TIME_IN_DAY = "TIME_IN_DAY"

class ConditionValueType(Enum):
    STRING = "STRING"
    NUMBER = "NUMBER"
    BOOLEAN = "BOOLEAN"
    OPTIONS = "OPTIONS"
    TIME_IN_DAY = "TIME_IN_DAY"
