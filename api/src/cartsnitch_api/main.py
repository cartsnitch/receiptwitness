"""FastAPI app factory for CartSnitch API Gateway."""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from cartsnitch_api.auth.routes import router as auth_router
from cartsnitch_api.middleware.cors import add_cors_middleware
from cartsnitch_api.middleware.error_handler import add_error_handlers, add_error_monitor_middleware
from cartsnitch_api.middleware.rate_limit import add_rate_limit_middleware
from cartsnitch_api.routes.alerts import router as alerts_router
from cartsnitch_api.routes.coupons import router as coupons_router
from cartsnitch_api.routes.health import router as health_router
from cartsnitch_api.routes.prices import router as prices_router
from cartsnitch_api.routes.products import router as products_router
from cartsnitch_api.routes.public import router as public_router
from cartsnitch_api.routes.purchases import router as purchases_router
from cartsnitch_api.routes.scraping import router as scraping_router
from cartsnitch_api.routes.shopping import router as shopping_router
from cartsnitch_api.routes.stores import router as stores_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # TODO: initialize DB session pool, Redis connection, service clients
    yield
    # TODO: cleanup connections


def create_app() -> FastAPI:
    app = FastAPI(
        title="CartSnitch API",
        description="Grocery price tracking and shrinkflation detection API",
        version="0.1.0",
        lifespan=lifespan,
    )

    # Middleware (order matters — outermost first)
    add_cors_middleware(app)
    add_error_monitor_middleware(app)
    add_rate_limit_middleware(app)

    # Exception handlers
    add_error_handlers(app)

    # Routers
    app.include_router(health_router)
    app.include_router(auth_router)
    app.include_router(stores_router)
    app.include_router(purchases_router)
    app.include_router(products_router)
    app.include_router(prices_router)
    app.include_router(coupons_router)
    app.include_router(shopping_router)
    app.include_router(alerts_router)
    app.include_router(scraping_router)
    app.include_router(public_router)

    return app


app = create_app()
