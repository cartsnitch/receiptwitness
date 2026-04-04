"""Add server_default to users.email_inbound_token.

Revision ID: 006_email_inbound_token_server_default
Revises: 005_add_email_inbound_token
Create Date: 2026-04-04
"""

import sqlalchemy as sa
from alembic import op

revision = "006_email_inbound_token_server_default"
down_revision = "005_add_email_inbound_token"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        "users",
        "email_inbound_token",
        server_default=sa.text(
            "replace(replace(trim(trailing '=' from encode(gen_random_bytes(16), 'base64')), '+', '-'), '/', '_')"
        ),
    )


def downgrade() -> None:
    op.alter_column(
        "users",
        "email_inbound_token",
        server_default=None,
    )
