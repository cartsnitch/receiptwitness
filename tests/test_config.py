import pytest
from receiptwitness.config import ReceiptWitnessSettings


def test_valid_config():
    s = ReceiptWitnessSettings(
        session_encryption_key="7reF42nmTwbdN21PBoubGp7h_FU8qSimstmlaMLoRK8="
    )
    assert s.session_encryption_key


def test_missing_session_encryption_key_raises():
    with pytest.raises(ValueError, match="RW_SESSION_ENCRYPTION_KEY"):
        ReceiptWitnessSettings(session_encryption_key="")


def test_placeholder_session_encryption_key_raises():
    with pytest.raises(ValueError, match="RW_SESSION_ENCRYPTION_KEY"):
        ReceiptWitnessSettings(session_encryption_key="change-me-in-production")


def test_notifications_enabled_without_resend_key_raises():
    with pytest.raises(ValueError, match="RW_RESEND_API_KEY"):
        ReceiptWitnessSettings(
            session_encryption_key="7reF42nmTwbdN21PBoubGp7h_FU8qSimstmlaMLoRK8=",
            notifications_enabled=True,
            resend_api_key="",
        )


def test_notifications_disabled_without_resend_key_ok():
    s = ReceiptWitnessSettings(
        session_encryption_key="7reF42nmTwbdN21PBoubGp7h_FU8qSimstmlaMLoRK8=",
        notifications_enabled=False,
        resend_api_key="",
    )
    assert s.notifications_enabled is False


def test_notifications_enabled_with_resend_key_ok():
    s = ReceiptWitnessSettings(
        session_encryption_key="7reF42nmTwbdN21PBoubGp7h_FU8qSimstmlaMLoRK8=",
        notifications_enabled=True,
        resend_api_key="re_test_1234567890",
    )
    assert s.resend_api_key == "re_test_1234567890"
