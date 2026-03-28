"""Shared test fixtures."""

import json
from pathlib import Path

import pytest

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def meijer_receipt_data() -> dict:
    """Load the sample Meijer receipt fixture."""
    with open(FIXTURES_DIR / "meijer_receipt.json") as f:
        return json.load(f)


@pytest.fixture
def kroger_receipt_data() -> dict:
    """Load the sample Kroger receipt fixture."""
    with open(FIXTURES_DIR / "kroger_receipt.json") as f:
        return json.load(f)


@pytest.fixture
def target_receipt_data() -> dict:
    """Load the sample Target receipt fixture."""
    with open(FIXTURES_DIR / "target_receipt.json") as f:
        return json.load(f)
