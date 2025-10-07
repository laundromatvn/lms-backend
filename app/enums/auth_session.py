from enum import Enum


class AuthSessionStatusEnum(Enum):
    NEW = "new"
    IN_PROGRESS = "in_progress"
    SUCCESS = "success"
    FAILED = "failed"
