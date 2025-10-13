import asyncio

from app.core.celery_app import celery_app
from app.core.logging import logger

from app.operations.auth.send_otp_operation import SendOTPOperation


@celery_app.task(name="app.tasks.auth.send_otp_task")
def send_otp_task(email: str):
    logger.info(f"Sending OTP to {email}")
    loop = asyncio.get_event_loop()
    loop.run_until_complete(SendOTPOperation.execute(email))
    logger.info(f"OTP sent to {email}")


