import base64

from pydantic import model_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_config = {"env_prefix": "CARTSNITCH_"}

    database_url: str = "postgresql+asyncpg://cartsnitch:cartsnitch@localhost:5432/cartsnitch"
    redis_url: str = "redis://localhost:6379/0"

    jwt_secret_key: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 15
    jwt_refresh_token_expire_days: int = 7

    service_key: str = "change-me-in-production"
    # Valid Fernet key for local dev — MUST be overridden in production
    fernet_key: str = "7reF42nmTwbdN21PBoubGp7h_FU8qSimstmlaMLoRK8="

    cors_origins: list[str] = ["http://localhost:3000", "https://cartsnitch.com"]

    receiptwitness_url: str = "http://receiptwitness:8001"
    stickershock_url: str = "http://stickershock:8002"
    clipartist_url: str = "http://clipartist:8003"
    shrinkray_url: str = "http://shrinkray:8004"

    rate_limit_requests: int = 60
    rate_limit_window_seconds: int = 60
    rate_limit_enabled: bool = True

    @model_validator(mode="after")
    def validate_fernet_key(self):
        """Validate fernet_key is a valid 32-byte url-safe base64 key at startup."""
        try:
            decoded = base64.urlsafe_b64decode(self.fernet_key.encode())
            if len(decoded) != 32:
                raise ValueError
        except Exception:
            raise ValueError(
                "CARTSNITCH_FERNET_KEY must be a valid Fernet key "
                "(32 bytes, url-safe base64 encoded). "
                "Generate one with: python -c "
                "'from cryptography.fernet import Fernet; "
                "print(Fernet.generate_key().decode())'"
            ) from None
        return self


settings = Settings()
