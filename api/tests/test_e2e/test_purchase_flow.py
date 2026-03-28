"""E2E: Purchase listing, detail, and stats against real DB fixtures."""

import pytest

from tests.test_e2e.conftest import ZERO_UUID


@pytest.mark.asyncio
class TestPurchaseList:
    """List and filter a user's purchases."""

    async def test_list_user_purchases(self, client, seed_data):
        resp = await client.get("/purchases", headers=seed_data["headers"])
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) >= 2
        store_names = [p["store_name"] for p in data]
        assert "Meijer" in store_names
        assert "Kroger" in store_names

    async def test_filter_purchases_by_store(self, client, seed_data):
        meijer_id = str(seed_data["stores"]["meijer"].id)
        resp = await client.get(
            "/purchases", params={"store_id": meijer_id}, headers=seed_data["headers"]
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) >= 1
        assert all(p["store_name"] == "Meijer" for p in data)

    async def test_purchases_require_auth(self, client, seed_data):
        resp = await client.get("/purchases")
        assert resp.status_code in (401, 403)


@pytest.mark.asyncio
class TestPurchaseDetail:
    """Retrieve individual purchase with line items."""

    async def test_get_purchase_detail(self, client, seed_data):
        purchase_id = str(seed_data["purchases"]["meijer_trip"].id)
        resp = await client.get(f"/purchases/{purchase_id}", headers=seed_data["headers"])
        assert resp.status_code == 200
        data = resp.json()
        assert data["store_name"] == "Meijer"
        assert data["total"] == 23.45
        assert len(data["line_items"]) == 2
        item_names = [li["name"] for li in data["line_items"]]
        assert "Cheerios 18oz Box" in item_names
        assert "Meijer Whole Milk 1gal" in item_names

    async def test_line_item_amounts_correct(self, client, seed_data):
        purchase_id = str(seed_data["purchases"]["meijer_trip"].id)
        resp = await client.get(f"/purchases/{purchase_id}", headers=seed_data["headers"])
        data = resp.json()
        cheerios_item = next(li for li in data["line_items"] if "Cheerios" in li["name"])
        assert cheerios_item["unit_price"] == 4.79
        assert cheerios_item["quantity"] == 1.0
        assert cheerios_item["total_price"] == 4.79

    async def test_purchase_not_found(self, client, seed_data):
        resp = await client.get(
            f"/purchases/{ZERO_UUID}",
            headers=seed_data["headers"],
        )
        assert resp.status_code == 404


@pytest.mark.asyncio
class TestPurchaseStats:
    """Verify spending aggregation across purchases."""

    async def test_purchase_stats_totals(self, client, seed_data):
        resp = await client.get("/purchases/stats", headers=seed_data["headers"])
        assert resp.status_code == 200
        data = resp.json()
        assert data["purchase_count"] == 2
        # 23.45 + 15.78 = 39.23
        assert abs(data["total_spent"] - 39.23) < 0.01

    async def test_purchase_stats_by_store(self, client, seed_data):
        resp = await client.get("/purchases/stats", headers=seed_data["headers"])
        data = resp.json()
        assert "Meijer" in data["by_store"]
        assert "Kroger" in data["by_store"]
        assert abs(data["by_store"]["Meijer"] - 23.45) < 0.01
        assert abs(data["by_store"]["Kroger"] - 15.78) < 0.01
