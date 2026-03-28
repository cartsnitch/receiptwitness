"""Tests for the Target receipt parser."""

from decimal import Decimal

from receiptwitness.parsers.target import _parse_item, _to_decimal, parse_target_receipt
from receiptwitness.scrapers.base import RawReceipt


class TestToDecimal:
    def test_from_int(self):
        assert _to_decimal(42) == Decimal("42")

    def test_from_float(self):
        assert _to_decimal(3.89) == Decimal("3.89")

    def test_from_string(self):
        assert _to_decimal("8.99") == Decimal("8.99")

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
            "department": "GROCERY",
        }
        result = _parse_item(raw)
        assert result["product_name_raw"] == "GOOD & GATHER WHOLE MILK GAL"
        assert result["upc"] == "85239100123"
        assert result["quantity"] == Decimal("1")
        assert result["unit_price"] == Decimal("3.89")
        assert result["extended_price"] == Decimal("3.89")
        assert result["regular_price"] == Decimal("4.19")
        assert result["sale_price"] == Decimal("3.89")
        assert result["loyalty_discount"] == Decimal("0.30")
        assert result["category_raw"] == "GROCERY"

    def test_weighted_item(self):
        raw = {
            "description": "DELI SLICED TURKEY BREAST",
            "quantity": 0.72,
            "unitPrice": 10.99,
            "totalPrice": 7.91,
            "weight": 0.72,
            "weightUom": "LB",
            "department": "DELI",
        }
        result = _parse_item(raw)
        assert result["product_name_raw"] == "DELI SLICED TURKEY BREAST"
        assert result["upc"] is None
        assert result["quantity"] == Decimal("0.72")
        assert result["unit_price"] == Decimal("10.99")
        assert result["extended_price"] == Decimal("7.91")

    def test_missing_extended_price_computed(self):
        raw = {
            "description": "TEST ITEM",
            "quantity": 3,
            "unitPrice": 2.49,
        }
        result = _parse_item(raw)
        assert result["extended_price"] == Decimal("2.49") * Decimal("3")

    def test_item_with_coupon(self):
        raw = {
            "description": "TIDE PODS 42CT",
            "upc": "0003700096223",
            "quantity": 1,
            "unitPrice": 13.49,
            "totalPrice": 13.49,
            "couponDiscount": 2.50,
        }
        result = _parse_item(raw)
        assert result["coupon_discount"] == Decimal("2.50")

    def test_missing_description_fallback(self):
        raw = {"unitPrice": 1.00, "totalPrice": 1.00}
        result = _parse_item(raw)
        assert result["product_name_raw"] == "UNKNOWN ITEM"

    def test_alternative_field_names(self):
        raw = {
            "productName": "ALT NAME ITEM",
            "price": 5.00,
            "extendedPrice": 5.00,
            "qty": 1,
            "UPC": "123456789",
            "category": "FROZEN",
        }
        result = _parse_item(raw)
        assert result["product_name_raw"] == "ALT NAME ITEM"
        assert result["unit_price"] == Decimal("5.00")
        assert result["extended_price"] == Decimal("5.00")
        assert result["upc"] == "123456789"
        assert result["category_raw"] == "FROZEN"

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
            "unitPrice": 0.25,
            "totalPrice": 0.25,
            "circlePrice": None,
            "couponDiscount": None,
            "circleRewardsDiscount": None,
        }
        result = _parse_item(raw)
        assert result["sale_price"] is None
        assert result["coupon_discount"] is None
        assert result["loyalty_discount"] is None

    def test_upc_leading_zeros_stripped(self):
        raw = {
            "description": "TEST",
            "upc": "0000000004011",
            "unitPrice": 1.00,
            "totalPrice": 1.00,
        }
        result = _parse_item(raw)
        assert result["upc"] == "4011"

    def test_description_whitespace_stripped(self):
        raw = {
            "description": "  EXTRA SPACES  ",
            "unitPrice": 1.00,
            "totalPrice": 1.00,
        }
        result = _parse_item(raw)
        assert result["product_name_raw"] == "EXTRA SPACES"

    def test_circle_price_preferred_over_sale_price(self):
        raw = {
            "description": "CIRCLE ITEM",
            "circlePrice": 2.99,
            "salePrice": 3.49,
            "unitPrice": 2.99,
            "totalPrice": 2.99,
        }
        result = _parse_item(raw)
        assert result["sale_price"] == Decimal("2.99")

    def test_sale_price_fallback_when_no_circle_price(self):
        raw = {
            "description": "SALE ITEM",
            "salePrice": 3.49,
            "unitPrice": 3.49,
            "totalPrice": 3.49,
        }
        result = _parse_item(raw)
        assert result["sale_price"] == Decimal("3.49")

    def test_circle_rewards_discount(self):
        raw = {
            "description": "CIRCLE REWARDS ITEM",
            "circleRewardsDiscount": 1.50,
            "unitPrice": 5.00,
            "totalPrice": 5.00,
        }
        result = _parse_item(raw)
        assert result["loyalty_discount"] == Decimal("1.50")

    def test_circle_discount_fallback(self):
        raw = {
            "description": "CIRCLE DISC ITEM",
            "circleDiscount": 0.75,
            "unitPrice": 3.00,
            "totalPrice": 3.00,
        }
        result = _parse_item(raw)
        assert result["loyalty_discount"] == Decimal("0.75")

    def test_bogo_item(self):
        raw = {
            "description": "BOGO GOOD & GATHER PASTA",
            "upc": "0085239300456",
            "quantity": 2,
            "unitPrice": 1.79,
            "totalPrice": 1.79,
            "regularPrice": 1.79,
            "circlePrice": 0.895,
            "circleRewardsDiscount": 1.79,
            "promoDescription": "Buy 1 get 1 free",
            "department": "GROCERY",
        }
        result = _parse_item(raw)
        assert result["quantity"] == Decimal("2")
        assert result["unit_price"] == Decimal("1.79")
        assert result["extended_price"] == Decimal("1.79")
        assert result["sale_price"] == Decimal("0.895")
        assert result["loyalty_discount"] == Decimal("1.79")

    def test_multi_quantity_item(self):
        raw = {
            "description": "MARKET PANTRY EGGS",
            "quantity": 2,
            "unitPrice": 4.99,
            "totalPrice": 9.98,
            "department": "GROCERY",
        }
        result = _parse_item(raw)
        assert result["quantity"] == Decimal("2")
        assert result["unit_price"] == Decimal("4.99")
        assert result["extended_price"] == Decimal("9.98")

    def test_coupon_savings_field(self):
        raw = {
            "description": "COUPON ITEM",
            "couponSavings": 1.00,
            "unitPrice": 5.00,
            "totalPrice": 5.00,
        }
        result = _parse_item(raw)
        assert result["coupon_discount"] == Decimal("1.00")


class TestParseTargetReceipt:
    def test_full_receipt(self, target_receipt_data):
        raw = RawReceipt(
            receipt_id="TGT-2026-0315-7890",
            purchase_date="2026-03-15T11:23:00Z",
            store_number="2774",
            raw_data=target_receipt_data,
        )
        result = parse_target_receipt(raw)

        assert result["receipt_id"] == "TGT-2026-0315-7890"
        assert result["purchase_date"] == "2026-03-15T11:23:00Z"
        assert result["total"] == Decimal("83.21")
        assert result["subtotal"] == Decimal("78.32")
        assert result["tax"] == Decimal("4.89")
        assert result["savings_total"] == Decimal("11.45")

        # Should have 8 items (voided + returned items excluded)
        assert len(result["items"]) == 8

        # Verify first item
        milk = result["items"][0]
        assert milk["product_name_raw"] == "GOOD & GATHER WHOLE MILK GAL"
        assert milk["upc"] == "85239100123"

    def test_voided_items_excluded(self, target_receipt_data):
        raw = RawReceipt(
            receipt_id="TGT-2026-0315-7890",
            purchase_date="2026-03-15",
            raw_data=target_receipt_data,
        )
        result = parse_target_receipt(raw)

        item_names = [i["product_name_raw"] for i in result["items"]]
        assert "VOIDED COCA-COLA 12PK" not in item_names

    def test_returned_items_excluded(self, target_receipt_data):
        raw = RawReceipt(
            receipt_id="TGT-2026-0315-7890",
            purchase_date="2026-03-15",
            raw_data=target_receipt_data,
        )
        result = parse_target_receipt(raw)

        item_names = [i["product_name_raw"] for i in result["items"]]
        assert "RETURNED OLAY MOISTURIZER" not in item_names

    def test_return_flag_items_excluded(self):
        data = {
            "detail": {
                "items": [
                    {
                        "description": "NORMAL ITEM",
                        "unitPrice": 5.00,
                        "totalPrice": 5.00,
                    },
                    {
                        "description": "RETURNED VIA FLAG",
                        "unitPrice": 3.00,
                        "totalPrice": 3.00,
                        "returnFlag": True,
                    },
                    {
                        "description": "IS RETURN ITEM",
                        "unitPrice": 2.00,
                        "totalPrice": 2.00,
                        "isReturn": True,
                    },
                ],
                "total": 5.00,
            }
        }
        raw = RawReceipt(
            receipt_id="RET-001",
            purchase_date="2026-03-15",
            raw_data=data,
        )
        result = parse_target_receipt(raw)
        assert len(result["items"]) == 1
        assert result["items"][0]["product_name_raw"] == "NORMAL ITEM"

    def test_cancelled_items_excluded(self):
        data = {
            "detail": {
                "items": [
                    {
                        "description": "NORMAL ITEM",
                        "unitPrice": 5.00,
                        "totalPrice": 5.00,
                    },
                    {
                        "description": "CANCELLED ITEM",
                        "unitPrice": 3.00,
                        "totalPrice": 3.00,
                        "status": "CANCELLED",
                    },
                ],
                "total": 5.00,
            }
        }
        raw = RawReceipt(
            receipt_id="CAN-001",
            purchase_date="2026-03-15",
            raw_data=data,
        )
        result = parse_target_receipt(raw)
        assert len(result["items"]) == 1
        assert result["items"][0]["product_name_raw"] == "NORMAL ITEM"

    def test_empty_receipt(self):
        raw = RawReceipt(
            receipt_id="EMPTY-001",
            purchase_date="2026-03-15",
            raw_data={"detail": {"items": [], "total": 0}},
        )
        result = parse_target_receipt(raw)
        assert result["items"] == []
        assert result["total"] == Decimal("0")

    def test_receipt_with_no_detail(self):
        raw = RawReceipt(
            receipt_id="NO-DETAIL-001",
            purchase_date="2026-03-15",
            raw_data={"total": 50.00},
        )
        result = parse_target_receipt(raw)
        assert result["items"] == []
        assert result["total"] == Decimal("50.00")

    def test_raw_data_preserved(self, target_receipt_data):
        raw = RawReceipt(
            receipt_id="TGT-2026-0315-7890",
            purchase_date="2026-03-15",
            raw_data=target_receipt_data,
        )
        result = parse_target_receipt(raw)
        assert result["raw_data"] is target_receipt_data

    def test_alternative_total_field_names(self):
        raw = RawReceipt(
            receipt_id="ALT-001",
            purchase_date="2026-03-15",
            raw_data={
                "orderTotal": 42.00,
                "subTotal": 35.00,
                "salesTax": 3.50,
                "circleSavings": 5.00,
                "detail": {"items": []},
            },
        )
        result = parse_target_receipt(raw)
        assert result["total"] == Decimal("42.00")
        assert result["subtotal"] == Decimal("35.00")
        assert result["tax"] == Decimal("3.50")
        assert result["savings_total"] == Decimal("5.00")

    def test_receipt_items_alternative_key(self):
        data = {
            "detail": {
                "lineItems": [
                    {
                        "description": "ALT KEY ITEM",
                        "unitPrice": 3.00,
                        "totalPrice": 3.00,
                    }
                ],
                "total": 3.00,
            }
        }
        raw = RawReceipt(
            receipt_id="ALT-KEY-001",
            purchase_date="2026-03-15",
            raw_data=data,
        )
        result = parse_target_receipt(raw)
        assert len(result["items"]) == 1
        assert result["items"][0]["product_name_raw"] == "ALT KEY ITEM"

    def test_source_url_preserved(self):
        raw = RawReceipt(
            receipt_id="URL-001",
            purchase_date="2026-03-15",
            raw_data={"detail": {"items": [], "total": 0}},
            source_url="https://api.target.com/order_history/v1/orders/URL-001",
        )
        result = parse_target_receipt(raw)
        assert result["source_url"] == "https://api.target.com/order_history/v1/orders/URL-001"

    def test_weighted_items_in_full_receipt(self, target_receipt_data):
        raw = RawReceipt(
            receipt_id="TGT-2026-0315-7890",
            purchase_date="2026-03-15",
            raw_data=target_receipt_data,
        )
        result = parse_target_receipt(raw)

        # Find the weighted turkey item
        turkey = next(i for i in result["items"] if "TURKEY" in i["product_name_raw"])
        assert turkey["quantity"] == Decimal("0.72")
        assert turkey["unit_price"] == Decimal("10.99")
        assert turkey["extended_price"] == Decimal("7.91")

    def test_bogo_items_in_full_receipt(self, target_receipt_data):
        raw = RawReceipt(
            receipt_id="TGT-2026-0315-7890",
            purchase_date="2026-03-15",
            raw_data=target_receipt_data,
        )
        result = parse_target_receipt(raw)

        # Find the BOGO pasta item
        pasta = next(i for i in result["items"] if "BOGO" in i["product_name_raw"])
        assert pasta["quantity"] == Decimal("2")
        assert pasta["extended_price"] == Decimal("1.79")
        assert pasta["loyalty_discount"] == Decimal("1.79")

    def test_grand_total_field(self):
        raw = RawReceipt(
            receipt_id="GT-001",
            purchase_date="2026-03-15",
            raw_data={"grandTotal": 99.99, "detail": {"items": []}},
        )
        result = parse_target_receipt(raw)
        assert result["total"] == Decimal("99.99")
