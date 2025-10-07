from enum import Enum
from typing import List, Dict, Any, Optional

from app.libs.smtp import SMTPClient


class MailClientTypeEnum(str, Enum):
    SMTP = "smtp"   


class MailService:
    def __init__(self, client_type: MailClientTypeEnum = MailClientTypeEnum.SMTP):
        self.client_type = client_type
        self.client = self._get_client(client_type)

    def _get_client(self, client_type: MailClientTypeEnum):
        if client_type == MailClientTypeEnum.SMTP:
            return SMTPClient()
        else:
            raise ValueError(f"Client type {client_type} not found")

    async def send_email(
        self,
        sender_email: str,
        sender_name: str,
        recipients: List[str],
        subject: str,
        body: str,
        attachments: Optional[List[Dict[str, Any]]] = None,
    ) -> None:
        return await self.client.send_email(
            sender_email,
            sender_name,
            recipients,
            subject,
            body,
            attachments,
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
        return await self.client.send_html_email(
            sender_email,
            sender_name,
            recipients,
            subject,
            body,
            attachments,
        )
