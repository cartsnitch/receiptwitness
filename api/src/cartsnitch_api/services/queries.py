"""Shared query helpers for service layer."""

from uuid import UUID

from sqlalchemy import func, select


def latest_price_per_store(product_ids: list[UUID] | None = None):
    """Subquery returning the latest observed_date per product+store.

    Optionally filtered to a list of product IDs. Returns a subquery with
    columns: normalized_product_id, store_id, max_date.
    """
    from cartsnitch_api.models import PriceHistory

    query = select(
        PriceHistory.normalized_product_id,
        PriceHistory.store_id,
        func.max(PriceHistory.observed_date).label("max_date"),
    ).group_by(PriceHistory.normalized_product_id, PriceHistory.store_id)
    if product_ids is not None:
        query = query.where(PriceHistory.normalized_product_id.in_(product_ids))
    return query.subquery()
