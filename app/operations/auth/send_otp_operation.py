import os
from sqlalchemy.orm import Session
from jinja2 import Template

from app.core.config import settings
from app.libs.database import with_db_session_classmethod
from app.models.user import User
from app.services.mail_service import MailService
from app.operations.auth.otp_generator import OtpGenerator

class SendOTPOperation:

    TEMPLATE_PATH: str = os.path.join(settings.TEMPLATE_DIR, "send_otp.html")

    @classmethod
    @with_db_session_classmethod
    async def execute(cls, db: Session, email: str, ttl_seconds: int = 600) -> None:
        user = await cls._get_user_by_email(db, email)
        otp = await OtpGenerator.execute(user.id, ttl_seconds)
        return await cls._send_otp_by_email(email, otp)

    @classmethod
    async def _get_user_by_email(cls, db: Session, email: str) -> User:
        user = db.query(User).filter(User.email == email).first()
        if not user:
            raise ValueError("User not found")
        return user

    @classmethod
    async def _send_otp_by_email(cls, email: str, otp: str) -> None:
        to = [email]
        subject = "OTP Verification"
        content = cls._render_template(otp)

        return await MailService().send_html_email(
            sender_email=settings.EMAIL_SENDER,
            sender_name=settings.EMAIL_SENDER_NAME,
            recipients=to,
            subject=subject,
            body=content,
            attachments=[],
        )

    @classmethod
    def _render_template(cls, otp: str) -> str:
        """
        Render the template with the OTP code and expiry minutes.
        For example:
        {
            "otp_code": "123456",
            "expiry_minutes": 10,
        }
        
        Template:
        <div class="otp-container">
            <div class="otp-label">Your Verification Code</div>
            <div class="otp-code">{{ otp_code }}</div>
            <div class="otp-expiry">Expires in {{ expiry_minutes }} minutes</div>
        </div>
        
        Return:
        <div class="otp-container">
            <div class="otp-label">Your Verification Code</div>
            <div class="otp-code">123456</div>
            <div class="otp-expiry">Expires in 10 minutes</div>
        </div>
        """
        template_path = cls.TEMPLATE_PATH

        with open(template_path, "r", encoding="utf-8") as file:
            template_content = file.read()

        template = Template(template_content)

        variables = {
            "otp_code": otp,
            "expiry_minutes": 10,
        }

        return template.render(**variables)