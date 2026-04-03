"""Detect which retailer sent a receipt email."""

import re

from receiptwitness.parsers.email.base import EmailReceipt

RETAILER_PATTERNS: dict[str, list[str]] = {
    "meijer": [r"@meijer\.com$", r"@email\.meijer\.com$"],
    "kroger": [r"@kroger\.com$", r"@email\.kroger\.com$"],
    "target": [r"@target\.com$", r"@email\.target\.com$"],
}


def detect_retailer(email: EmailReceipt) -> str | None:
    """Return retailer slug or None if unrecognized."""
    sender = email.sender.lower().strip()
    # Extract email from "Name <email>" format
    match = re.search(r"<([^>]+)>", sender)
    if match:
        sender = match.group(1)
    for retailer, patterns in RETAILER_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, sender):
                return retailer
    return None
