"""Target Circle receipt parser.

Transforms raw Target in-store receipt JSON into the common PurchaseCreate schema.
Target receipt data includes Circle pricing, BOGO deals, and Circle rewards
discounts that need special handling.

Target receipt detail structure (reverse-engineered from target.com SPA):

{
    "orderId": "TGT-2026-0315-7890",
    "items": [
        {
            "description": "GOOD & GATHER WHOLE MILK GAL",
            "tcin": "14767459",
            "upc": "0085239100123",
            "quantity": 1,
            "unitPrice": 3.89,
            "totalPrice": 3.89,
            "regularPrice": 4.19,
            "circlePrice": 3.89,
            "couponDiscount": 0.0,
            "circleRewardsDiscount": 0.30,
            "promoDescription": "Circle offer: Save 30c",
            "department": "GROCERY"
        }
    ],
    "subtotal": 78.32,
    "tax": 4.89,
    "total": 83.21,
    "totalSavings": 11.45
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
    """Parse a single line item from a Target receipt.

    Target items may include fields like:
    - description / itemDescription / productName
    - tcin (Target internal product ID) / upc / dpci
    - quantity / qty
    - unitPrice / price
    - totalPrice / extendedPrice / lineTotal
    - regularPrice / originalPrice
    - circlePrice / salePrice / promoPrice
    - couponDiscount / couponSavings
    - circleRewardsDiscount / circleDiscount / loyaltyDiscount
    - promoDescription / offerDescription (e.g. "BOGO 50% off", "Circle offer")
    - department / category
    """
    description = (
        item.get("description")
        or item.get("itemDescription")
        or item.get("productName")
        or item.get("name")
        or "UNKNOWN ITEM"
    )

    quantity = _to_decimal(item.get("quantity", item.get("qty", item.get("quantitySold", 1))), "1")
    unit_price = _to_decimal(item.get("unitPrice", item.get("price", item.get("basePrice", 0))))
    extended_price = _to_decimal(
        item.get("totalPrice", item.get("extendedPrice", item.get("lineTotal")))
    )

    # Compute extended_price if not provided
    if extended_price == Decimal("0") and unit_price != Decimal("0"):
        extended_price = unit_price * quantity

    regular_price = item.get("regularPrice", item.get("originalPrice"))
    # Target Circle pricing — circlePrice takes precedence over generic salePrice
    sale_price = item.get("circlePrice", item.get("salePrice", item.get("promoPrice")))
    coupon_discount = item.get(
        "couponDiscount", item.get("couponSavings", item.get("couponAmount"))
    )
    # Circle rewards / loyalty discount
    loyalty_discount = item.get(
        "circleRewardsDiscount",
        item.get("circleDiscount", item.get("loyaltyDiscount")),
    )

    # UPC handling — Target may use tcin, upc, or dpci
    upc = item.get("upc", item.get("UPC"))
    if upc:
        upc = str(upc).strip().lstrip("0") or None

    # Target also has TCIN (Target.com Item Number) and DPCI (Department/Class/Item)
    tcin = item.get("tcin", item.get("TCIN"))
    dpci = item.get("dpci", item.get("DPCI"))

    category = item.get("department", item.get("category"))

    # Capture promo/deal description for BOGO and Circle offers
    promo_description = item.get("promoDescription", item.get("offerDescription"))

    # Weight info for produce/deli items
    weight = item.get("weight", item.get("netWeight"))
    extra: dict = {}
    if weight is not None:
        extra["weight"] = str(weight)
        weight_uom = item.get("weightUom", item.get("unitOfMeasure"))
        if weight_uom:
            extra["weight_uom"] = weight_uom
    if tcin:
        extra["tcin"] = str(tcin)
    if dpci:
        extra["dpci"] = str(dpci)
    if promo_description:
        extra["promo_description"] = promo_description

    result: dict = {
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

    return result


def parse_target_receipt(raw: RawReceipt) -> dict:
    """Parse a RawReceipt from Target into a PurchaseCreate-compatible dict."""
    data = raw.raw_data
    detail = data.get("detail", {})

    # Parse items — Target uses "items" or "lineItems"
    raw_items = detail.get("items", detail.get("lineItems", []))
    items = []
    for raw_item in raw_items:
        # Skip voided / returned items
        if raw_item.get("voided") or raw_item.get("status") in (
            "VOIDED",
            "RETURNED",
            "CANCELLED",
        ):
            logger.debug("Skipping voided/returned item: %s", raw_item.get("description"))
            continue
        if raw_item.get("returnFlag") or raw_item.get("isReturn"):
            logger.debug("Skipping returned item: %s", raw_item.get("description"))
            continue
        items.append(_parse_item(raw_item))

    # Parse totals
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
        data.get("savings", data.get("totalDiscount", data.get("circleSavings"))),
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
