from app.subcribers.machine_ack_subscriber import MachineAckSubscriber
from app.subcribers.register_controller_subcriber import RegisterControllerSubcriber


ON_STARTUP_SUBSCRIBERS = [
    MachineAckSubscriber,
    RegisterControllerSubcriber,
]

__all__ = [
    "ON_STARTUP_SUBSCRIBERS",
]
