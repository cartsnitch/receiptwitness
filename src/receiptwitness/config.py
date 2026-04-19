"""Service-specific configuration for ReceiptWitness."""

from pydantic import model_validator
from pydantic_settings import BaseSettings


_PLACEHOLDER_VALUES = {"change-me-in-production"}


class ReceiptWitnessSettings(BaseSettings):
    model_config = {"env_prefix": "RW_"}

    # Inherited from cartsnitch-common
    database_url: str = "postgresql+asyncpg://cartsnitch:cartsnitch@localhost:5432/cartsnitch"
    redis_url: str = "redis://localhost:6379/0"

    # Session encryption
    session_encryption_key: str = ""

    # Scraping defaults
    scrape_interval_seconds: int = 86400  # 24 hours
    min_request_delay_ms: int = 1000
    max_request_delay_ms: int = 5000

    # Playwright
    headless: bool = True
    browser_timeout_ms: int = 60000

    # Email notifications (Resend)
    resend_api_key: str = ""
    notification_email_from: str = "notifications@cartsnitch.com"
    notifications_enabled: bool = False

    # Mailgun inbound email webhook
    mailgun_webhook_signing_key: str = ""

    @model_validator(mode="after")
    def validate_required_vars(self):
        errors = []
        if not self.session_encryption_key or self.session_encryption_key in _PLACEHOLDER_VALUES:
            errors.append(
                "RW_SESSION_ENCRYPTION_KEY must be set to a secure value. "
                'Generate one with: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"'
            )
        if self.notifications_enabled and not self.resend_api_key:
            errors.append(
                "RW_RESEND_API_KEY must be set when RW_NOTIFICATIONS_ENABLED=true. "
                "Get an API key from https://resend.com/api-keys"
            )
        if errors:
            raise ValueError(
                "ReceiptWitness startup failed — missing required config:\n"
                + "\n".join(f"  - {e}" for e in errors)
            )
        return self


class _LazySettings:
    _instance: ReceiptWitnessSettings | None = None

    def __getattr__(self, name: str):
        if _LazySettings._instance is None:
            _LazySettings._instance = ReceiptWitnessSettings()
        return getattr(_LazySettings._instance, name)


settings = _LazySettings()
