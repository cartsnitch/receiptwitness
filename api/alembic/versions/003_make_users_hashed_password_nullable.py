"""Make users.hashed_password nullable.

Better-Auth inserts users without hashed_password (passwords live in the
accounts table). This column is now purely optional.

Revision ID: 003_make_users_hashed_password_nullable
Revises: 002_better_auth_tables
Create Date: 2026-03-30
"""

import sqlalchemy as sa

from alembic import op

revision = "003_make_users_hashed_password_nullable"
down_revision = "002_better_auth_tables"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column("users", "hashed_password", existing_type=sa.String(255), nullable=True)


def downgrade() -> None:
    op.alter_column("users", "hashed_password", existing_type=sa.String(255), nullable=False)
