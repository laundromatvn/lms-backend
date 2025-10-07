import random
import os
from datetime import datetime, timedelta
from string import Template
from sqlalchemy.orm import Session
from sqlalchemy.exc import NoResultFound

from app.core.config import settings
from app.core.logging import logger
from app.libs.database import with_db_session_classmethod
from app.libs.cache import set_cache, get_cache, delete_cache
from app.models.user import User
from app.services.mail_service import MailService


class SendOTPOperation:
    
    TEMPLATE_PATH: str = os.path.join(settings.TEMPLATE_DIR, "send_otp.html")

    @classmethod
    @with_db_session_classmethod
    async def execute(cls, db: Session, email: str) -> None:
        to = [email]
        otp = str(random.randint(100000, 999999))
        subject = "OTP Verification"
        content = cls._render_template(otp)
        
        logger.info(f"Sending OTP to {email} with OTP {otp}")

        mail_service = MailService()
        await mail_service.send_html_email(
            sender_email=settings.SMTP_USERNAME,
            sender_name="LMS System",
            recipients=to,
            subject=subject,
            body=content,
            attachments=[],
        )

    @classmethod
    def _render_template(cls, otp: str) -> str:
        template_path = cls.TEMPLATE_PATH

        with open(template_path, "r", encoding="utf-8") as file:
            template_content = file.read()

        template = Template(template_content)

        variables = {
            "otp_code": otp,
            "expiry_minutes": 10,
        }

        return template.substitute(**variables)
