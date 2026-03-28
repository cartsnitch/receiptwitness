"""Kroger receipt parser.

Transforms raw Kroger receipt JSON into the common PurchaseCreate schema.
Kroger receipt data uses different field names than Meijer — this parser
handles Kroger-specific naming conventions and receipt structure.
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
    """Parse a single line item from a Kroger receipt.

    Kroger items typically include fields like:
    - description / itemDescription / productName
    - upc / krogerProductId
    - quantity / qty
    - basePrice / unitPrice / price
    - totalPrice / extendedAmount / lineTotal
    - regularPrice / originalPrice
    - salePrice / promoPrice
    - couponAmount / couponSavings
    - loyaltyDiscount / fuelPointsDiscount / plusCardSavings
    - department / category / aisle
    """
    description = (
        item.get("description")
        or item.get("itemDescription")
        or item.get("productName")
        or item.get("name")
        or "UNKNOWN ITEM"
    )

    quantity = _to_decimal(item.get("quantity", item.get("qty", item.get("quantitySold", 1))), "1")
    unit_price = _to_decimal(item.get("basePrice", item.get("unitPrice", item.get("price", 0))))
    extended_price = _to_decimal(
        item.get("totalPrice", item.get("extendedAmount", item.get("lineTotal")))
    )

    # Compute extended_price if not provided
    if extended_price == Decimal("0") and unit_price != Decimal("0"):
        extended_price = unit_price * quantity

    regular_price = item.get("regularPrice", item.get("originalPrice"))
    sale_price = item.get("salePrice", item.get("promoPrice"))
    coupon_discount = item.get(
        "couponAmount", item.get("couponSavings", item.get("couponDiscount"))
    )
    loyalty_discount = item.get(
        "plusCardSavings",
        item.get("loyaltyDiscount", item.get("fuelPointsDiscount")),
    )

    # UPC handling — Kroger may use krogerProductId or upc
    upc = item.get("upc", item.get("UPC", item.get("krogerProductId")))
    if upc:
        upc = str(upc).strip().lstrip("0") or None

    category = item.get("department", item.get("category", item.get("aisle")))

    # Weight info for produce/deli items
    weight = item.get("weight", item.get("netWeight"))
    extra = {}
    if weight is not None:
        extra["weight"] = str(weight)
        weight_uom = item.get("weightUom", item.get("unitOfMeasure"))
        if weight_uom:
            extra["weight_uom"] = weight_uom

    result = {
        "product_name_raw": description.strip(),
        "upc": upc,
        "quantity": quantity,
        "unit_price": unit_price,
        "extended_price": extended_price,
        "regular_price": (_to_decimal(regular_price) if regular_price is not None else None),
        "sale_price": (_to_decimal(sale_price) if sale_price is not None else None),
        "coupon_discount": (_to_decimal(coupon_discount) if coupon_discount is not None else None),
        "loyalty_discount": (
            _to_decimal(loyalty_discount) if loyalty_discount is not None else None
        ),
        "category_raw": category.strip() if category else None,
    }

    return result


def parse_kroger_receipt(raw: RawReceipt) -> dict:
    """Parse a RawReceipt from Kroger into a PurchaseCreate-compatible dict."""
    data = raw.raw_data
    detail = data.get("detail", {})

    # Parse items — Kroger uses "items" or "lineItems" or "receiptItems"
    raw_items = detail.get("items", detail.get("lineItems", detail.get("receiptItems", [])))
    items = []
    for raw_item in raw_items:
        # Skip voided / returned items
        if raw_item.get("voided") or raw_item.get("status") in (
            "VOIDED",
            "RETURNED",
        ):
            logger.debug("Skipping voided/returned item: %s", raw_item.get("description"))
            continue
        if raw_item.get("returnFlag") or raw_item.get("isReturn"):
            logger.debug("Skipping returned item: %s", raw_item.get("description"))
            continue
        items.append(_parse_item(raw_item))

    # Parse totals — Kroger uses various field names
    total = _to_decimal(
        detail.get(
            "total",
            data.get("total", data.get("orderTotal", data.get("grandTotal", 0))),
        )
    )
    subtotal = detail.get("subtotal", data.get("subtotal", data.get("subTotal")))
    tax = detail.get("tax", data.get("tax", data.get("salesTax")))
    savings = detail.get(
        "totalSavings",
        data.get("savings", data.get("totalDiscount", data.get("youSaved"))),
    )

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
