from app.subcribers.machine_ack_subscriber import MachineAckSubscriber
from app.subcribers.machine_action_subscriber import MachineActionSubscriber
from app.subcribers.machine_metric_subscriber import MachineMetricSubscriber
from app.subcribers.register_controller_subcriber import RegisterControllerSubcriber


ON_STARTUP_SUBSCRIBERS = [
    MachineAckSubscriber,
    RegisterControllerSubcriber,
    MachineActionSubscriber,
    MachineMetricSubscriber,
]

__all__ = [
    "ON_STARTUP_SUBSCRIBERS",
]
