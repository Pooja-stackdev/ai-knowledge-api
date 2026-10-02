"""SMTP email provider abstraction."""

import smtplib
from abc import ABC, abstractmethod
from email.message import EmailMessage

from app.core.config import settings


class EmailProvider(ABC):
    """Infrastructure boundary for outbound email providers."""

    @abstractmethod
    def send(self, message: EmailMessage) -> None:
        """Hand an already-rendered message to the provider."""


class SmtpEmailProvider(EmailProvider):
    """SMTP implementation configured exclusively through environment settings."""

    def send(self, message: EmailMessage) -> None:
        """Send a message using TLS and optional SMTP authentication."""
        if not settings.smtp_enabled:
            raise RuntimeError("SMTP delivery is disabled.")
        if not settings.smtp_host:
            raise RuntimeError("SMTP host is not configured.")

        with smtplib.SMTP(
            host=settings.smtp_host,
            port=settings.smtp_port,
            timeout=settings.smtp_timeout_seconds,
        ) as client:
            client.ehlo()
            if settings.smtp_use_tls:
                client.starttls()
                client.ehlo()
            if settings.smtp_username and settings.smtp_password:
                client.login(settings.smtp_username, settings.smtp_password)
            client.send_message(message)
