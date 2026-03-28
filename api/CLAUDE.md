# CartSnitch API Gateway

## Project Context

CartSnitch is a self-hosted grocery price intelligence platform built as a polyrepo microservices architecture. This repo (`cartsnitch/api`) is the public-facing API gateway that serves the frontend and proxies requests to internal services.

**GitHub org:** github.com/cartsnitch
**Domain:** cartsnitch.com

### CartSnitch Services

| Repo | Service | Purpose |
|------|---------|---------|
| `cartsnitch/common` | — | Shared models, schemas, utilities |
| `cartsnitch/receiptwitness` | ReceiptWitness | Purchase data ingestion via retailer scrapers |
| `cartsnitch/api` | API Gateway | Frontend-facing REST API (this repo) |
| `cartsnitch/cartsnitch` | Frontend | React PWA (mobile-first) |
| `cartsnitch/stickershock` | StickerShock | Price increase detection & CPI comparison |
| `cartsnitch/shrinkray` | ShrinkRay | Shrinkflation monitoring |
| `cartsnitch/clipartist` | ClipArtist | Coupon/deal watching & shopping optimization |
| `cartsnitch/infra` | — | K8s manifests, Flux kustomizations |

### Architecture Decisions

- **Polyrepo:** Each service has its own repo, Dockerfile, CI/CD pipeline.
- **Shared DB:** One PostgreSQL cluster. This service reads from all tables for serving frontend queries. Models come from `cartsnitch-common`.
- **Inter-service comms:** REST to internal services, Redis pub/sub for event subscriptions.
- **Target scale:** 500–1,000 users initially.

## What This Service Does

The API Gateway is the single entry point for the frontend PWA and any external consumers. It:

1. **Handles user authentication** — registration, login, JWT token management
2. **Serves purchase/product/price data** — reads from the shared DB
3. **Proxies scraping operations** — forwards scrape triggers to ReceiptWitness
4. **Serves coupon/deal data** — reads from shared DB (written by ClipArtist)
5. **Serves alerts** — price increase alerts (StickerShock), shrinkflation alerts (ShrinkRay)
6. **Provides public data endpoints** — aggregate price trends for the transparency/shaming features

## Tech Stack

- Python 3.12+
- FastAPI (async)
- SQLAlchemy 2.0 (via `cartsnitch-common`, read-heavy)
- Pydantic v2 (request/response validation)
- python-jose or PyJWT (JWT auth)
- passlib + bcrypt (password hashing)
- httpx (async HTTP client for proxying to internal services)
- Redis (subscribe to events for websocket push, caching)
- uvicorn (ASGI server)

## Repo Structure

```
api/
├── CLAUDE.md
├── README.md
├── pyproject.toml
├── Dockerfile
├── docker-compose.yml
├── src/
│   └── cartsnitch_api/
│       ├── __init__.py
│       ├── config.py           # Service-specific settings
│       ├── main.py             # FastAPI app factory, lifespan, middleware
│       ├── auth/
│       │   ├── __init__.py
│       │   ├── jwt.py          # JWT creation/validation
│       │   ├── passwords.py    # Hashing, verification
│       │   ├── dependencies.py # FastAPI dependency injection (get_current_user)
│       │   └── routes.py       # /auth/register, /auth/login, /auth/refresh
│       ├── routes/
│       │   ├── __init__.py
│       │   ├── purchases.py    # Purchase history endpoints
│       │   ├── products.py     # Normalized product catalog
│       │   ├── prices.py       # Price history and trends
│       │   ├── coupons.py      # Active coupons and deals
│       │   ├── alerts.py       # Price increase / shrinkflation alerts
│       │   ├── stores.py       # Store info, user store account management
│       │   ├── scraping.py     # Proxy to ReceiptWitness (trigger scrape, status)
│       │   ├── shopping.py     # Optimized shopping list (proxy to ClipArtist)
│       │   ├── public.py       # Public price transparency endpoints (no auth)
│       │   └── health.py
│       ├── services/
│       │   ├── __init__.py
│       │   ├── receiptwitness.py   # HTTP client for ReceiptWitness internal API
│       │   ├── stickershock.py     # HTTP client for StickerShock internal API
│       │   ├── clipartist.py       # HTTP client for ClipArtist internal API
│       │   └── shrinkray.py        # HTTP client for ShrinkRay internal API
│       ├── middleware/
│       │   ├── __init__.py
│       │   ├── cors.py
│       │   └── rate_limit.py
│       └── cache.py            # Redis caching helpers
└── tests/
    ├── conftest.py
    ├── test_auth/
    ├── test_routes/
    └── test_services/
```

## API Endpoint Design

### Auth
- `POST /auth/register` — create account
- `POST /auth/login` — get JWT access + refresh tokens
- `POST /auth/refresh` — refresh access token
- `GET /auth/me` — current user profile

### Store Accounts
- `GET /stores` — list supported stores
- `GET /me/stores` — list user's connected store accounts + sync status
- `POST /me/stores/{store_slug}/connect` — initiate store connection flow
- `DELETE /me/stores/{store_slug}` — disconnect store account

### Purchases
- `GET /purchases` — list user's purchases (paginated, filterable by store/date)
- `GET /purchases/{id}` — purchase detail with line items
- `GET /purchases/stats` — spending summary (by store, by category, by period)

### Products
- `GET /products` — normalized product catalog (search, filter)
- `GET /products/{id}` — product detail with cross-store price comparison
- `GET /products/{id}/prices` — price history for a product across stores

### Prices
- `GET /prices/trends` — aggregate price trends (public-capable)
- `GET /prices/increases` — recent significant price increases
- `GET /prices/comparison` — compare specific items across stores

### Coupons
- `GET /coupons` — active coupons/deals (filterable by store)
- `GET /coupons/relevant` — coupons relevant to user's purchase history

### Shopping
- `POST /shopping/optimize` — input: shopping list → output: store-split + coupons
- `GET /shopping/lists` — user's saved shopping lists

### Alerts
- `GET /alerts` — user's price increase and shrinkflation alerts
- `PUT /alerts/settings` — configure alert thresholds

### Public (No Auth)
- `GET /public/trends/{product_id}` — public price trend for a product
- `GET /public/store-comparison` — public store-vs-store price comparison
- `GET /public/inflation` — price changes vs CPI baseline

### Scraping (Proxy to ReceiptWitness)
- `POST /scraping/{store_slug}/sync` — trigger a sync for the current user
- `GET /scraping/status` — sync status across all stores

## Authentication

- JWT-based auth with short-lived access tokens (15 min) and longer refresh tokens (7 days).
- Passwords hashed with bcrypt via passlib.
- All user-specific endpoints require a valid JWT in the `Authorization: Bearer` header.
- Public endpoints under `/public/` do not require auth.
- Internal service-to-service calls (ReceiptWitness, etc.) use a shared API key in the `X-Service-Key` header — not user JWTs.

## Development Workflow

- **Never push directly to main.** Always create feature branches and open PRs.
- Branch naming: `feature/<description>` or `fix/<description>`
- Use conventional commits: `feat:`, `fix:`, `refactor:`, `docs:`, `chore:`
- OpenAPI docs auto-generated at `/docs` (Swagger) and `/redoc`.
- Write tests for all routes. Use httpx.AsyncClient with FastAPI's TestClient pattern.

## Important Notes

- This service is read-heavy on the shared DB. Use async SQLAlchemy sessions.
- Consider Redis caching for expensive queries (price trends, product comparisons). Cache invalidation via Redis pub/sub events from other services.
- Rate limiting on public endpoints is important — these could get hammered if the price transparency features get attention.
- CORS must allow the frontend origin (cartsnitch.com and localhost for dev).
- The store connection flow is the trickiest UX challenge: the user needs to authenticate with each retailer, and we need to capture the resulting session. This likely involves a controlled Playwright browser session that the user can see/interact with, or an OAuth-like redirect flow if the retailer supports it (Kroger does for its public API, but not for purchase history access).
