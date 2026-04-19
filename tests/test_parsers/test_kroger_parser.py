"""Tests for the Kroger receipt parser."""

from decimal import Decimal

from receiptwitness.parsers.kroger import _parse_item, _to_decimal, parse_kroger_receipt
from receiptwitness.scrapers.base import RawReceipt


class TestToDecimal:
    def test_from_int(self):
        assert _to_decimal(42) == Decimal("42")

    def test_from_float(self):
        assert _to_decimal(3.99) == Decimal("3.99")

    def test_from_string(self):
        assert _to_decimal("7.49") == Decimal("7.49")

    def test_none_returns_default(self):
        assert _to_decimal(None) == Decimal("0")

    def test_none_custom_default(self):
        assert _to_decimal(None, "1") == Decimal("1")

    def test_invalid_string_returns_default(self):
        assert _to_decimal("not-a-number") == Decimal("0")

    def test_empty_string_returns_default(self):
        assert _to_decimal("") == Decimal("0")


class TestParseItem:
    def test_standard_item(self):
        raw = {
            "description": "KROGER WHOLE MILK GAL",
            "upc": "0001111041700",
            "quantity": 1,
            "basePrice": 3.99,
            "totalPrice": 3.99,
            "regularPrice": 4.29,
            "salePrice": 3.99,
            "couponAmount": 0.0,
            "plusCardSavings": 0.30,
            "department": "DAIRY",
        }
        result = _parse_item(raw)
        assert result["product_name_raw"] == "KROGER WHOLE MILK GAL"
        assert result["upc"] == "1111041700"
        assert result["quantity"] == Decimal("1")
        assert result["unit_price"] == Decimal("3.99")
        assert result["extended_price"] == Decimal("3.99")
        assert result["regular_price"] == Decimal("4.29")
        assert result["sale_price"] == Decimal("3.99")
        assert result["loyalty_discount"] == Decimal("0.30")
        assert result["category_raw"] == "DAIRY"

    def test_weighted_item(self):
        raw = {
            "description": "KROGER DELI TURKEY BREAST",
            "quantity": 0.68,
            "basePrice": 9.99,
            "totalPrice": 6.79,
            "weight": 0.68,
            "weightUom": "LB",
            "department": "DELI",
        }
        result = _parse_item(raw)
        assert result["product_name_raw"] == "KROGER DELI TURKEY BREAST"
        assert result["upc"] is None
        assert result["quantity"] == Decimal("0.68")
        assert result["unit_price"] == Decimal("9.99")
        assert result["extended_price"] == Decimal("6.79")

    def test_missing_extended_price_computed(self):
        raw = {
            "description": "TEST ITEM",
            "quantity": 3,
            "basePrice": 2.49,
        }
        result = _parse_item(raw)
        assert result["extended_price"] == Decimal("2.49") * Decimal("3")

    def test_item_with_coupon(self):
        raw = {
            "description": "TIDE PODS 42CT",
            "upc": "0003700096223",
            "quantity": 1,
            "basePrice": 13.99,
            "totalPrice": 13.99,
            "couponAmount": 2.00,
        }
        result = _parse_item(raw)
        assert result["coupon_discount"] == Decimal("2.00")

    def test_missing_description_fallback(self):
        raw = {"basePrice": 1.00, "totalPrice": 1.00}
        result = _parse_item(raw)
        assert result["product_name_raw"] == "UNKNOWN ITEM"

    def test_alternative_field_names_product_name(self):
        raw = {
            "productName": "ALT NAME ITEM",
            "unitPrice": 5.00,
            "extendedAmount": 5.00,
            "qty": 1,
            "krogerProductId": "123456789",
            "category": "GROCERY",
        }
        result = _parse_item(raw)
        assert result["product_name_raw"] == "ALT NAME ITEM"
        assert result["unit_price"] == Decimal("5.00")
        assert result["extended_price"] == Decimal("5.00")
        assert result["upc"] == "123456789"
        assert result["category_raw"] == "GROCERY"

    def test_item_description_field_name(self):
        raw = {
            "itemDescription": "ITEM DESC FIELD",
            "price": 3.00,
            "lineTotal": 3.00,
        }
        result = _parse_item(raw)
        assert result["product_name_raw"] == "ITEM DESC FIELD"
        assert result["unit_price"] == Decimal("3.00")
        assert result["extended_price"] == Decimal("3.00")

    def test_null_optional_fields(self):
        raw = {
            "description": "BANANAS",
            "upc": "0000000004011",
            "quantity": 1,
            "basePrice": 0.59,
            "totalPrice": 0.59,
            "salePrice": None,
            "couponAmount": None,
            "plusCardSavings": None,
        }
        result = _parse_item(raw)
        assert result["sale_price"] is None
        assert result["coupon_discount"] is None
        assert result["loyalty_discount"] is None

    def test_upc_leading_zeros_stripped(self):
        raw = {
            "description": "TEST",
            "upc": "0000000004011",
            "basePrice": 1.00,
            "totalPrice": 1.00,
        }
        result = _parse_item(raw)
        assert result["upc"] == "4011"

    def test_upc_from_kroger_product_id(self):
        raw = {
            "description": "TEST",
            "krogerProductId": "987654321",
            "basePrice": 1.00,
            "totalPrice": 1.00,
        }
        result = _parse_item(raw)
        assert result["upc"] == "987654321"

    def test_description_whitespace_stripped(self):
        raw = {
            "description": "  EXTRA SPACES  ",
            "basePrice": 1.00,
            "totalPrice": 1.00,
        }
        result = _parse_item(raw)
        assert result["product_name_raw"] == "EXTRA SPACES"

    def test_promo_price_field(self):
        raw = {
            "description": "PROMO ITEM",
            "promoPrice": 2.99,
            "originalPrice": 4.99,
            "basePrice": 2.99,
            "totalPrice": 2.99,
        }
        result = _parse_item(raw)
        assert result["sale_price"] == Decimal("2.99")
        assert result["regular_price"] == Decimal("4.99")

    def test_loyalty_discount_from_fuel_points(self):
        raw = {
            "description": "FUEL DISC ITEM",
            "fuelPointsDiscount": 0.50,
            "basePrice": 3.00,
            "totalPrice": 3.00,
        }
        result = _parse_item(raw)
        assert result["loyalty_discount"] == Decimal("0.50")

    def test_multi_quantity_item(self):
        raw = {
            "description": "PRIVATE SELECTION PASTA",
            "quantity": 3,
            "basePrice": 2.49,
            "totalPrice": 7.47,
            "department": "GROCERY",
        }
        result = _parse_item(raw)
        assert result["quantity"] == Decimal("3")
        assert result["unit_price"] == Decimal("2.49")
        assert result["extended_price"] == Decimal("7.47")

    def test_aisle_as_category(self):
        raw = {
            "description": "AISLE ITEM",
            "aisle": "FROZEN FOODS",
            "basePrice": 4.00,
            "totalPrice": 4.00,
        }
        result = _parse_item(raw)
        assert result["category_raw"] == "FROZEN FOODS"


class TestParseKrogerReceipt:
    def test_full_receipt(self, kroger_receipt_data):
        raw = RawReceipt(
            receipt_id="KR-2026-0312-4471",
            purchase_date="2026-03-12T16:45:00Z",
            store_number="00357",
            raw_data=kroger_receipt_data,
        )
        result = parse_kroger_receipt(raw)

        assert result["receipt_id"] == "KR-2026-0312-4471"
        assert result["purchase_date"] == "2026-03-12T16:45:00Z"
        assert result["total"] == Decimal("94.17")
        assert result["subtotal"] == Decimal("78.47")
        assert result["tax"] == Decimal("5.50")
        assert result["savings_total"] == Decimal("15.30")

        # Should have 8 items (voided + returned items excluded)
        assert len(result["items"]) == 8

        # Verify first item
        milk = result["items"][0]
        assert milk["product_name_raw"] == "KROGER WHOLE MILK GAL"
        assert milk["upc"] == "1111041700"

    def test_voided_items_excluded(self, kroger_receipt_data):
        raw = RawReceipt(
            receipt_id="KR-2026-0312-4471",
            purchase_date="2026-03-12",
            raw_data=kroger_receipt_data,
        )
        result = parse_kroger_receipt(raw)

        item_names = [i["product_name_raw"] for i in result["items"]]
        assert "VOIDED DORITOS NACHO" not in item_names

    def test_returned_items_excluded(self, kroger_receipt_data):
        raw = RawReceipt(
            receipt_id="KR-2026-0312-4471",
            purchase_date="2026-03-12",
            raw_data=kroger_receipt_data,
        )
        result = parse_kroger_receipt(raw)

        item_names = [i["product_name_raw"] for i in result["items"]]
        assert "RETURNED GATORADE 8PK" not in item_names

    def test_return_flag_items_excluded(self):
        data = {
            "detail": {
                "items": [
                    {
                        "description": "NORMAL ITEM",
                        "basePrice": 5.00,
                        "totalPrice": 5.00,
                    },
                    {
                        "description": "RETURNED VIA FLAG",
                        "basePrice": 3.00,
                        "totalPrice": 3.00,
                        "returnFlag": True,
                    },
                    {
                        "description": "IS RETURN ITEM",
                        "basePrice": 2.00,
                        "totalPrice": 2.00,
                        "isReturn": True,
                    },
                ],
                "total": 5.00,
            }
        }
        raw = RawReceipt(
            receipt_id="RET-001",
            purchase_date="2026-03-12",
            raw_data=data,
        )
        result = parse_kroger_receipt(raw)
        assert len(result["items"]) == 1
        assert result["items"][0]["product_name_raw"] == "NORMAL ITEM"

    def test_empty_receipt(self):
        raw = RawReceipt(
            receipt_id="EMPTY-001",
            purchase_date="2026-03-12",
            raw_data={"detail": {"items": [], "total": 0}},
        )
        result = parse_kroger_receipt(raw)
        assert result["items"] == []
        assert result["total"] == Decimal("0")

    def test_receipt_with_no_detail(self):
        raw = RawReceipt(
            receipt_id="NO-DETAIL-001",
            purchase_date="2026-03-12",
            raw_data={"total": 50.00},
        )
        result = parse_kroger_receipt(raw)
        assert result["items"] == []
        assert result["total"] == Decimal("50.00")

    def test_raw_data_preserved(self, kroger_receipt_data):
        raw = RawReceipt(
            receipt_id="KR-2026-0312-4471",
            purchase_date="2026-03-12",
            raw_data=kroger_receipt_data,
        )
        result = parse_kroger_receipt(raw)
        assert result["raw_data"] is kroger_receipt_data

    def test_alternative_total_field_names(self):
        raw = RawReceipt(
            receipt_id="ALT-001",
            purchase_date="2026-03-12",
            raw_data={
                "orderTotal": 42.00,
                "subTotal": 35.00,
                "salesTax": 3.50,
                "youSaved": 5.00,
                "detail": {"items": []},
            },
        )
        result = parse_kroger_receipt(raw)
        assert result["total"] == Decimal("42.00")
        assert result["subtotal"] == Decimal("35.00")
        assert result["tax"] == Decimal("3.50")
        assert result["savings_total"] == Decimal("5.00")

    def test_receipt_items_alternative_key(self):
        data = {
            "detail": {
                "receiptItems": [
                    {
                        "description": "ALT KEY ITEM",
                        "basePrice": 3.00,
                        "totalPrice": 3.00,
                    }
                ],
                "total": 3.00,
            }
        }
        raw = RawReceipt(
            receipt_id="ALT-KEY-001",
            purchase_date="2026-03-12",
            raw_data=data,
        )
        result = parse_kroger_receipt(raw)
        assert len(result["items"]) == 1
        assert result["items"][0]["product_name_raw"] == "ALT KEY ITEM"

    def test_source_url_preserved(self):
        raw = RawReceipt(
            receipt_id="URL-001",
            purchase_date="2026-03-12",
            raw_data={"detail": {"items": [], "total": 0}},
            source_url="https://www.kroger.com/atlas/v1/receipt/api?orderId=URL-001",
        )
        result = parse_kroger_receipt(raw)
        assert result["source_url"] == "https://www.kroger.com/atlas/v1/receipt/api?orderId=URL-001"

    def test_weighted_items_in_full_receipt(self, kroger_receipt_data):
        raw = RawReceipt(
            receipt_id="KR-2026-0312-4471",
            purchase_date="2026-03-12",
            raw_data=kroger_receipt_data,
        )
        result = parse_kroger_receipt(raw)

        # Find the weighted turkey item
        turkey = next(i for i in result["items"] if "TURKEY" in i["product_name_raw"])
        assert turkey["quantity"] == Decimal("0.68")
        assert turkey["unit_price"] == Decimal("9.99")
        assert turkey["extended_price"] == Decimal("6.79")

    def test_grand_total_field(self):
        raw = RawReceipt(
            receipt_id="GT-001",
            purchase_date="2026-03-12",
            raw_data={"grandTotal": 99.99, "detail": {"items": []}},
        )
        result = parse_kroger_receipt(raw)
        assert result["total"] == Decimal("99.99")
