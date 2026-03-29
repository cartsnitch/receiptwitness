"""Add Better-Auth tables and extend users table.

Creates sessions, accounts, and verifications tables for Better-Auth.
Adds email_verified and image columns to existing users table.
Migrates password hashes from users.hashed_password to accounts.password.

Revision ID: 002_better_auth_tables
Revises: 001_encrypt_session_data
Create Date: 2026-03-28
"""

import sqlalchemy as sa
from sqlalchemy import text

from alembic import op

revision = "002_better_auth_tables"
down_revision = "001_encrypt_session_data"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # --- Extend users table for Better-Auth compatibility ---
    op.add_column("users", sa.Column("email_verified", sa.Boolean(), nullable=False, server_default="false"))
    op.add_column("users", sa.Column("image", sa.Text(), nullable=True))

    # --- Create sessions table ---
    op.create_table(
        "sessions",
        sa.Column("id", sa.Text(), nullable=False),
        sa.Column("token", sa.Text(), nullable=False),
        sa.Column("user_id", sa.Text(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ip_address", sa.Text(), nullable=True),
        sa.Column("user_agent", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_sessions_token", "sessions", ["token"], unique=True)
    op.create_index("ix_sessions_user_id", "sessions", ["user_id"])

    # --- Create accounts table ---
    op.create_table(
        "accounts",
        sa.Column("id", sa.Text(), nullable=False),
        sa.Column("user_id", sa.Text(), nullable=False),
        sa.Column("account_id", sa.Text(), nullable=False),
        sa.Column("provider_id", sa.Text(), nullable=False),
        sa.Column("access_token", sa.Text(), nullable=True),
        sa.Column("refresh_token", sa.Text(), nullable=True),
        sa.Column("access_token_expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("refresh_token_expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("scope", sa.Text(), nullable=True),
        sa.Column("id_token", sa.Text(), nullable=True),
        sa.Column("password", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_accounts_user_id", "accounts", ["user_id"])

    # --- Create verifications table ---
    op.create_table(
        "verifications",
        sa.Column("id", sa.Text(), nullable=False),
        sa.Column("identifier", sa.Text(), nullable=False),
        sa.Column("value", sa.Text(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    # --- Migrate existing password hashes to accounts table ---
    # For each user with a hashed_password, create a 'credential' account row
    conn = op.get_bind()
    users = conn.execute(
        text("SELECT id, hashed_password FROM users WHERE hashed_password IS NOT NULL")
    ).fetchall()

    for user_id, hashed_password in users:
        user_id_str = str(user_id)
        conn.execute(
            text(
                "INSERT INTO accounts (id, user_id, account_id, provider_id, password, created_at, updated_at) "
                "VALUES (gen_random_uuid()::text, :user_id, :account_id, 'credential', :password, now(), now())"
            ),
            {"user_id": user_id_str, "account_id": user_id_str, "password": hashed_password},
        )


def downgrade() -> None:
    op.drop_table("verifications")
    op.drop_table("accounts")
    op.drop_index("ix_sessions_user_id", table_name="sessions")
    op.drop_index("ix_sessions_token", table_name="sessions")
    op.drop_table("sessions")
    op.drop_column("users", "image")
    op.drop_column("users", "email_verified")
