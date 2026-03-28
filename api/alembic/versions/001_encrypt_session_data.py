"""Encrypt existing plaintext session_data with Fernet.

Revision ID: 001_encrypt_session_data
Revises:
Create Date: 2026-03-19
"""

import json
import os

import sqlalchemy as sa
from cryptography.fernet import Fernet
from sqlalchemy import text

from alembic import op

revision = "001_encrypt_session_data"
down_revision = None
branch_labels = None
depends_on = None


def _get_fernet() -> Fernet:
    key = os.environ.get("CARTSNITCH_FERNET_KEY")
    if not key:
        raise RuntimeError("CARTSNITCH_FERNET_KEY must be set to run this migration")
    return Fernet(key.encode())


def _is_fernet_token(value: str) -> bool:
    """Check if a string looks like a Fernet token (base64 starting with gAAAAA)."""
    return value.startswith("gAAAAA")


def upgrade() -> None:
    # Change column type from JSON to TEXT to hold Fernet ciphertext
    op.alter_column(
        "user_store_accounts",
        "session_data",
        type_=sa.Text(),
        existing_type=sa.JSON(),
        existing_nullable=True,
        postgresql_using="session_data::text",
    )

    conn = op.get_bind()
    rows = conn.execute(
        text("SELECT id, session_data FROM user_store_accounts WHERE session_data IS NOT NULL")
    ).fetchall()

    f = _get_fernet()
    for row_id, session_data in rows:
        raw = str(session_data)
        if _is_fernet_token(raw):
            continue
        plaintext = raw if isinstance(session_data, str) else json.dumps(session_data)
        encrypted = f.encrypt(plaintext.encode()).decode()
        conn.execute(
            text("UPDATE user_store_accounts SET session_data = :data WHERE id = :id"),
            {"data": encrypted, "id": row_id},
        )


def downgrade() -> None:
    conn = op.get_bind()
    rows = conn.execute(
        text("SELECT id, session_data FROM user_store_accounts WHERE session_data IS NOT NULL")
    ).fetchall()

    f = _get_fernet()
    for row_id, session_data in rows:
        raw = str(session_data)
        if not _is_fernet_token(raw):
            continue
        decrypted = f.decrypt(raw.encode()).decode()
        conn.execute(
            text("UPDATE user_store_accounts SET session_data = :data WHERE id = :id"),
            {"data": decrypted, "id": row_id},
        )

    # Revert column type from TEXT back to JSON
    op.alter_column(
        "user_store_accounts",
        "session_data",
        type_=sa.JSON(),
        existing_type=sa.Text(),
        existing_nullable=True,
        postgresql_using="session_data::json",
    )
