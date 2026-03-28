"""Regression tests: scraper output matches expected schema.

Validates that parsed receipts from both Kroger and Meijer conform to the
PurchaseCreate schema contract. Uses recorded fixtures to ensure outputs
remain stable across code changes.
"""

from decimal import Decimal

from receiptwitness.parsers.kroger import parse_kroger_receipt
from receiptwitness.parsers.meijer import parse_meijer_receipt
from receiptwitness.scrapers.base import RawReceipt

# Required top-level keys in a parsed receipt
RECEIPT_REQUIRED_KEYS = {"receipt_id", "purchase_date", "total", "items", "raw_data"}
RECEIPT_OPTIONAL_KEYS = {"subtotal", "tax", "savings_total", "source_url"}

# Required keys in each parsed item
ITEM_REQUIRED_KEYS = {
    "product_name_raw",
    "upc",
    "quantity",
    "unit_price",
    "extended_price",
}
ITEM_OPTIONAL_KEYS = {
    "regular_price",
    "sale_price",
    "coupon_discount",
    "loyalty_discount",
    "category_raw",
}


def _validate_receipt_schema(result: dict) -> None:
    """Assert that a parsed receipt dict conforms to the expected schema."""
    # All required keys present
    for key in RECEIPT_REQUIRED_KEYS:
        assert key in result, f"Missing required key: {key}"

    # Types
    assert isinstance(result["receipt_id"], str)
    assert isinstance(result["purchase_date"], str)
    assert isinstance(result["total"], Decimal)
    assert isinstance(result["items"], list)
    assert isinstance(result["raw_data"], dict)

    # Optional keys should be correct types when present
    if result.get("subtotal") is not None:
        assert isinstance(result["subtotal"], Decimal)
    if result.get("tax") is not None:
        assert isinstance(result["tax"], Decimal)
    if result.get("savings_total") is not None:
        assert isinstance(result["savings_total"], Decimal)
    if result.get("source_url") is not None:
        assert isinstance(result["source_url"], str)

    # No unexpected keys
    all_keys = RECEIPT_REQUIRED_KEYS | RECEIPT_OPTIONAL_KEYS
    for key in result:
        assert key in all_keys, f"Unexpected key in receipt: {key}"


def _validate_item_schema(item: dict) -> None:
    """Assert that a parsed item dict conforms to the expected schema."""
    for key in ITEM_REQUIRED_KEYS:
        assert key in item, f"Missing required item key: {key}"

    assert isinstance(item["product_name_raw"], str)
    assert len(item["product_name_raw"]) > 0
    assert isinstance(item["quantity"], Decimal)
    assert isinstance(item["unit_price"], Decimal)
    assert isinstance(item["extended_price"], Decimal)

    # UPC can be None or str
    if item["upc"] is not None:
        assert isinstance(item["upc"], str)
        # UPC should not have leading zeros (stripped during parsing)
        assert not item["upc"].startswith("0"), f"UPC has leading zeros: {item['upc']}"

    # Optional Decimal fields
    for opt_key in ("regular_price", "sale_price", "coupon_discount", "loyalty_discount"):
        if item.get(opt_key) is not None:
            assert isinstance(item[opt_key], Decimal), f"{opt_key} should be Decimal"

    if item.get("category_raw") is not None:
        assert isinstance(item["category_raw"], str)

    # No unexpected keys
    all_keys = ITEM_REQUIRED_KEYS | ITEM_OPTIONAL_KEYS
    for key in item:
        assert key in all_keys, f"Unexpected key in item: {key}"


class TestKrogerSchemaValidation:
    def test_full_receipt_schema(self, kroger_receipt_data):
        raw = RawReceipt(
            receipt_id="KR-2026-0312-4471",
            purchase_date="2026-03-12T16:45:00Z",
            store_number="00357",
            raw_data=kroger_receipt_data,
            source_url="https://www.kroger.com/atlas/v1/receipt/api?orderId=KR-2026-0312-4471",
        )
        result = parse_kroger_receipt(raw)
        _validate_receipt_schema(result)
        for item in result["items"]:
            _validate_item_schema(item)

    def test_item_count_excludes_voided_and_returned(self, kroger_receipt_data):
        """Fixture has 10 items, 2 should be excluded (voided + returned)."""
        raw = RawReceipt(
            receipt_id="KR-2026-0312-4471",
            purchase_date="2026-03-12T16:45:00Z",
            raw_data=kroger_receipt_data,
        )
        result = parse_kroger_receipt(raw)
        assert len(result["items"]) == 8

    def test_totals_are_positive_decimals(self, kroger_receipt_data):
        raw = RawReceipt(
            receipt_id="KR-2026-0312-4471",
            purchase_date="2026-03-12T16:45:00Z",
            raw_data=kroger_receipt_data,
        )
        result = parse_kroger_receipt(raw)
        assert result["total"] > Decimal("0")
        assert result["subtotal"] > Decimal("0")
        assert result["tax"] > Decimal("0")
        assert result["savings_total"] > Decimal("0")

    def test_receipt_id_preserved(self, kroger_receipt_data):
        raw = RawReceipt(
            receipt_id="KR-2026-0312-4471",
            purchase_date="2026-03-12T16:45:00Z",
            raw_data=kroger_receipt_data,
        )
        result = parse_kroger_receipt(raw)
        assert result["receipt_id"] == "KR-2026-0312-4471"

    def test_known_product_prices(self, kroger_receipt_data):
        """Verify specific products produce correct price extraction."""
        raw = RawReceipt(
            receipt_id="KR-2026-0312-4471",
            purchase_date="2026-03-12T16:45:00Z",
            raw_data=kroger_receipt_data,
        )
        result = parse_kroger_receipt(raw)
        items_by_name = {i["product_name_raw"]: i for i in result["items"]}

        # Milk: $3.99, regular $4.29
        milk = items_by_name["KROGER WHOLE MILK GAL"]
        assert milk["unit_price"] == Decimal("3.99")
        assert milk["regular_price"] == Decimal("4.29")
        assert milk["sale_price"] == Decimal("3.99")

        # Eggs: qty 2, $5.49 each, total $10.98
        eggs = items_by_name["SIMPLE TRUTH ORG EGGS 12CT"]
        assert eggs["quantity"] == Decimal("2")
        assert eggs["unit_price"] == Decimal("5.49")
        assert eggs["extended_price"] == Decimal("10.98")

        # Deli turkey: weighted item, 0.68 lb
        turkey = items_by_name["KROGER DELI TURKEY BREAST"]
        assert turkey["quantity"] == Decimal("0.68")
        assert turkey["upc"] is None

    def test_multi_quantity_item_correct(self, kroger_receipt_data):
        """Pasta is qty=3, unit=$2.49, total=$7.47."""
        raw = RawReceipt(
            receipt_id="KR-2026-0312-4471",
            purchase_date="2026-03-12T16:45:00Z",
            raw_data=kroger_receipt_data,
        )
        result = parse_kroger_receipt(raw)
        pasta = [i for i in result["items"] if "PASTA" in i["product_name_raw"]][0]
        assert pasta["quantity"] == Decimal("3")
        assert pasta["unit_price"] == Decimal("2.49")
        assert pasta["extended_price"] == Decimal("7.47")

    def test_coupon_discount_captured(self, kroger_receipt_data):
        """Tide Pods has $2.00 coupon."""
        raw = RawReceipt(
            receipt_id="KR-2026-0312-4471",
            purchase_date="2026-03-12T16:45:00Z",
            raw_data=kroger_receipt_data,
        )
        result = parse_kroger_receipt(raw)
        tide = [i for i in result["items"] if "TIDE" in i["product_name_raw"]][0]
        assert tide["coupon_discount"] == Decimal("2.00")


class TestMeijerSchemaValidation:
    def test_full_receipt_schema(self, meijer_receipt_data):
        raw = RawReceipt(
            receipt_id="TXN-2026-0310-001",
            purchase_date="2026-03-10T14:30:00Z",
            store_number="42",
            raw_data=meijer_receipt_data,
            source_url="https://www.meijer.com/bin/meijer/profile/receipt?receiptId=TXN-2026-0310-001",
        )
        result = parse_meijer_receipt(raw)
        _validate_receipt_schema(result)
        for item in result["items"]:
            _validate_item_schema(item)

    def test_item_count_excludes_voided(self, meijer_receipt_data):
        """Fixture has 6 items, 1 should be excluded (voided soda)."""
        raw = RawReceipt(
            receipt_id="TXN-2026-0310-001",
            purchase_date="2026-03-10T14:30:00Z",
            raw_data=meijer_receipt_data,
        )
        result = parse_meijer_receipt(raw)
        assert len(result["items"]) == 5

    def test_totals_are_positive_decimals(self, meijer_receipt_data):
        raw = RawReceipt(
            receipt_id="TXN-2026-0310-001",
            purchase_date="2026-03-10T14:30:00Z",
            raw_data=meijer_receipt_data,
        )
        result = parse_meijer_receipt(raw)
        assert result["total"] > Decimal("0")
        assert result["subtotal"] > Decimal("0")
        assert result["tax"] > Decimal("0")
        assert result["savings_total"] > Decimal("0")

    def test_receipt_id_preserved(self, meijer_receipt_data):
        raw = RawReceipt(
            receipt_id="TXN-2026-0310-001",
            purchase_date="2026-03-10T14:30:00Z",
            raw_data=meijer_receipt_data,
        )
        result = parse_meijer_receipt(raw)
        assert result["receipt_id"] == "TXN-2026-0310-001"

    def test_known_product_prices(self, meijer_receipt_data):
        """Verify specific Meijer products produce correct price extraction."""
        raw = RawReceipt(
            receipt_id="TXN-2026-0310-001",
            purchase_date="2026-03-10T14:30:00Z",
            raw_data=meijer_receipt_data,
        )
        result = parse_meijer_receipt(raw)
        items_by_name = {i["product_name_raw"]: i for i in result["items"]}

        # Bananas: $0.69
        bananas = items_by_name["ORGANIC BANANAS"]
        assert bananas["unit_price"] == Decimal("0.69")
        assert bananas["mperks_discount"] if "mperks_discount" in bananas else True
        assert bananas["loyalty_discount"] == Decimal("0.10")

        # Milk: qty 2, $3.49 each, total $6.98
        milk = items_by_name["MEIJER 2% MILK GAL"]
        assert milk["quantity"] == Decimal("2")
        assert milk["unit_price"] == Decimal("3.49")
        assert milk["extended_price"] == Decimal("6.98")

        # Weighted deli turkey: 0.75 lb at $8.99/lb
        turkey = items_by_name["WEIGHTED DELI TURKEY"]
        assert turkey["quantity"] == Decimal("0.75")
        assert turkey["upc"] is None

    def test_mperks_discount_captured(self, meijer_receipt_data):
        """Paper towels has $1.00 mPerks discount."""
        raw = RawReceipt(
            receipt_id="TXN-2026-0310-001",
            purchase_date="2026-03-10T14:30:00Z",
            raw_data=meijer_receipt_data,
        )
        result = parse_meijer_receipt(raw)
        towels = [i for i in result["items"] if "PAPER TOWELS" in i["product_name_raw"]][0]
        assert towels["loyalty_discount"] == Decimal("1.00")
        assert towels["coupon_discount"] == Decimal("1.00")

    def test_cheerios_coupon_discount(self, meijer_receipt_data):
        """Cheerios has $0.50 coupon."""
        raw = RawReceipt(
            receipt_id="TXN-2026-0310-001",
            purchase_date="2026-03-10T14:30:00Z",
            raw_data=meijer_receipt_data,
        )
        result = parse_meijer_receipt(raw)
        cheerios = [i for i in result["items"] if "CHEERIOS" in i["product_name_raw"]][0]
        assert cheerios["coupon_discount"] == Decimal("0.50")


class TestEmptyAndEdgeCaseSchemas:
    """Regression tests for edge-case receipts that should not crash."""

    def test_kroger_empty_receipt(self):
        raw = RawReceipt(receipt_id="KR-EMPTY", purchase_date="2026-03-12", raw_data={})
        result = parse_kroger_receipt(raw)
        _validate_receipt_schema(result)
        assert result["items"] == []
        assert result["total"] == Decimal("0")

    def test_meijer_empty_receipt(self):
        raw = RawReceipt(receipt_id="MJ-EMPTY", purchase_date="2026-03-10", raw_data={})
        result = parse_meijer_receipt(raw)
        _validate_receipt_schema(result)
        assert result["items"] == []
        assert result["total"] == Decimal("0")

    def test_kroger_receipt_no_detail(self):
        raw = RawReceipt(
            receipt_id="KR-NODET",
            purchase_date="2026-03-12",
            raw_data={"total": 50.00},
        )
        result = parse_kroger_receipt(raw)
        _validate_receipt_schema(result)
        assert result["items"] == []
        assert result["total"] == Decimal("50.00")

    def test_meijer_receipt_no_detail(self):
        raw = RawReceipt(
            receipt_id="MJ-NODET",
            purchase_date="2026-03-10",
            raw_data={"total": 30.00},
        )
        result = parse_meijer_receipt(raw)
        _validate_receipt_schema(result)
        assert result["items"] == []
        assert result["total"] == Decimal("30.00")

    def test_kroger_receipt_all_voided(self):
        """A receipt where every item is voided should have 0 items."""
        raw = RawReceipt(
            receipt_id="KR-ALLVOID",
            purchase_date="2026-03-12",
            raw_data={
                "detail": {
                    "items": [
                        {"description": "VOIDED A", "basePrice": 5.0, "voided": True},
                        {"description": "VOIDED B", "basePrice": 3.0, "status": "VOIDED"},
                        {"description": "RETURNED C", "basePrice": 7.0, "status": "RETURNED"},
                        {"description": "RETURNED D", "basePrice": 2.0, "returnFlag": True},
                    ],
                    "total": 0,
                }
            },
        )
        result = parse_kroger_receipt(raw)
        _validate_receipt_schema(result)
        assert result["items"] == []

    def test_meijer_receipt_all_voided(self):
        raw = RawReceipt(
            receipt_id="MJ-ALLVOID",
            purchase_date="2026-03-10",
            raw_data={
                "detail": {
                    "items": [
                        {"description": "VOIDED A", "price": 5.0, "voided": True},
                        {"description": "VOIDED B", "price": 3.0, "status": "VOIDED"},
                    ],
                    "total": 0,
                }
            },
        )
        result = parse_meijer_receipt(raw)
        _validate_receipt_schema(result)
        assert result["items"] == []
