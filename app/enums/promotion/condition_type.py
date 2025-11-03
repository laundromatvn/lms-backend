from enum import Enum


class ConditionType(Enum):
    # Object conditions
    TENANTS = "TENANTS"
    STORES = "STORES"
    USERS = "USERS"
    
    # Amount conditions
    TOTAL_AMOUNT = "TOTAL_AMOUNT"
    AMOUNT_PER_USER = "AMOUNT_PER_USER"
    AMOUNT_PER_STORE = "AMOUNT_PER_STORE"
    AMOUNT_PER_TENANT = "AMOUNT_PER_TENANT"
