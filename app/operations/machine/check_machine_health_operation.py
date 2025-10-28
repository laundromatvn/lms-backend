from app.libs.database import with_db_session_classmethod
from app.models.machine import Machine


class CheckMachineHealthOperation:
    def __init__(self, machine_id: str):
        self.machine_id = machine_id

    def execute(self):
        pass
