"""Conftest for middleware tests — re-enables rate limiting after global disable."""

import pytest

from cartsnitch_api.config import settings as cartsnitch_settings


@pytest.fixture(autouse=True)
def enable_rate_limiting():
    """Re-enable rate limiting after the global disable_rate_limiting fixture runs.

    The root conftest disables rate limiting for all tests to prevent 429
    interference. Middleware tests need it active to verify headers and
    enforcement. This fixture runs after the root fixture (more local = later
    in setup order) so True is the effective value during the test body.
    """
    cartsnitch_settings.rate_limit_enabled = True
    yield
    cartsnitch_settings.rate_limit_enabled = False
