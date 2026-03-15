# CartSnitch Frontend

## Project Context

CartSnitch is a self-hosted grocery price intelligence platform built as a polyrepo microservices architecture. This repo (`cartsnitch/cartsnitch`) is the mobile-first Progressive Web App — the flagship repo and primary user interface.

**GitHub org:** github.com/cartsnitch
**Domain:** cartsnitch.com

### CartSnitch Services

| Repo | Service | Purpose |
|------|---------|---------|
| `cartsnitch/common` | — | Shared models, schemas, utilities |
| `cartsnitch/receiptwitness` | ReceiptWitness | Purchase data ingestion via retailer scrapers |
| `cartsnitch/api` | API Gateway | Frontend-facing REST API |
| `cartsnitch/cartsnitch` | Frontend | React PWA, mobile-first (this repo) |
| `cartsnitch/stickershock` | StickerShock | Price increase detection & CPI comparison |
| `cartsnitch/shrinkray` | ShrinkRay | Shrinkflation monitoring |
| `cartsnitch/clipartist` | ClipArtist | Coupon/deal watching & shopping optimization |
| `cartsnitch/infra` | — | K8s manifests, Flux kustomizations |

## What This App Does

The frontend is a mobile-first PWA that serves as the primary user interface for CartSnitch. Users interact with it to:

1. **Connect store accounts** — link their Meijer, Kroger, Target loyalty accounts
2. **View purchase history** — see all purchases across stores in one timeline
3. **Browse products** — search the normalized product catalog
4. **Track prices** — view per-item price charts across stores over time
5. **Get alerts** — see price increase and shrinkflation notifications
6. **View coupons/deals** — browse active coupons relevant to their shopping
7. **Generate optimized shopping lists** — input what they need, get a store-split plan with coupon instructions
8. **Public dashboards** — shareable price transparency views (store comparisons, inflation tracking)

## Tech Stack

- React 18+ (or Next.js if SSR/SSG is valuable for public pages)
- TypeScript
- Tailwind CSS (mobile-first responsive design)
- Workbox (service worker, offline caching, PWA manifest)
- Recharts or Chart.js (price trend visualizations)
- TanStack Query (React Query) for data fetching and caching
- React Router (client-side routing)
- Zustand or Jotai (lightweight state management)
- Vite (build tool)

## Repo Structure

```
frontend/
├── CLAUDE.md
├── README.md
├── package.json
├── tsconfig.json
├── vite.config.ts
├── tailwind.config.ts
├── Dockerfile                  # Multi-stage: build + nginx serve
├── docker-compose.yml          # Local dev
├── public/
│   ├── manifest.json           # PWA manifest
│   ├── sw.js                   # Service worker (Workbox generated)
│   ├── icons/                  # PWA icons (192, 512, maskable)
│   └── favicon.ico
├── src/
│   ├── main.tsx
│   ├── App.tsx
│   ├── api/
│   │   ├── client.ts           # Axios/fetch wrapper, JWT interceptor
│   │   ├── auth.ts             # Auth API calls
│   │   ├── purchases.ts
│   │   ├── products.ts
│   │   ├── prices.ts
│   │   ├── coupons.ts
│   │   ├── shopping.ts
│   │   └── alerts.ts
│   ├── hooks/
│   │   ├── useAuth.ts
│   │   ├── usePurchases.ts
│   │   ├── useProducts.ts
│   │   ├── usePrices.ts
│   │   └── useAlerts.ts
│   ├── pages/
│   │   ├── Login.tsx
│   │   ├── Register.tsx
│   │   ├── Dashboard.tsx        # Home — summary, recent purchases, alerts
│   │   ├── Purchases.tsx        # Purchase history timeline
│   │   ├── PurchaseDetail.tsx   # Single receipt view
│   │   ├── Products.tsx         # Product catalog / search
│   │   ├── ProductDetail.tsx    # Product with cross-store price chart
│   │   ├── Prices.tsx           # Price trends overview
│   │   ├── Coupons.tsx          # Active deals
│   │   ├── ShoppingList.tsx     # Optimized shopping list builder
│   │   ├── Alerts.tsx           # Price increase / shrinkflation alerts
│   │   ├── StoreAccounts.tsx    # Manage connected stores
│   │   ├── Settings.tsx
│   │   └── public/
│   │       ├── PriceTrends.tsx  # Public shareable price dashboards
│   │       └── StoreComparison.tsx
│   ├── components/
│   │   ├── layout/
│   │   │   ├── AppShell.tsx     # Mobile nav, header, bottom tabs
│   │   │   ├── BottomNav.tsx
│   │   │   └── Header.tsx
│   │   ├── charts/
│   │   │   ├── PriceHistoryChart.tsx
│   │   │   ├── SpendingChart.tsx
│   │   │   └── InflationComparisonChart.tsx
│   │   ├── purchases/
│   │   │   ├── PurchaseCard.tsx
│   │   │   └── PurchaseItemRow.tsx
│   │   ├── products/
│   │   │   ├── ProductCard.tsx
│   │   │   └── StorePriceComparison.tsx
│   │   ├── coupons/
│   │   │   └── CouponCard.tsx
│   │   ├── shopping/
│   │   │   ├── ShoppingListEditor.tsx
│   │   │   └── OptimizedPlan.tsx
│   │   ├── alerts/
│   │   │   ├── PriceAlertCard.tsx
│   │   │   └── ShrinkflationCard.tsx
│   │   └── common/
│   │       ├── LoadingSpinner.tsx
│   │       ├── EmptyState.tsx
│   │       ├── StoreLogo.tsx
│   │       └── ErrorBoundary.tsx
│   ├── stores/                 # Zustand/Jotai state stores
│   │   ├── authStore.ts
│   │   └── uiStore.ts
│   ├── utils/
│   │   ├── formatCurrency.ts
│   │   ├── formatDate.ts
│   │   └── storeSlugs.ts
│   └── types/
│       ├── purchase.ts
│       ├── product.ts
│       ├── price.ts
│       ├── coupon.ts
│       └── alert.ts
└── tests/
    └── ...
```

## Design Principles

- **Mobile-first.** Primary use case is checking prices and managing lists on a phone in-store or on the couch. Design for 375px viewport first, scale up.
- **Fast and offline-capable.** Service worker caches the app shell and recent data. Users should be able to browse their purchase history and shopping lists offline.
- **Minimal, opinionated UI.** This isn't a generic dashboard. Every screen should answer a specific question: "What did I buy?" "Where should I buy this?" "Am I getting ripped off?"
- **Store branding.** Use each retailer's brand colors for visual differentiation (Meijer red, Kroger blue, Target red — careful with the two reds, differentiate with icons/logos).
- **Charts that tell a story.** Price history charts should make it immediately obvious when a price spiked. Annotations for "coupon available" or "inflation baseline" add context.

## PWA Requirements

- `manifest.json` with proper app name, icons (192x192, 512x512, maskable), theme color, background color, display: standalone
- Service worker via Workbox: precache app shell, runtime cache API responses with stale-while-revalidate
- Add to Home Screen support on iOS and Android
- Offline fallback page

## API Integration

All data comes from the CartSnitch API gateway (`cartsnitch/api`). Base URL configured via environment variable `VITE_API_URL`.

- JWT auth: store access token in memory (not localStorage), refresh token in httpOnly cookie if possible, or secure storage.
- TanStack Query handles caching, background refetching, and optimistic updates.
- API client should handle 401 responses by attempting token refresh before retrying.

## Development Workflow

- **Never push directly to main.** Always create feature branches and open PRs.
- Branch naming: `feature/<description>` or `fix/<description>`
- Use conventional commits: `feat:`, `fix:`, `refactor:`, `docs:`, `chore:`
- `npm run dev` for local development with hot reload
- `npm run build` for production build
- Lint with ESLint, format with Prettier

## Important Notes

- The store account connection flow is the most complex UX. Users need to authenticate with each retailer. This likely involves opening a controlled browser window/iframe where they log in, and CartSnitch captures the resulting session. Design this flow carefully — it needs to feel safe and trustworthy.
- Public price transparency pages should be SSR-friendly or statically generated for SEO if the "naming and shaming" feature is going to get organic traffic. Consider Next.js for these pages specifically, or a separate lightweight static site.
- The optimized shopping list is the killer feature for retention. Make it dead simple: add items → see the split → go shop. No friction.
- Push notifications (via service worker) for price alerts and deal notifications are a Phase 2+ feature but design the alert system with this in mind.
