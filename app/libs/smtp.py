from typing import List, Optional, Dict, Any

import smtplib
from email.utils import formataddr
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication

from app.core.config import settings
from app.core.logging import logger


class SMTPClient:

    def __init__(self):
        self.server = settings.SMTP_SERVER
        self.port = settings.SMTP_PORT
        self.username = settings.SMTP_USERNAME
        self.password = settings.SMTP_PASSWORD
        self.client = self._get_client()

    def _get_client(self) -> smtplib.SMTP:
        self.client = smtplib.SMTP(self.server, self.port)
        self.client.starttls()
        self.client.login(self.username, self._clean_password())
        return self.client
    
    def _clean_password(self) -> str:
        return self.password.replace("_", " ")

    async def send_email(
        self,
        sender_email: str,
        sender_name: str,
        recipients: List[str],
        subject: str,
        body: str,
        attachments: Optional[List[Dict[str, Any]]] = None,
    ) -> None:
        return await self._send_email(
            sender_email,
            sender_name,
            recipients,
            subject,
            body,
            attachments,
            False,
        )

    async def send_html_email(
        self, 
        sender_email: str,
        sender_name: str,
        recipients: List[str],
        subject: str,
        body: str,
        attachments: Optional[List[Dict[str, Any]]] = None,
    ) -> None:
        return await self._send_email(
            sender_email,
            sender_name,
            recipients,
            subject,
            body,
            attachments,
            True,
        )

    async def _send_email(
        self,
        sender_email: str,
        sender_name: str,
        recipients: List[str],
        subject: str,
        body: str,
        attachments: Optional[List[Dict[str, Any]]] = None,
        is_html: bool = False,
    ) -> None:
        # Create MIME message
        msg = MIMEMultipart()
        msg["From"] = formataddr((sender_name, sender_email))
        msg["To"] = ", ".join(recipients)
        msg["Subject"] = subject

        # Attach body
        msg.attach(MIMEText(body, "html" if is_html else "plain"))

        # Attach files if any
        if attachments:
            for attachment in attachments:
                file_path = attachment["file_path"]
                file_name = attachment["file_name"]
                try:
                    with open(file_path, "rb") as f:
                        part = MIMEApplication(f.read(), Name=file_name)
                    part["Content-Disposition"] = f'attachment; filename="{file_name}"'
                    msg.attach(part)
                except Exception as e:
                    raise ValueError(f"Failed to attach {file_path}: {e}")

        # Send email
        self.client.send_message(msg)
