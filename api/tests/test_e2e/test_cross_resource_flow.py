"""E2E: Cross-resource flows — store connect → purchases → prices → coupons → alerts."""

import pytest


@pytest.mark.asyncio
class TestStoreConnectToPurchaseFlow:
    """Connect a store, then verify purchases and related data are accessible."""

    async def test_connect_store_then_list(self, client, seed_data):
        headers = seed_data["headers"]
        # Connect to Meijer
        resp = await client.post("/me/stores/meijer/connect", json={}, headers=headers)
        assert resp.status_code in (200, 201)

        # Verify store appears in user's connected stores
        stores = await client.get("/me/stores", headers=headers)
        assert stores.status_code == 200
        slugs = [s["store"]["slug"] for s in stores.json()]
        assert "meijer" in slugs

    async def test_disconnect_store(self, client, seed_data):
        headers = seed_data["headers"]
        await client.post("/me/stores/kroger/connect", json={}, headers=headers)
        resp = await client.delete("/me/stores/kroger", headers=headers)
        assert resp.status_code in (200, 204)

        # Verify store no longer in connected list
        stores = await client.get("/me/stores", headers=headers)
        slugs = [s["store"]["slug"] for s in stores.json()]
        assert "kroger" not in slugs


@pytest.mark.asyncio
class TestPurchaseToPriceFlow:
    """Verify purchase data links to price comparison data."""

    async def test_purchase_items_link_to_products(self, client, seed_data):
        """Items from purchases reference products that have price data."""
        headers = seed_data["headers"]
        purchase_id = str(seed_data["purchases"]["meijer_trip"].id)

        # Get purchase detail
        purchase = await client.get(f"/purchases/{purchase_id}", headers=headers)
        assert purchase.status_code == 200
        items = purchase.json()["line_items"]

        # Get product detail for an item that has a product_id
        product_ids = [li["product_id"] for li in items if li.get("product_id")]
        assert len(product_ids) >= 1

        for pid in product_ids:
            product = await client.get(f"/products/{pid}", headers=headers)
            assert product.status_code == 200
            assert len(product.json()["prices_by_store"]) >= 1


@pytest.mark.asyncio
class TestCouponFlow:
    """Verify coupon listing and relevance filtering."""

    async def test_list_all_coupons(self, client, seed_data):
        headers = seed_data["headers"]
        resp = await client.get("/coupons", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) >= 2
        descriptions = [c["description"] for c in data]
        assert any("Cheerios" in d for d in descriptions)

    async def test_filter_coupons_by_store(self, client, seed_data):
        headers = seed_data["headers"]
        meijer_id = str(seed_data["stores"]["meijer"].id)
        resp = await client.get("/coupons", params={"store_id": meijer_id}, headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert all(c["store_name"] == "Meijer" for c in data)

    async def test_relevant_coupons_for_user(self, client, seed_data):
        """User bought Cheerios, so the Cheerios coupon should be relevant."""
        headers = seed_data["headers"]
        resp = await client.get("/coupons/relevant", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) >= 1, "Expected at least one relevant coupon for user with purchases"
        descriptions = [c["description"] for c in data]
        assert any("Cheerios" in d for d in descriptions)


@pytest.mark.asyncio
class TestAlertFlow:
    """Verify alert listing with seeded data."""

    async def test_list_alerts(self, client, seed_data):
        """User bought Cheerios which has a shrinkflation event — may appear as alert."""
        headers = seed_data["headers"]
        resp = await client.get("/alerts", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        # If alerts are generated synchronously, verify shrinkflation alert content
        if len(data) > 0:
            alert_types = [a["alert_type"] for a in data]
            product_names = [a["product_name"] for a in data]
            assert any(t in ("shrinkflation", "price_increase") for t in alert_types)
            assert any("Cheerios" in name for name in product_names)

    async def test_alert_settings_default(self, client, seed_data):
        headers = seed_data["headers"]
        resp = await client.get("/alerts/settings", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "price_increase_threshold_pct" in data
        assert "shrinkflation_enabled" in data
