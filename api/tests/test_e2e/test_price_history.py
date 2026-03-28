"""E2E: Price history queries returning correct data."""

import pytest


@pytest.mark.asyncio
class TestPriceTrends:
    """Verify price trend aggregation against seeded history."""

    async def test_trends_returns_all_products(self, client, seed_data):
        resp = await client.get("/prices/trends", headers=seed_data["headers"])
        assert resp.status_code == 200
        data = resp.json()
        product_names = [t["product_name"] for t in data]
        assert "Cheerios 18oz" in product_names
        assert "Whole Milk 1gal" in product_names

    async def test_trends_filter_by_category(self, client, seed_data):
        resp = await client.get(
            "/prices/trends", params={"category": "dairy"}, headers=seed_data["headers"]
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) >= 1
        # Only dairy products should appear
        for trend in data:
            assert trend["product_name"] == "Whole Milk 1gal"

    async def test_trends_contain_data_points(self, client, seed_data):
        resp = await client.get("/prices/trends", headers=seed_data["headers"])
        data = resp.json()
        cheerios_trend = next(t for t in data if t["product_name"] == "Cheerios 18oz")
        assert len(cheerios_trend["data_points"]) >= 3


@pytest.mark.asyncio
class TestPriceIncreases:
    """Detect price increases from seeded price history."""

    async def test_increases_detected(self, client, seed_data):
        resp = await client.get("/prices/increases", headers=seed_data["headers"])
        assert resp.status_code == 200
        data = resp.json()
        # Cheerios at Meijer went from 3.99 → 4.29 → 4.79
        cheerios_increases = [inc for inc in data if inc["product_name"] == "Cheerios 18oz"]
        assert len(cheerios_increases) >= 1
        # Verify the increase data makes sense
        for inc in cheerios_increases:
            assert inc["new_price"] > inc["old_price"]
            assert inc["increase_pct"] > 0
            assert inc["store_name"] == "Meijer"

    async def test_stable_prices_not_flagged(self, client, seed_data):
        """Kroger Cheerios price is stable at $4.49 — should not appear as increase."""
        resp = await client.get("/prices/increases", headers=seed_data["headers"])
        data = resp.json()
        kroger_increases = [
            inc
            for inc in data
            if inc["product_name"] == "Cheerios 18oz" and inc["store_name"] == "Kroger"
        ]
        assert len(kroger_increases) == 0


@pytest.mark.asyncio
class TestPriceComparison:
    """Compare prices across stores for specific products."""

    async def test_compare_cheerios_across_stores(self, client, seed_data):
        cheerios_id = str(seed_data["products"]["cheerios"].id)
        resp = await client.get(
            "/prices/comparison",
            params={"product_ids": cheerios_id},
            headers=seed_data["headers"],
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) >= 1
        cheerios_cmp = data[0]
        assert cheerios_cmp["product_name"] == "Cheerios 18oz"
        store_names = [p["store_name"] for p in cheerios_cmp["prices"]]
        assert "Meijer" in store_names
        assert "Kroger" in store_names

    async def test_compare_requires_product_ids(self, client, seed_data):
        """product_ids is required — omitting it must return 422."""
        resp = await client.get("/prices/comparison", headers=seed_data["headers"])
        assert resp.status_code == 422

    async def test_compare_multiple_products(self, client, seed_data):
        cheerios_id = str(seed_data["products"]["cheerios"].id)
        milk_id = str(seed_data["products"]["milk"].id)
        resp = await client.get(
            "/prices/comparison",
            params=[("product_ids", cheerios_id), ("product_ids", milk_id)],
            headers=seed_data["headers"],
        )
        assert resp.status_code == 200
        data = resp.json()
        names = [c["product_name"] for c in data]
        assert "Cheerios 18oz" in names
        assert "Whole Milk 1gal" in names
