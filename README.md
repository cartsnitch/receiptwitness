# ReceiptWitness

Purchase data ingestion service for CartSnitch. Authenticates with grocery retailer web portals (Meijer, Kroger, Target) via Playwright, scrapes purchase history, and writes structured records to the shared PostgreSQL database.

## Quick Start

```bash
# Install dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/ -v

# Local dev with Docker Compose
docker-compose up
```

## Architecture

- **Scrapers:** Playwright-based browser automation for each retailer
- **Parsers:** Converts raw receipt data to structured `Purchase` / `PurchaseItem` records
- **Database:** SQLAlchemy 2.0 async; models inlined under `src/receiptwitness/shared/`
- **Events:** Publishes `cartsnitch.receipts.ingested` to Redis after ingestion

## Branches

- `dev` — development, auto-deploys to dev cluster
- `uat` — user acceptance testing
- `main` — production, auto-deploys to prod cluster
