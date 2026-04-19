"""Abstract email sender + Console (dev) and SES (prod) implementations."""
from __future__ import annotations

import logging
from abc import ABC, abstractmethod

import boto3

from app.config import settings

log = logging.getLogger(__name__)


class EmailSender(ABC):
    @abstractmethod
    async def send(self, *, to: str, subject: str, html: str, text: str) -> str:
        """Send an email. Returns the provider's message id (or empty string)."""


class ConsoleSender(EmailSender):
    """Dev sender — logs to stdout. Never actually delivers mail."""

    async def send(self, *, to: str, subject: str, html: str, text: str) -> str:
        log.warning("=== EMAIL (console) ===\nTo: %s\nSubject: %s\n\n%s\n=======", to, subject, text)
        return ""


class SESSender(EmailSender):
    def __init__(self) -> None:
        self._client = boto3.client("ses", region_name=settings.aws_region)

    async def send(self, *, to: str, subject: str, html: str, text: str) -> str:
        # boto3 is sync; fine for v1. If volume grows, wrap in threadpool.
        response = self._client.send_email(
            Source=settings.email_sender,
            Destination={"ToAddresses": [to]},
            Message={
                "Subject": {"Data": subject, "Charset": "UTF-8"},
                "Body": {
                    "Html": {"Data": html, "Charset": "UTF-8"},
                    "Text": {"Data": text, "Charset": "UTF-8"},
                },
            },
        )
        return response.get("MessageId", "")


def get_sender() -> EmailSender:
    backend = settings.email_backend.lower()
    if backend == "ses":
        return SESSender()
    return ConsoleSender()
