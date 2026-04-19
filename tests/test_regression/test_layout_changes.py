"""Regression tests: graceful handling of page layout changes.

Retailers frequently change their API response structures, field names,
and nesting. These tests verify that both parsers degrade gracefully when
encountering alternative or missing fields — producing valid output
instead of crashing.
"""

from decimal import Decimal

from receiptwitness.parsers.kroger import parse_kroger_receipt
from receiptwitness.parsers.meijer import parse_meijer_receipt
from receiptwitness.scrapers.base import RawReceipt


class TestKrogerFieldNameVariations:
    """Kroger changes field names between app versions and API revisions."""

    def test_alternative_item_key_line_items(self):
        raw = RawReceipt(
            receipt_id="KR-ALT-1",
            purchase_date="2026-03-12",
            raw_data={
                "detail": {
                    "lineItems": [{"description": "MILK", "basePrice": 3.99, "totalPrice": 3.99}],
                    "total": 3.99,
                }
            },
        )
        result = parse_kroger_receipt(raw)
        assert len(result["items"]) == 1
        assert result["items"][0]["product_name_raw"] == "MILK"

    def test_alternative_item_key_receipt_items(self):
        raw = RawReceipt(
            receipt_id="KR-ALT-2",
            purchase_date="2026-03-12",
            raw_data={
                "detail": {
                    "receiptItems": [
                        {"description": "EGGS", "basePrice": 5.49, "totalPrice": 5.49}
                    ],
                    "total": 5.49,
                }
            },
        )
        result = parse_kroger_receipt(raw)
        assert len(result["items"]) == 1
        assert result["items"][0]["product_name_raw"] == "EGGS"

    def test_alternative_description_fields(self):
        """Test productName and itemDescription fallbacks."""
        for field in ("productName", "itemDescription", "name"):
            raw = RawReceipt(
                receipt_id="KR-DESC",
                purchase_date="2026-03-12",
                raw_data={
                    "detail": {
                        "items": [{field: "TEST PRODUCT", "basePrice": 1.00, "totalPrice": 1.00}],
                        "total": 1.00,
                    }
                },
            )
            result = parse_kroger_receipt(raw)
            assert result["items"][0]["product_name_raw"] == "TEST PRODUCT"

    def test_alternative_price_fields(self):
        """Test unitPrice and price fallbacks for basePrice."""
        raw = RawReceipt(
            receipt_id="KR-PRICE-1",
            purchase_date="2026-03-12",
            raw_data={
                "detail": {
                    "items": [{"description": "ITEM A", "unitPrice": 2.50, "totalPrice": 2.50}],
                    "total": 2.50,
                }
            },
        )
        result = parse_kroger_receipt(raw)
        assert result["items"][0]["unit_price"] == Decimal("2.50")

        raw2 = RawReceipt(
            receipt_id="KR-PRICE-2",
            purchase_date="2026-03-12",
            raw_data={
                "detail": {
                    "items": [{"description": "ITEM B", "price": 4.00, "totalPrice": 4.00}],
                    "total": 4.00,
                }
            },
        )
        result2 = parse_kroger_receipt(raw2)
        assert result2["items"][0]["unit_price"] == Decimal("4.00")

    def test_alternative_total_fields(self):
        """Test orderTotal, grandTotal fallbacks."""
        for field in ("orderTotal", "grandTotal"):
            raw = RawReceipt(
                receipt_id="KR-TOT",
                purchase_date="2026-03-12",
                raw_data={field: 42.50, "detail": {}},
            )
            result = parse_kroger_receipt(raw)
            assert result["total"] == Decimal("42.50")

    def test_alternative_savings_fields(self):
        """Test youSaved and totalDiscount fallbacks."""
        raw = RawReceipt(
            receipt_id="KR-SAV-1",
            purchase_date="2026-03-12",
            raw_data={"youSaved": 5.00, "detail": {}},
        )
        result = parse_kroger_receipt(raw)
        assert result["savings_total"] == Decimal("5.00")

    def test_alternative_tax_field(self):
        raw = RawReceipt(
            receipt_id="KR-TAX",
            purchase_date="2026-03-12",
            raw_data={"salesTax": 3.25, "detail": {}},
        )
        result = parse_kroger_receipt(raw)
        assert result["tax"] == Decimal("3.25")

    def test_alternative_quantity_field_qty(self):
        raw = RawReceipt(
            receipt_id="KR-QTY",
            purchase_date="2026-03-12",
            raw_data={
                "detail": {
                    "items": [
                        {"description": "APPLES", "qty": 5, "basePrice": 1.00, "totalPrice": 5.00}
                    ],
                    "total": 5.00,
                }
            },
        )
        result = parse_kroger_receipt(raw)
        assert result["items"][0]["quantity"] == Decimal("5")

    def test_alternative_upc_field_kroger_product_id(self):
        raw = RawReceipt(
            receipt_id="KR-UPC",
            purchase_date="2026-03-12",
            raw_data={
                "detail": {
                    "items": [
                        {
                            "description": "ITEM",
                            "krogerProductId": "12345678",
                            "basePrice": 1.00,
                            "totalPrice": 1.00,
                        }
                    ],
                    "total": 1.00,
                }
            },
        )
        result = parse_kroger_receipt(raw)
        assert result["items"][0]["upc"] == "12345678"

    def test_missing_extended_price_computed(self):
        """When totalPrice is missing, extended_price = unit_price * quantity."""
        raw = RawReceipt(
            receipt_id="KR-CALC",
            purchase_date="2026-03-12",
            raw_data={
                "detail": {
                    "items": [{"description": "EGGS", "basePrice": 5.49, "quantity": 2}],
                    "total": 10.98,
                }
            },
        )
        result = parse_kroger_receipt(raw)
        assert result["items"][0]["extended_price"] == Decimal("5.49") * Decimal("2")


class TestMeijerFieldNameVariations:
    """Meijer XHR endpoints may change field names between SPA versions."""

    def test_alternative_item_key_line_items(self):
        raw = RawReceipt(
            receipt_id="MJ-ALT-1",
            purchase_date="2026-03-10",
            raw_data={
                "detail": {
                    "lineItems": [{"description": "BANANAS", "price": 0.69, "extendedPrice": 0.69}],
                    "total": 0.69,
                }
            },
        )
        result = parse_meijer_receipt(raw)
        assert len(result["items"]) == 1
        assert result["items"][0]["product_name_raw"] == "BANANAS"

    def test_alternative_description_fields(self):
        for field in ("itemDescription", "name"):
            raw = RawReceipt(
                receipt_id="MJ-DESC",
                purchase_date="2026-03-10",
                raw_data={
                    "detail": {
                        "items": [{field: "TEST ITEM", "price": 1.00, "extendedPrice": 1.00}],
                        "total": 1.00,
                    }
                },
            )
            result = parse_meijer_receipt(raw)
            assert result["items"][0]["product_name_raw"] == "TEST ITEM"

    def test_alternative_price_field_unit_price(self):
        raw = RawReceipt(
            receipt_id="MJ-PRICE",
            purchase_date="2026-03-10",
            raw_data={
                "detail": {
                    "items": [{"description": "MILK", "unitPrice": 3.49, "totalPrice": 3.49}],
                    "total": 3.49,
                }
            },
        )
        result = parse_meijer_receipt(raw)
        assert result["items"][0]["unit_price"] == Decimal("3.49")

    def test_alternative_extended_price_field_total_price(self):
        raw = RawReceipt(
            receipt_id="MJ-EXT",
            purchase_date="2026-03-10",
            raw_data={
                "detail": {
                    "items": [{"description": "CEREAL", "price": 4.99, "totalPrice": 4.99}],
                    "total": 4.99,
                }
            },
        )
        result = parse_meijer_receipt(raw)
        assert result["items"][0]["extended_price"] == Decimal("4.99")

    def test_alternative_total_field_transaction_total(self):
        raw = RawReceipt(
            receipt_id="MJ-TOT",
            purchase_date="2026-03-10",
            raw_data={"transactionTotal": 55.00, "detail": {}},
        )
        result = parse_meijer_receipt(raw)
        assert result["total"] == Decimal("55.00")

    def test_alternative_loyalty_field(self):
        raw = RawReceipt(
            receipt_id="MJ-LOY",
            purchase_date="2026-03-10",
            raw_data={
                "detail": {
                    "items": [
                        {
                            "description": "ITEM",
                            "price": 5.00,
                            "extendedPrice": 5.00,
                            "loyaltyDiscount": 0.50,
                        }
                    ],
                    "total": 5.00,
                }
            },
        )
        result = parse_meijer_receipt(raw)
        assert result["items"][0]["loyalty_discount"] == Decimal("0.50")

    def test_alternative_upc_field_uppercase(self):
        raw = RawReceipt(
            receipt_id="MJ-UPC",
            purchase_date="2026-03-10",
            raw_data={
                "detail": {
                    "items": [
                        {
                            "description": "ITEM",
                            "UPC": "0012345678",
                            "price": 1.00,
                            "extendedPrice": 1.00,
                        }
                    ],
                    "total": 1.00,
                }
            },
        )
        result = parse_meijer_receipt(raw)
        assert result["items"][0]["upc"] == "12345678"

    def test_alternative_category_field(self):
        raw = RawReceipt(
            receipt_id="MJ-CAT",
            purchase_date="2026-03-10",
            raw_data={
                "detail": {
                    "items": [
                        {
                            "description": "ITEM",
                            "price": 1.00,
                            "extendedPrice": 1.00,
                            "departmentDescription": "FROZEN",
                        }
                    ],
                    "total": 1.00,
                }
            },
        )
        result = parse_meijer_receipt(raw)
        assert result["items"][0]["category_raw"] == "FROZEN"

    def test_missing_extended_price_computed(self):
        raw = RawReceipt(
            receipt_id="MJ-CALC",
            purchase_date="2026-03-10",
            raw_data={
                "detail": {
                    "items": [{"description": "MILK", "price": 3.49, "quantity": 2}],
                    "total": 6.98,
                }
            },
        )
        result = parse_meijer_receipt(raw)
        assert result["items"][0]["extended_price"] == Decimal("3.49") * Decimal("2")

    def test_missing_description_fallback(self):
        raw = RawReceipt(
            receipt_id="MJ-NODESC",
            purchase_date="2026-03-10",
            raw_data={
                "detail": {
                    "items": [{"price": 1.00, "extendedPrice": 1.00}],
                    "total": 1.00,
                }
            },
        )
        result = parse_meijer_receipt(raw)
        assert result["items"][0]["product_name_raw"] == "UNKNOWN ITEM"


class TestMixedFieldVersions:
    """Test receipts that mix field naming conventions (happens during rollouts)."""

    def test_kroger_mixed_item_fields(self):
        """Some items use old names, some use new names in same receipt."""
        raw = RawReceipt(
            receipt_id="KR-MIX",
            purchase_date="2026-03-12",
            raw_data={
                "detail": {
                    "items": [
                        {"description": "OLD STYLE", "basePrice": 2.00, "totalPrice": 2.00},
                        {"productName": "NEW STYLE", "unitPrice": 3.00, "extendedAmount": 3.00},
                    ],
                    "total": 5.00,
                }
            },
        )
        result = parse_kroger_receipt(raw)
        assert len(result["items"]) == 2
        assert result["items"][0]["product_name_raw"] == "OLD STYLE"
        assert result["items"][0]["unit_price"] == Decimal("2.00")
        assert result["items"][1]["product_name_raw"] == "NEW STYLE"
        assert result["items"][1]["unit_price"] == Decimal("3.00")

    def test_kroger_completely_unknown_structure_no_crash(self):
        """Receipt with unrecognized structure should return empty items."""
        raw = RawReceipt(
            receipt_id="KR-UNKNOWN",
            purchase_date="2026-03-12",
            raw_data={"something_unexpected": [1, 2, 3], "detail": {"foo": "bar"}},
        )
        result = parse_kroger_receipt(raw)
        assert result["receipt_id"] == "KR-UNKNOWN"
        assert result["items"] == []

    def test_meijer_completely_unknown_structure_no_crash(self):
        raw = RawReceipt(
            receipt_id="MJ-UNKNOWN",
            purchase_date="2026-03-10",
            raw_data={"something_unexpected": [1, 2, 3], "detail": {"foo": "bar"}},
        )
        result = parse_meijer_receipt(raw)
        assert result["receipt_id"] == "MJ-UNKNOWN"
        assert result["items"] == []

    def test_kroger_null_fields_no_crash(self):
        """Fields with None values should be handled gracefully."""
        raw = RawReceipt(
            receipt_id="KR-NULL",
            purchase_date="2026-03-12",
            raw_data={
                "detail": {
                    "items": [
                        {
                            "description": "ITEM",
                            "basePrice": None,
                            "totalPrice": None,
                            "quantity": None,
                            "upc": None,
                            "department": None,
                        }
                    ],
                    "total": None,
                    "subtotal": None,
                    "tax": None,
                }
            },
        )
        result = parse_kroger_receipt(raw)
        assert result["items"][0]["product_name_raw"] == "ITEM"
        assert result["items"][0]["unit_price"] == Decimal("0")

    def test_meijer_null_fields_no_crash(self):
        raw = RawReceipt(
            receipt_id="MJ-NULL",
            purchase_date="2026-03-10",
            raw_data={
                "detail": {
                    "items": [
                        {
                            "description": "ITEM",
                            "price": None,
                            "extendedPrice": None,
                            "quantity": None,
                            "upc": None,
                            "category": None,
                        }
                    ],
                    "total": None,
                }
            },
        )
        result = parse_meijer_receipt(raw)
        assert result["items"][0]["product_name_raw"] == "ITEM"
        assert result["items"][0]["unit_price"] == Decimal("0")
