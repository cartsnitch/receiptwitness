"""Tests for the Meijer receipt parser."""

from decimal import Decimal

from receiptwitness.parsers.meijer import _parse_item, _to_decimal, parse_meijer_receipt
from receiptwitness.scrapers.base import RawReceipt


class TestToDecimal:
    def test_from_int(self):
        assert _to_decimal(42) == Decimal("42")

    def test_from_float(self):
        assert _to_decimal(3.49) == Decimal("3.49")

    def test_from_string(self):
        assert _to_decimal("7.99") == Decimal("7.99")

    def test_none_returns_default(self):
        assert _to_decimal(None) == Decimal("0")

    def test_none_custom_default(self):
        assert _to_decimal(None, "1") == Decimal("1")

    def test_invalid_string_returns_default(self):
        assert _to_decimal("not-a-number") == Decimal("0")


class TestParseItem:
    def test_standard_item(self):
        raw = {
            "description": "ORGANIC BANANAS",
            "upc": "0000000004011",
            "quantity": 1,
            "price": 0.69,
            "extendedPrice": 0.69,
            "regularPrice": 0.79,
            "salePrice": 0.69,
            "couponDiscount": 0.0,
            "mperksDiscount": 0.10,
            "category": "PRODUCE",
        }
        result = _parse_item(raw)
        assert result["product_name_raw"] == "ORGANIC BANANAS"
        assert result["upc"] == "4011"
        assert result["quantity"] == Decimal("1")
        assert result["unit_price"] == Decimal("0.69")
        assert result["extended_price"] == Decimal("0.69")
        assert result["regular_price"] == Decimal("0.79")
        assert result["sale_price"] == Decimal("0.69")
        assert result["loyalty_discount"] == Decimal("0.10")
        assert result["category_raw"] == "PRODUCE"

    def test_weighted_item(self):
        raw = {
            "description": "WEIGHTED DELI TURKEY",
            "quantity": 0.75,
            "price": 8.99,
            "extendedPrice": 6.74,
            "category": "DELI",
        }
        result = _parse_item(raw)
        assert result["product_name_raw"] == "WEIGHTED DELI TURKEY"
        assert result["upc"] is None
        assert result["quantity"] == Decimal("0.75")
        assert result["unit_price"] == Decimal("8.99")
        assert result["extended_price"] == Decimal("6.74")

    def test_missing_extended_price_computed(self):
        raw = {
            "description": "TEST ITEM",
            "quantity": 3,
            "price": 2.50,
        }
        result = _parse_item(raw)
        assert result["extended_price"] == Decimal("2.50") * Decimal("3")

    def test_item_with_coupon_discount(self):
        raw = {
            "description": "CHEERIOS 18OZ",
            "upc": "0016000275614",
            "quantity": 1,
            "price": 4.99,
            "extendedPrice": 4.99,
            "couponDiscount": 0.50,
        }
        result = _parse_item(raw)
        assert result["coupon_discount"] == Decimal("0.50")

    def test_missing_description_fallback(self):
        raw = {"price": 1.00, "extendedPrice": 1.00}
        result = _parse_item(raw)
        assert result["product_name_raw"] == "UNKNOWN ITEM"

    def test_alternative_field_names(self):
        raw = {
            "itemDescription": "ALT NAME ITEM",
            "unitPrice": 5.00,
            "totalPrice": 5.00,
            "qty": 1,
            "UPC": "123456789",
            "departmentDescription": "GROCERY",
        }
        result = _parse_item(raw)
        assert result["product_name_raw"] == "ALT NAME ITEM"
        assert result["unit_price"] == Decimal("5.00")
        assert result["upc"] == "123456789"
        assert result["category_raw"] == "GROCERY"


class TestParseMeijerReceipt:
    def test_full_receipt(self, meijer_receipt_data):
        raw = RawReceipt(
            receipt_id="TXN-2026-0310-001",
            purchase_date="2026-03-10T14:30:00Z",
            store_number="42",
            raw_data=meijer_receipt_data,
        )
        result = parse_meijer_receipt(raw)

        assert result["receipt_id"] == "TXN-2026-0310-001"
        assert result["purchase_date"] == "2026-03-10T14:30:00Z"
        assert result["total"] == Decimal("87.42")
        assert result["subtotal"] == Decimal("74.92")
        assert result["tax"] == Decimal("5.24")
        assert result["savings_total"] == Decimal("12.50")

        # Should have 5 items (voided item excluded)
        assert len(result["items"]) == 5

        # Verify first item
        bananas = result["items"][0]
        assert bananas["product_name_raw"] == "ORGANIC BANANAS"
        assert bananas["upc"] == "4011"

    def test_voided_items_excluded(self, meijer_receipt_data):
        raw = RawReceipt(
            receipt_id="TXN-2026-0310-001",
            purchase_date="2026-03-10",
            raw_data=meijer_receipt_data,
        )
        result = parse_meijer_receipt(raw)

        item_names = [i["product_name_raw"] for i in result["items"]]
        assert "VOIDED SODA 12PK" not in item_names

    def test_empty_receipt(self):
        raw = RawReceipt(
            receipt_id="EMPTY-001",
            purchase_date="2026-03-10",
            raw_data={"detail": {"items": [], "total": 0}},
        )
        result = parse_meijer_receipt(raw)
        assert result["items"] == []
        assert result["total"] == Decimal("0")

    def test_receipt_with_no_detail(self):
        raw = RawReceipt(
            receipt_id="NO-DETAIL-001",
            purchase_date="2026-03-10",
            raw_data={"total": 50.00},
        )
        result = parse_meijer_receipt(raw)
        assert result["items"] == []
        assert result["total"] == Decimal("50.00")

    def test_raw_data_preserved(self, meijer_receipt_data):
        raw = RawReceipt(
            receipt_id="TXN-2026-0310-001",
            purchase_date="2026-03-10",
            raw_data=meijer_receipt_data,
        )
        result = parse_meijer_receipt(raw)
        assert result["raw_data"] is meijer_receipt_data
