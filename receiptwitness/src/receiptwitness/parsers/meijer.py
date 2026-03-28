"""Parse raw Meijer mPerks receipt data into PurchaseCreate-compatible dicts.

The mPerks receipt JSON structure (reverse-engineered from their SPA)
typically looks like:

Transaction listing:
{
    "transactions": [
        {
            "transactionId": "12345",
            "transactionDate": "2026-03-10T14:30:00Z",
            "storeNumber": "123",
            "total": 87.42,
            "savings": 12.50
        }
    ]
}

Receipt detail:
{
    "receiptId": "12345",
    "items": [
        {
            "description": "ORGANIC BANANAS",
            "upc": "0000000004011",
            "quantity": 1,
            "price": 0.69,
            "extendedPrice": 0.69,
            "regularPrice": 0.79,
            "salePrice": 0.69,
            "couponDiscount": 0.0,
            "mperksDiscount": 0.10,
            "category": "PRODUCE"
        }
    ],
    "subtotal": 74.92,
    "tax": 5.24,
    "total": 87.42,
    "totalSavings": 12.50
}
"""

import logging
from decimal import Decimal, InvalidOperation

from receiptwitness.scrapers.base import RawReceipt

logger = logging.getLogger(__name__)


def _to_decimal(value, default: str = "0") -> Decimal:
    """Safely convert a value to Decimal."""
    if value is None:
        return Decimal(default)
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        return Decimal(default)


def _parse_item(item: dict) -> dict:
    """Parse a single line item from Meijer receipt detail."""
    description = (
        item.get("description") or item.get("itemDescription") or item.get("name") or "UNKNOWN ITEM"
    )

    quantity = _to_decimal(item.get("quantity", item.get("qty", 1)), "1")
    unit_price = _to_decimal(item.get("price", item.get("unitPrice", 0)))
    extended_price = _to_decimal(item.get("extendedPrice", item.get("totalPrice")))

    # If extended_price wasn't provided, compute it
    if extended_price == Decimal("0") and unit_price != Decimal("0"):
        extended_price = unit_price * quantity

    regular_price = item.get("regularPrice")
    sale_price = item.get("salePrice")
    coupon_discount = item.get("couponDiscount", item.get("couponSavings"))
    loyalty_discount = item.get("mperksDiscount", item.get("loyaltyDiscount"))

    upc = item.get("upc", item.get("UPC"))
    if upc:
        upc = str(upc).strip().lstrip("0") or None

    category = item.get("category", item.get("departmentDescription"))

    return {
        "product_name_raw": description.strip(),
        "upc": upc,
        "quantity": quantity,
        "unit_price": unit_price,
        "extended_price": extended_price,
        "regular_price": _to_decimal(regular_price) if regular_price is not None else None,
        "sale_price": _to_decimal(sale_price) if sale_price is not None else None,
        "coupon_discount": (_to_decimal(coupon_discount) if coupon_discount is not None else None),
        "loyalty_discount": (
            _to_decimal(loyalty_discount) if loyalty_discount is not None else None
        ),
        "category_raw": category.strip() if category else None,
    }


def parse_meijer_receipt(raw: RawReceipt) -> dict:
    """Parse a RawReceipt from Meijer into a PurchaseCreate-compatible dict.

    Returns a dict with keys matching PurchaseCreate schema fields.
    The caller is responsible for setting store_id and store_location_id
    from the store registry.
    """
    data = raw.raw_data
    detail = data.get("detail", {})

    # Parse items from the detail response
    raw_items = detail.get("items", detail.get("lineItems", []))
    items = []
    for raw_item in raw_items:
        # Skip voided items
        if raw_item.get("voided") or raw_item.get("status") == "VOIDED":
            logger.debug("Skipping voided item: %s", raw_item.get("description"))
            continue
        items.append(_parse_item(raw_item))

    # Parse totals
    total = _to_decimal(detail.get("total", data.get("total", data.get("transactionTotal", 0))))
    subtotal = detail.get("subtotal", data.get("subtotal"))
    tax = detail.get("tax", data.get("tax"))
    savings = detail.get("totalSavings", data.get("savings", data.get("totalDiscount")))

    return {
        "receipt_id": raw.receipt_id,
        "purchase_date": raw.purchase_date,
        "total": total,
        "subtotal": _to_decimal(subtotal) if subtotal is not None else None,
        "tax": _to_decimal(tax) if tax is not None else None,
        "savings_total": _to_decimal(savings) if savings is not None else None,
        "source_url": raw.source_url,
        "raw_data": data,
        "items": items,
    }
