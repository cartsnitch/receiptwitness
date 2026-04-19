"""Tests for email notifications."""

from unittest.mock import patch

import pytest


class TestSendReceiptNotification:
    @pytest.fixture
    def mock_resend(self):
        with patch("receiptwitness.notifications.email.resend") as mock:
            yield mock

    @pytest.mark.asyncio
    async def test_sends_email_with_correct_params(self, mock_resend):
        from receiptwitness.notifications.email import send_receipt_notification

        with (
            patch("receiptwitness.notifications.email.settings") as mock_settings,
            patch(
                "receiptwitness.notifications.email.asyncio.to_thread",
                new=lambda fn, *args, **kwargs: fn(*args, **kwargs),
            ),
        ):
            mock_settings.notifications_enabled = True
            mock_settings.resend_api_key = "re_testkey_123"
            mock_settings.notification_email_from = "noreply@test.com"

            await send_receipt_notification(
                user_email="user@example.com",
                store_name="Meijer",
                item_count=5,
                total=42.99,
                purchase_date="2026-03-28",
            )

        mock_resend.Emails.send.assert_called_once_with(
            {
                "from": "noreply@test.com",
                "to": ["user@example.com"],
                "subject": "Receipt processed: Meijer - $42.99",
                "html": (
                    "<p>Your receipt from <strong>Meijer</strong> on "
                    "2026-03-28 has been processed.</p>"
                    "<p>5 items, total: $42.99</p>"
                ),
            }
        )

    @pytest.mark.asyncio
    async def test_skips_when_disabled(self, mock_resend):
        from receiptwitness.notifications.email import send_receipt_notification

        with patch("receiptwitness.notifications.email.settings") as mock_settings:
            mock_settings.notifications_enabled = False
            mock_settings.resend_api_key = "re_testkey_123"

            await send_receipt_notification(
                user_email="user@example.com",
                store_name="Meijer",
                item_count=5,
                total=42.99,
                purchase_date="2026-03-28",
            )

        mock_resend.Emails.send.assert_not_called()

    @pytest.mark.asyncio
    async def test_skips_when_api_key_empty(self, mock_resend):
        from receiptwitness.notifications.email import send_receipt_notification

        with patch("receiptwitness.notifications.email.settings") as mock_settings:
            mock_settings.notifications_enabled = True
            mock_settings.resend_api_key = ""

            await send_receipt_notification(
                user_email="user@example.com",
                store_name="Meijer",
                item_count=5,
                total=42.99,
                purchase_date="2026-03-28",
            )

        mock_resend.Emails.send.assert_not_called()
