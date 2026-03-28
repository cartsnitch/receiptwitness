"""Service-specific configuration for ReceiptWitness."""

from pydantic_settings import BaseSettings


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


settings = ReceiptWitnessSettings()
