"""Add GIN index on upc_variants and alter column to JSONB.

Revision ID: 009_add_gin_index_upc_variants
Revises: 008_create_domain_tables
Create Date: 2026-04-14
"""

import sqlalchemy as sa
from alembic import op

revision = "009_add_gin_index_upc_variants"
down_revision = "008_create_domain_tables"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        "normalized_products",
        "upc_variants",
        type_=sa.dialects.postgresql.JSONB(),
        postgresql_using="upc_variants::jsonb",
    )
    op.create_index(
        "ix_normalized_products_upc_variants_gin",
        "normalized_products",
        ["upc_variants"],
        postgresql_using="gin",
    )


def downgrade() -> None:
    op.drop_index("ix_normalized_products_upc_variants_gin", table_name="normalized_products")
    op.alter_column(
        "normalized_products",
        "upc_variants",
        type_=sa.JSON(),
    )
