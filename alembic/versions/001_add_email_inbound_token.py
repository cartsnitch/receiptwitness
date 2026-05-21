"""Add email_inbound_token to users.

Revision ID: 001_add_email_inbound_token
Revises:
Create Date: 2026-04-02
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "001_add_email_inbound_token"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("users", sa.Column("email_inbound_token", sa.String(22), nullable=True))
    op.create_unique_constraint("uq_users_email_inbound_token", "users", ["email_inbound_token"])

    # Backfill existing users with generated tokens (PostgreSQL)
    op.execute(
        "UPDATE users SET email_inbound_token = "
        "substring(replace(gen_random_uuid()::text, '-', ''), 1, 22) "
        "WHERE email_inbound_token IS NULL"
    )

    # Alter to non-nullable
    op.alter_column("users", "email_inbound_token", nullable=False)


def downgrade() -> None:
    op.drop_constraint("uq_users_email_inbound_token", "users", type_="unique")
    op.drop_column("users", "email_inbound_token")