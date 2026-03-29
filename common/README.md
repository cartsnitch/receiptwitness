# CartSnitch Common

Shared models, schemas, and utilities for CartSnitch services.

## Test Users

The following users are seeded by `cartsnitch-seed` and can be used for local development and UAT.

| Email | Password | Display Name | Notes |
|---|---|---|---|
| `uat@cartsnitch.com` | `CartSnitch-UAT-2026!` | UAT Tester | Primary UAT account. Use for regression testing in the CartSnitch frontend. Created by the seed runner via Better-Auth's bcrypt path — credentials work against the live auth service. Idempotent; re-running the seed skips this user if it already exists. |

### Running the Seed

```bash
# Install with seed dependencies
pip install -e "cartsnitch-common[seed]"

# Run (requires CARTSNITCH_DATABASE_URL_SYNC)
CARTSNITCH_DATABASE_URL_SYNC=postgresql://user:pass@localhost:5432/cartsnitch \
  cartsnitch-seed
```

### Architecture

- **Models** live in `src/cartsnitch_common/models/`
- **Alembic migrations** run via the `api` service (`api/alembic/`)
- **Seed runner** runs via `cartsnitch-seed` (installed as a package entry point)
