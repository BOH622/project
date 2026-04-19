"""Application settings loaded from environment."""
from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # DB
    database_url: str = Field(..., alias="DATABASE_URL")
    test_database_url: str | None = Field(default=None, alias="TEST_DATABASE_URL")

    # HTTP
    portal_base_url: str = Field(default="http://localhost:5173", alias="PORTAL_BASE_URL")
    backend_base_url: str = Field(default="http://localhost:8000", alias="BACKEND_BASE_URL")
    cors_allowed_origins: str = Field(
        default="http://localhost:5173", alias="CORS_ALLOWED_ORIGINS"
    )

    # Auth
    auth_signing_key: str = Field(..., alias="AUTH_SIGNING_KEY")
    magic_link_ttl_seconds: int = Field(default=900, alias="MAGIC_LINK_TTL_SECONDS")

    # Email
    email_sender: str = Field(
        default="noreply@projects.tryusercue.com", alias="EMAIL_SENDER"
    )
    email_backend: str = Field(default="console", alias="EMAIL_BACKEND")  # console | ses

    # AWS
    aws_region: str = Field(default="us-east-1", alias="AWS_REGION")
    s3_attachments_bucket: str = Field(
        default="usercue-portal-attachments-dev", alias="S3_ATTACHMENTS_BUCKET"
    )

    # Inbound email
    inbound_email_domain: str = Field(
        default="threads.projects.tryusercue.com", alias="INBOUND_EMAIL_DOMAIN"
    )
    inbound_email_hmac_secret: str = Field(..., alias="INBOUND_EMAIL_HMAC_SECRET")

    # Webhook signing
    webhook_hmac_secret: str = Field(..., alias="WEBHOOK_HMAC_SECRET")

    # Super-admin
    super_admin_emails: str = Field(default="", alias="SUPER_ADMIN_EMAILS")

    @property
    def cors_origins(self) -> list[str]:
        return [o.strip() for o in self.cors_allowed_origins.split(",") if o.strip()]

    @property
    def super_admins(self) -> set[str]:
        return {e.strip().lower() for e in self.super_admin_emails.split(",") if e.strip()}


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]


settings = get_settings()
