# ReceiptWitness — CartSnitch Receipt Ingestion Service

## Project Context

CartSnitch is a self-hosted grocery price intelligence platform built as a polyrepo microservices architecture. This repo (`cartsnitch/receiptwitness`) is the receipt/purchase history ingestion service.

**GitHub org:** github.com/cartsnitch
**Domain:** cartsnitch.com

### CartSnitch Services

| Repo | Service | Purpose |
|------|---------|---------|
| `cartsnitch/common` | — | Shared models, schemas, utilities |
| `cartsnitch/receiptwitness` | ReceiptWitness | Purchase data ingestion via retailer scrapers (this repo) |
| `cartsnitch/api` | API Gateway | Frontend-facing REST API |
| `cartsnitch/cartsnitch` | Frontend | React PWA (mobile-first) |
| `cartsnitch/stickershock` | StickerShock | Price increase detection & CPI comparison |
| `cartsnitch/shrinkray` | ShrinkRay | Shrinkflation monitoring |
| `cartsnitch/clipartist` | ClipArtist | Coupon/deal watching & shopping optimization |
| `cartsnitch/infra` | — | K8s manifests, Flux kustomizations |

### Architecture Decisions

- **Polyrepo:** Each service has its own repo, Dockerfile, CI/CD pipeline.
- **Shared DB:** One PostgreSQL cluster. This service writes to `purchases`, `purchase_items`, `price_history` tables. Models come from `cartsnitch-common`.
- **Inter-service comms:** REST (synchronous) + Redis pub/sub (async events).
- **Target scale:** 500–1,000 users. Each user has their own authenticated sessions to up to 3 retailers.

## What This Service Does

ReceiptWitness authenticates with grocery retailer web portals using per-user sessions, scrapes purchase history / receipt data, parses it into structured records, and writes it to the shared database. After ingestion, it publishes a `cartsnitch.receipts.ingested` event so downstream services (StickerShock, ClipArtist) can react.

### Target Retailers (MVP)

#### Meijer (mPerks)
- **Auth:** No public API. Session cookie-based auth on mperks.meijer.com.
- **Receipt location:** meijer.com/mperks/receipts-savings.html (or underlying XHR endpoints)
- **Approach:** Playwright login → capture session → hit receipt XHR endpoints directly. Map the API calls the frontend makes via browser dev tools network tab.
- **Prior art:** `dapperfu/python_Meijer` (requires MITM proxy for auth — avoid this pattern, prefer direct browser automation).
- **Data available:** Digital receipts appear ~15 minutes after purchase if mPerks ID was used at checkout. Includes item names, prices, discounts, savings.

#### Kroger
- **Auth:** No public API for purchase history (that's behind Partner API). Session cookie-based auth on kroger.com.
- **Receipt location:** kroger.com/mypurchases
- **Approach:** Playwright login → scrape purchase history pages or intercept XHR endpoints.
- **Anti-bot:** Kroger uses Akamai Bot Manager. Aggressive headless browser detection. Need Playwright stealth, realistic fingerprinting, human-like interaction pacing.
- **Prior art:** `phyllis-vance/KrogerScrape` (.NET, old), `callaginn/kroger-sweeper` (Puppeteer/Node), `ThermoMan/Get-Kroger-Grocery-List` (Greasemonkey userscript).
- **Kroger public API:** Free developer account at developer.kroger.com provides product catalog data (`product.compact` scope) — useful for enriching scraped receipt data with UPCs, categories, product images. NOT useful for purchase history.
- **Data available:** Purchase history tied to Kroger Plus loyalty card. Shows items, prices, quantities.

#### Target (Circle)
- **Auth:** Session-based auth on target.com.
- **Receipt location:** target.com account → Orders → In-store tab, or target.com/account/orders
- **Approach:** Playwright login → scrape in-store purchase history.
- **Data available:** ~1 year of history if user paid with a linked card, used the Target app wallet, or entered their Target Circle phone number at checkout. Includes item names, prices.

## Tech Stack

- Python 3.12+
- Playwright (Python async API) for headless browser automation
- FastAPI (lightweight internal API for triggering scrapes, health checks, status)
- SQLAlchemy 2.0 (via `cartsnitch-common`)
- Redis (pub/sub event publishing)
- APScheduler or Celery (for scheduled scraping jobs)
- cryptography / Fernet (encrypting stored session data)

## Repo Structure

```
receiptwitness/
├── CLAUDE.md
├── README.md
├── pyproject.toml
├── Dockerfile                  # Playwright + Chromium headless
├── docker-compose.yml          # Local dev (Postgres, Redis, this service)
├── src/
│   └── receiptwitness/
│       ├── __init__.py
│       ├── config.py           # Service-specific settings
│       ├── main.py             # FastAPI app + scheduler bootstrap
│       ├── scrapers/
│       │   ├── __init__.py
│       │   ├── base.py         # Abstract BaseScraper class
│       │   ├── meijer.py       # Meijer/mPerks scraper
│       │   ├── kroger.py       # Kroger scraper
│       │   └── target.py       # Target/Circle scraper
│       ├── parsers/
│       │   ├── __init__.py
│       │   ├── meijer.py       # Parse raw Meijer receipt data → PurchaseItem records
│       │   ├── kroger.py
│       │   └── target.py
│       ├── session/
│       │   ├── __init__.py
│       │   ├── manager.py      # Session storage, retrieval, refresh logic
│       │   └── encryption.py   # Encrypt/decrypt session cookies at rest
│       ├── scheduler.py        # Scrape scheduling (per-user cron jobs)
│       ├── events.py           # Publish receipt.ingested events to Redis
│       ├── api/
│       │   ├── __init__.py
│       │   ├── routes.py       # Internal API: trigger scrape, check status, health
│       │   └── auth.py         # Internal service auth (API key or JWT)
│       └── enrichment.py       # Optional: enrich receipt data via Kroger public API
└── tests/
    ├── conftest.py
    ├── fixtures/               # Sample receipt HTML/JSON for testing parsers
    │   ├── meijer_receipt.json
    │   ├── kroger_receipt.html
    │   └── target_receipt.html
    ├── test_scrapers/
    ├── test_parsers/
    └── test_session/
```

## Scraper Architecture

### Base Scraper Pattern

```python
class BaseScraper(ABC):
    """All retailer scrapers implement this interface."""

    @abstractmethod
    async def login(self, credentials: UserStoreAccount) -> SessionData: ...

    @abstractmethod
    async def check_session(self, session: SessionData) -> bool: ...

    @abstractmethod
    async def scrape_receipts(self, session: SessionData, since: datetime | None) -> list[RawReceipt]: ...

    @abstractmethod
    def parse_receipt(self, raw: RawReceipt) -> tuple[Purchase, list[PurchaseItem]]: ...
```

### Scraping Flow

1. **Scheduler fires** for a user+store combination
2. **Load session** from `user_store_accounts` table (encrypted)
3. **Check session validity** — quick lightweight request to verify auth
4. **If expired:** launch Playwright, re-authenticate, save new session
5. **Scrape receipts** since `last_sync_at` timestamp
6. **Parse** raw data into `Purchase` and `PurchaseItem` records
7. **Deduplicate** — skip receipts already in DB (match on `receipt_id` per store)
8. **Write to DB** — insert new purchases and items
9. **Derive price_history** entries from purchase_items
10. **Publish event** — `cartsnitch.receipts.ingested` to Redis
11. **Update** `user_store_accounts.last_sync_at`

### Session Management

- Sessions (cookies, tokens) are encrypted at rest using Fernet symmetric encryption.
- The encryption key is provided via environment variable, not stored in the DB.
- Sessions are stored in the `user_store_accounts` table as encrypted JSONB.
- Each scrape attempt first checks if the existing session is valid before launching a full Playwright browser instance.
- When a session expires, the service needs the user's stored credentials OR a manual re-auth flow (the user logs in via the frontend, and we capture the session).

### Anti-Bot Considerations

- Use `playwright-stealth` or equivalent to mask automation signals.
- Set realistic viewport sizes, user agents, and locale settings.
- Add human-like delays between page navigations (randomized 1-5 seconds).
- For Kroger specifically (Akamai Bot Manager): may need to use non-headless mode on initial auth, or route through a persistent browser profile that has established trust.
- Rate limit scraping: no more than 1 scrape per user per store per hour. Default cadence: once daily.
- Store and reuse browser profiles/cookies to minimize fresh logins.

### Dockerfile

The Dockerfile must include Playwright and Chromium. Base image pattern:

```dockerfile
FROM mcr.microsoft.com/playwright/python:v1.49.0-noble
# Install deps, copy code, etc.
```

This is a large image (~2GB) due to Chromium. Consider multi-stage builds if the final image can be slimmed down.

## Internal API Endpoints

This service exposes a lightweight internal API (not public-facing):

- `GET /health` — health check
- `GET /status/{user_id}` — sync status per store for a user
- `POST /scrape/{user_id}/{store_slug}` — trigger an immediate scrape for a user+store
- `POST /scrape/{user_id}/all` — trigger scrape across all configured stores
- `GET /sessions/{user_id}` — list configured store sessions and their status

The public-facing API gateway (`cartsnitch/api`) proxies user-facing requests to this service's internal API.

## Events Published

### `cartsnitch.receipts.ingested`

Published after new receipt data is successfully written to the DB.

```json
{
  "event_type": "cartsnitch.receipts.ingested",
  "timestamp": "2026-03-15T12:00:00Z",
  "service": "receiptwitness",
  "payload": {
    "user_id": "uuid",
    "store_slug": "meijer",
    "purchase_id": "uuid",
    "purchase_date": "2026-03-14",
    "item_count": 23,
    "total": 87.42
  }
}
```

## Development Workflow

- **Never push directly to main.** Always create feature branches and open PRs.
- Branch naming: `feature/<store>/<description>` or `fix/<description>`
- Use conventional commits: `feat:`, `fix:`, `refactor:`, `docs:`, `chore:`
- Test parsers with fixture data (sample receipts in `tests/fixtures/`). Scraper integration tests require real credentials and should be tagged/skipped in CI.
- Local dev: `docker-compose up` starts Postgres, Redis, and the service. Playwright runs inside the container.

## Important Notes

- The Playwright container image is large. On K8s, consider using a dedicated node or tolerating scheduling delays.
- Each user needs their own authenticated sessions. At 1,000 users × 3 stores = 3,000 sessions to manage. Sessions expire at different rates per retailer.
- Scraping must be respectful: randomized intervals, rate limiting, no parallel scraping of the same store for the same user.
- Receipt data structure varies significantly between retailers. The parsers must be robust and handle edge cases (returns, voided items, weighted produce, BOGO items, coupon stacking).
- Kroger's public API (`product.compact` scope) can be used to enrich scraped data with UPCs and product metadata after receipt parsing. This is optional but improves product normalization downstream.
- Store credentials for users should ideally NOT be stored by CartSnitch. Prefer a flow where the user authenticates in a controlled browser session, and we capture/store only the resulting session cookies. If credential storage is necessary, use strong encryption and make the tradeoffs clear to users.
