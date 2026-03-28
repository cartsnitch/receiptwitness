"""Verify all expected routes are present in the OpenAPI spec."""

import pytest
from httpx import ASGITransport, AsyncClient

from cartsnitch_api.main import app

EXPECTED_ROUTES = [
    # Auth (6)
    ("post", "/auth/register"),
    ("post", "/auth/login"),
    ("post", "/auth/refresh"),
    ("get", "/auth/me"),
    ("patch", "/auth/me"),
    ("delete", "/auth/me"),
    # Stores (4)
    ("get", "/stores"),
    ("get", "/me/stores"),
    ("post", "/me/stores/{store_slug}/connect"),
    ("delete", "/me/stores/{store_slug}"),
    # Purchases (3)
    ("get", "/purchases"),
    ("get", "/purchases/stats"),
    ("get", "/purchases/{purchase_id}"),
    # Products (3)
    ("get", "/products"),
    ("get", "/products/{product_id}"),
    ("get", "/products/{product_id}/prices"),
    # Prices (3)
    ("get", "/prices/trends"),
    ("get", "/prices/increases"),
    ("get", "/prices/comparison"),
    # Coupons (2)
    ("get", "/coupons"),
    ("get", "/coupons/relevant"),
    # Shopping (2)
    ("post", "/shopping/optimize"),
    ("get", "/shopping/lists"),
    # Alerts (3)
    ("get", "/alerts"),
    ("get", "/alerts/settings"),
    ("put", "/alerts/settings"),
    # Scraping (2)
    ("post", "/scraping/{store_slug}/sync"),
    ("get", "/scraping/status"),
    # Public (3)
    ("get", "/public/trends/{product_id}"),
    ("get", "/public/store-comparison"),
    ("get", "/public/inflation"),
    # Health (1)
    ("get", "/health"),
]


@pytest.mark.asyncio
async def test_all_routes_in_openapi():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/openapi.json")
        assert resp.status_code == 200
        spec = resp.json()
        paths = spec["paths"]

        registered = set()
        for path, methods in paths.items():
            for method in methods:
                if method in ("get", "post", "put", "delete", "patch"):
                    registered.add((method, path))

        missing = []
        for method, path in EXPECTED_ROUTES:
            if (method, path) not in registered:
                missing.append(f"{method.upper()} {path}")

        assert not missing, "Missing routes in OpenAPI spec:\n" + "\n".join(missing)


@pytest.mark.asyncio
async def test_route_count():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/openapi.json")
        spec = resp.json()
        paths = spec["paths"]

        count = 0
        for _path, methods in paths.items():
            for method in methods:
                if method in ("get", "post", "put", "delete", "patch"):
                    count += 1

        assert count == 33, f"Expected 33 routes, found {count}"
