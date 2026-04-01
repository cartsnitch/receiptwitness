"""Fix users.id UUID->text type mismatch for Better-Auth compatibility.

Better-Auth generates nanoid-style text IDs (e.g. pGud2ln2WAFHC0KYjBVKR4Rc7mM8OcTI),
but the users table was using PostgreSQL uuid type. When Better-Auth tries to INSERT
a new user, Postgres throws:
  ERROR: invalid input syntax for type uuid: "pGud2ln2WAFHC0KYjBVKR4Rc7mM8OcTI"

The sessions, accounts, and verifications tables already use text IDs — only users,
user_store_accounts.user_id, and purchases.user_id needed fixing.

Revision ID: 004_fix_user_id_text
Revises: 003_make_users_hashed_password_nullable
Create Date: 2026-03-31
"""

import sqlalchemy as sa
from sqlalchemy import text

from alembic import op

revision = "004_fix_user_id_text"
down_revision = "003_make_users_hashed_password_nullable"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Step 1: Drop existing FK constraints
    op.execute(text("ALTER TABLE user_store_accounts DROP CONSTRAINT IF EXISTS user_store_accounts_user_id_fkey"))
    op.execute(text("ALTER TABLE purchases DROP CONSTRAINT IF EXISTS purchases_user_id_fkey"))

    # Step 2: Alter users.id from uuid to text
    op.alter_column(
        "users",
        "id",
        type_=sa.Text(),
        existing_type=sa.UUID(),
        postgresql_using="id::text",
    )

    # Step 3: Alter user_store_accounts.user_id from uuid to text
    op.alter_column(
        "user_store_accounts",
        "user_id",
        type_=sa.Text(),
        existing_type=sa.UUID(),
        postgresql_using="user_id::text",
    )

    # Step 4: Alter purchases.user_id from uuid to text
    op.alter_column(
        "purchases",
        "user_id",
        type_=sa.Text(),
        existing_type=sa.UUID(),
        postgresql_using="user_id::text",
    )

    # Step 5: Re-add FK constraints
    op.execute(
        text(
            "ALTER TABLE user_store_accounts "
            "ADD CONSTRAINT user_store_accounts_user_id_fkey "
            "FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE"
        )
    )
    op.execute(
        text(
            "ALTER TABLE purchases "
            "ADD CONSTRAINT purchases_user_id_fkey "
            "FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE"
        )
    )


def downgrade() -> None:
    # Drop FK constraints
    op.execute(text("ALTER TABLE user_store_accounts DROP CONSTRAINT IF EXISTS user_store_accounts_user_id_fkey"))
    op.execute(text("ALTER TABLE purchases DROP CONSTRAINT IF EXISTS purchases_user_id_fkey"))

    # Revert users.id from text to uuid
    op.alter_column(
        "users",
        "id",
        type_=sa.UUID(),
        existing_type=sa.Text(),
        postgresql_using="id::uuid",
    )

    # Revert user_store_accounts.user_id from text to uuid
    op.alter_column(
        "user_store_accounts",
        "user_id",
        type_=sa.UUID(),
        existing_type=sa.Text(),
        postgresql_using="user_id::uuid",
    )

    # Revert purchases.user_id from text to uuid
    op.alter_column(
        "purchases",
        "user_id",
        type_=sa.UUID(),
        existing_type=sa.Text(),
        postgresql_using="user_id::uuid",
    )

    # Re-add FK constraints (PostgreSQL will auto-name them)
    op.execute(
        text(
            "ALTER TABLE user_store_accounts "
            "ADD CONSTRAINT user_store_accounts_user_id_fkey "
            "FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE"
        )
    )
    op.execute(
        text(
            "ALTER TABLE purchases "
            "ADD CONSTRAINT purchases_user_id_fkey "
            "FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE"
        )
    )
