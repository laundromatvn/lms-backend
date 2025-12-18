from app.tasks.health_check import health_check

from app.tasks.payment.payment_tasks import (
    generate_payment_details,
    sync_payment_transaction,
)
from app.tasks.payment.sync_up_timeout_payments_task import sync_up_timeout_payments_task

from app.tasks.auth.send_otp_task import send_otp_task

from app.tasks.order.sync_up_in_progress_orders_task import sync_up_in_progress_orders_task

from app.tasks.promotion.sync_up_promotion_campaign_task import sync_up_promotion_campaign_task

from app.tasks.firmware.flash_new_firmware_to_controllers_task import flash_new_firmware_to_controllers_task
from app.tasks.firmware.handle_cancel_update_firmware_ack_task import handle_cancel_update_firmware_ack_task
from app.tasks.firmware.handle_update_firmware_ack_task import handle_update_firmware_ack_task
from app.tasks.firmware.handle_update_firmware_completed_task import handle_update_firmware_completed_task
from app.tasks.firmware.handle_update_firmware_failed_task import handle_update_firmware_failed_task

from app.tasks.permissions.add_foundation_permissions_task import add_foundation_permissions_task

from app.tasks.machine.reset_no_responding_machines_task import reset_no_responding_machines_task


__all__ = [
    # Health check
    "health_check",

    # Payment tasks
    "generate_payment_details",
    "sync_payment_transaction",
    "sync_up_timeout_payments_task",

    # Auth tasks
    "send_otp_task",

    # Order tasks
    "sync_up_in_progress_orders_task",

    # Promotion tasks
    "sync_up_promotion_campaign_task",
    
    # Firmware tasks
    "flash_new_firmware_to_controllers_task",
    "handle_cancel_update_firmware_ack_task",
    "handle_update_firmware_ack_task",
    "handle_update_firmware_completed_task",
    "handle_update_firmware_failed_task",
    
    # Permission tasks
    "add_foundation_permissions_task",
    
    # Machine tasks
    "reset_no_responding_machines_task",
]

