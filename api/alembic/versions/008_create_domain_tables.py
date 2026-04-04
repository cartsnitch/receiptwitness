"""Create domain tables (stores, purchases, coupons, etc.).

Revision ID: 008_create_domain_tables
Revises: 007_bootstrap_users_table
Create Date: 2026-04-04
"""

import sqlalchemy as sa
from sqlalchemy import text

from alembic import op

revision = "008_create_domain_tables"
down_revision = "007_bootstrap_users_table"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    # 1. stores
    if not inspector.has_table("stores"):
        op.create_table(
            "stores",
            sa.Column("id", sa.Uuid(), server_default=text("gen_random_uuid()"), primary_key=True),
            sa.Column("name", sa.String(100), nullable=False),
            sa.Column("slug", sa.String(20), nullable=False, unique=True),
            sa.Column("logo_url", sa.String(500), nullable=True),
            sa.Column("website_url", sa.String(500), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        )

    # 2. store_locations
    if not inspector.has_table("store_locations"):
        op.create_table(
            "store_locations",
            sa.Column("id", sa.Uuid(), server_default=text("gen_random_uuid()"), primary_key=True),
            sa.Column("store_id", sa.Uuid(), sa.ForeignKey("stores.id"), nullable=False),
            sa.Column("address", sa.String(300), nullable=False),
            sa.Column("city", sa.String(100), nullable=False),
            sa.Column("state", sa.String(2), nullable=False),
            sa.Column("zip", sa.String(10), nullable=False),
            sa.Column("lat", sa.Float(), nullable=True),
            sa.Column("lng", sa.Float(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        )

    # 3. normalized_products
    if not inspector.has_table("normalized_products"):
        op.create_table(
            "normalized_products",
            sa.Column("id", sa.Uuid(), server_default=text("gen_random_uuid()"), primary_key=True),
            sa.Column("canonical_name", sa.String(300), nullable=False),
            sa.Column("category", sa.String(50), nullable=True),
            sa.Column("subcategory", sa.String(100), nullable=True),
            sa.Column("brand", sa.String(200), nullable=True),
            sa.Column("size", sa.String(50), nullable=True),
            sa.Column("size_unit", sa.String(10), nullable=True),
            sa.Column("upc_variants", sa.JSON(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        )

    # 4. purchases
    if not inspector.has_table("purchases"):
        op.create_table(
            "purchases",
            sa.Column("id", sa.Uuid(), server_default=text("gen_random_uuid()"), primary_key=True),
            sa.Column("user_id", sa.Text(), sa.ForeignKey("users.id"), nullable=False),
            sa.Column("store_id", sa.Uuid(), sa.ForeignKey("stores.id"), nullable=False),
            sa.Column("store_location_id", sa.Uuid(), sa.ForeignKey("store_locations.id"), nullable=True),
            sa.Column("receipt_id", sa.String(200), nullable=False),
            sa.Column("purchase_date", sa.Date(), nullable=False),
            sa.Column("total", sa.Numeric(10, 2), nullable=False),
            sa.Column("subtotal", sa.Numeric(10, 2), nullable=True),
            sa.Column("tax", sa.Numeric(10, 2), nullable=True),
            sa.Column("savings_total", sa.Numeric(10, 2), nullable=True),
            sa.Column("source_url", sa.String(500), nullable=True),
            sa.Column("raw_data", sa.JSON(), nullable=True),
            sa.Column("ingested_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.UniqueConstraint("user_id", "store_id", "receipt_id", name="uq_purchase_receipt"),
            sa.Index("ix_purchases_user_store", "user_id", "store_id"),
        )

    # 5. purchase_items
    if not inspector.has_table("purchase_items"):
        op.create_table(
            "purchase_items",
            sa.Column("id", sa.Uuid(), server_default=text("gen_random_uuid()"), primary_key=True),
            sa.Column("purchase_id", sa.Uuid(), sa.ForeignKey("purchases.id"), nullable=False),
            sa.Column("product_name_raw", sa.String(300), nullable=False),
            sa.Column("upc", sa.String(20), nullable=True),
            sa.Column("quantity", sa.Numeric(10, 3), nullable=False),
            sa.Column("unit_price", sa.Numeric(10, 2), nullable=False),
            sa.Column("extended_price", sa.Numeric(10, 2), nullable=False),
            sa.Column("regular_price", sa.Numeric(10, 2), nullable=True),
            sa.Column("sale_price", sa.Numeric(10, 2), nullable=True),
            sa.Column("coupon_discount", sa.Numeric(10, 2), nullable=True),
            sa.Column("loyalty_discount", sa.Numeric(10, 2), nullable=True),
            sa.Column("category_raw", sa.String(100), nullable=True),
            sa.Column("normalized_product_id", sa.Uuid(), sa.ForeignKey("normalized_products.id"), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        )

    # 6. coupons
    if not inspector.has_table("coupons"):
        op.create_table(
            "coupons",
            sa.Column("id", sa.Uuid(), server_default=text("gen_random_uuid()"), primary_key=True),
            sa.Column("store_id", sa.Uuid(), sa.ForeignKey("stores.id"), nullable=False),
            sa.Column("normalized_product_id", sa.Uuid(), sa.ForeignKey("normalized_products.id"), nullable=True),
            sa.Column("title", sa.String(300), nullable=False),
            sa.Column("description", sa.String(1000), nullable=True),
            sa.Column("discount_type", sa.String(20), nullable=False),
            sa.Column("discount_value", sa.Numeric(10, 2), nullable=True),
            sa.Column("min_purchase", sa.Numeric(10, 2), nullable=True),
            sa.Column("valid_from", sa.Date(), nullable=True),
            sa.Column("valid_to", sa.Date(), nullable=True),
            sa.Column("requires_clip", sa.Boolean(), server_default=text("false"), nullable=False),
            sa.Column("coupon_code", sa.String(100), nullable=True),
            sa.Column("source_url", sa.String(500), nullable=True),
            sa.Column("scraped_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        )

    # 7. price_history
    if not inspector.has_table("price_history"):
        op.create_table(
            "price_history",
            sa.Column("id", sa.Uuid(), server_default=text("gen_random_uuid()"), primary_key=True),
            sa.Column("normalized_product_id", sa.Uuid(), sa.ForeignKey("normalized_products.id"), nullable=False),
            sa.Column("store_id", sa.Uuid(), sa.ForeignKey("stores.id"), nullable=False),
            sa.Column("observed_date", sa.Date(), nullable=False),
            sa.Column("regular_price", sa.Numeric(10, 2), nullable=False),
            sa.Column("sale_price", sa.Numeric(10, 2), nullable=True),
            sa.Column("loyalty_price", sa.Numeric(10, 2), nullable=True),
            sa.Column("coupon_price", sa.Numeric(10, 2), nullable=True),
            sa.Column("source", sa.String(20), nullable=False),
            sa.Column("purchase_item_id", sa.Uuid(), sa.ForeignKey("purchase_items.id"), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Index("ix_price_history_product_store_date", "normalized_product_id", "store_id", "observed_date"),
        )

    # 8. shrinkflation_events
    if not inspector.has_table("shrinkflation_events"):
        op.create_table(
            "shrinkflation_events",
            sa.Column("id", sa.Uuid(), server_default=text("gen_random_uuid()"), primary_key=True),
            sa.Column("normalized_product_id", sa.Uuid(), sa.ForeignKey("normalized_products.id"), nullable=False),
            sa.Column("detected_date", sa.Date(), nullable=False),
            sa.Column("old_size", sa.String(50), nullable=False),
            sa.Column("new_size", sa.String(50), nullable=False),
            sa.Column("old_unit", sa.String(10), nullable=True),
            sa.Column("new_unit", sa.String(10), nullable=True),
            sa.Column("price_at_old_size", sa.Numeric(10, 2), nullable=True),
            sa.Column("price_at_new_size", sa.Numeric(10, 2), nullable=True),
            sa.Column("confidence", sa.Numeric(3, 2), server_default=text("1.00"), nullable=False),
            sa.Column("notes", sa.String(1000), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        )

    # 9. user_store_accounts
    if not inspector.has_table("user_store_accounts"):
        op.create_table(
            "user_store_accounts",
            sa.Column("id", sa.Uuid(), server_default=text("gen_random_uuid()"), primary_key=True),
            sa.Column("user_id", sa.Text(), sa.ForeignKey("users.id"), nullable=False),
            sa.Column("store_id", sa.Uuid(), sa.ForeignKey("stores.id"), nullable=False),
            sa.Column("session_data", sa.JSON(), nullable=True),
            sa.Column("session_expires_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("last_sync_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("status", sa.String(20), server_default=text("'active'"), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.UniqueConstraint("user_id", "store_id", name="uq_user_store_account"),
        )


def downgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    if inspector.has_table("user_store_accounts"):
        op.drop_table("user_store_accounts")
    if inspector.has_table("shrinkflation_events"):
        op.drop_table("shrinkflation_events")
    if inspector.has_table("price_history"):
        op.drop_table("price_history")
    if inspector.has_table("coupons"):
        op.drop_table("coupons")
    if inspector.has_table("purchase_items"):
        op.drop_table("purchase_items")
    if inspector.has_table("purchases"):
        op.drop_table("purchases")
    if inspector.has_table("normalized_products"):
        op.drop_table("normalized_products")
    if inspector.has_table("store_locations"):
        op.drop_table("store_locations")
    if inspector.has_table("stores"):
        op.drop_table("stores")
