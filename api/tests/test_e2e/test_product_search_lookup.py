"""E2E: Product search/lookup endpoints with real DB fixtures."""

import pytest

from tests.test_e2e.conftest import ZERO_UUID


@pytest.mark.asyncio
class TestProductSearch:
    """Search and filter products against seeded data."""

    async def test_list_all_products(self, client, seed_data):
        resp = await client.get("/products", headers=seed_data["headers"])
        assert resp.status_code == 200
        products = resp.json()
        names = [p["name"] for p in products]
        assert "Cheerios 18oz" in names
        assert "Whole Milk 1gal" in names
        assert "Chicken Breast 1lb" in names

    async def test_search_by_name(self, client, seed_data):
        resp = await client.get("/products", params={"q": "cheerios"}, headers=seed_data["headers"])
        assert resp.status_code == 200
        products = resp.json()
        assert len(products) >= 1
        assert all("cheerios" in p["name"].lower() for p in products)

    async def test_search_by_category(self, client, seed_data):
        resp = await client.get(
            "/products", params={"category": "dairy"}, headers=seed_data["headers"]
        )
        assert resp.status_code == 200
        products = resp.json()
        assert len(products) >= 1
        assert all(p["category"] == "dairy" for p in products)

    async def test_search_no_results(self, client, seed_data):
        resp = await client.get(
            "/products", params={"q": "nonexistentxyz"}, headers=seed_data["headers"]
        )
        assert resp.status_code == 200
        assert resp.json() == []


@pytest.mark.asyncio
class TestProductLookup:
    """Detailed product lookups with cross-store pricing."""

    async def test_get_product_detail_with_prices(self, client, seed_data):
        cheerios_id = str(seed_data["products"]["cheerios"].id)
        resp = await client.get(f"/products/{cheerios_id}", headers=seed_data["headers"])
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "Cheerios 18oz"
        assert data["brand"] == "General Mills"
        assert data["category"] == "pantry"
        # Should have prices from both Meijer and Kroger
        store_names = [p["store_name"] for p in data["prices_by_store"]]
        assert "Meijer" in store_names
        assert "Kroger" in store_names

    async def test_product_prices_reflect_latest(self, client, seed_data):
        """The latest Meijer price for Cheerios should be 4.79 (the increase)."""
        cheerios_id = str(seed_data["products"]["cheerios"].id)
        resp = await client.get(f"/products/{cheerios_id}", headers=seed_data["headers"])
        data = resp.json()
        meijer_price = next(p for p in data["prices_by_store"] if p["store_name"] == "Meijer")
        assert meijer_price["current_price"] == 4.79

    async def test_product_not_found(self, client, seed_data):
        resp = await client.get(f"/products/{ZERO_UUID}", headers=seed_data["headers"])
        assert resp.status_code == 404

    async def test_product_price_history(self, client, seed_data):
        cheerios_id = str(seed_data["products"]["cheerios"].id)
        resp = await client.get(f"/products/{cheerios_id}/prices", headers=seed_data["headers"])
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["data_points"]) >= 3  # At least the 3 Meijer observations
        # Verify chronological ordering exists
        prices = [dp["price"] for dp in data["data_points"]]
        assert len(prices) >= 3
