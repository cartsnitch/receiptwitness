"""Add email_inbound_token to users.

Revision ID: 005_add_email_inbound_token
Revises: 004_fix_user_id_text
Create Date: 2026-04-02
"""

import secrets

import sqlalchemy as sa

from alembic import op

revision = "005_add_email_inbound_token"
down_revision = "004_fix_user_id_text"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add column nullable first so existing rows can be backfilled
    op.add_column(
        "users",
        sa.Column("email_inbound_token", sa.String(22), nullable=True),
    )

    # Backfill existing users with unique tokens
    connection = op.get_bind()
    result = connection.execute(sa.text("SELECT id FROM users WHERE email_inbound_token IS NULL"))
    for (user_id,) in result:
        token = secrets.token_urlsafe(16)
        connection.execute(
            sa.text("UPDATE users SET email_inbound_token = :token WHERE id = :id"),
            {"token": token, "id": user_id},
        )

    # Now enforce non-null and unique
    op.alter_column("users", "email_inbound_token", nullable=False)
    op.create_index(
        "ix_users_email_inbound_token",
        "users",
        ["email_inbound_token"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("ix_users_email_inbound_token", table_name="users")
    op.drop_column("users", "email_inbound_token")
