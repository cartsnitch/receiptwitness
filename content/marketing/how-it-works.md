# How CartSnitch Works

## The Core Idea

Every product at the grocery store has two prices:
- **Shelf price** — what you pay at checkout
- **Unit price** — what you pay per ounce, per gram, per sheet, per load

Most people compare shelf prices. Smart shoppers compare unit prices.

CartSnitch tracks unit prices automatically — so you don't have to do the math yourself.

---

## How We Track Prices

CartSnitch pulls pricing data from:
- **Store loyalty portals** — Meijer, Kroger, and Target — when you connect your account, CartSnitch uses an automated scraper to pull your purchase history from the store loyalty portal
- **Public manufacturer data** — packaging changes, suggested retail prices
- **USDA FoodData Central** — reference data for package sizing baselines (used for historical size comparison only — not part of our live tracking system)

We calculate unit price for every product we track:

`Unit Price = Shelf Price ÷ Package Size`

When a brand reduces package size — or a store changes its price — we catch it.

---

## What Is Shrinkflation Detection?

Shrinkflation happens when a brand reduces the size of a product without lowering the price. The shelf price stays the same. The unit price goes up.

**Example:**
- 2021: Cereal at $4.99 for 18 oz → $0.277 per oz
- 2024: Same cereal at $4.99 for 15.5 oz → $0.322 per oz

Same price. 16% more per ounce. That's shrinkflation.

CartSnitch monitors unit prices over time. When we detect a statistically significant unit price increase — whether from a size reduction, a price increase, or both — we flag it.

---

## How Price Alerts Work

1. **You add a product** — Search for any product you buy regularly and add it to your tracked list.
2. **We monitor unit prices** — Every time we detect a price or size change, we recalculate the unit price.
3. **You get an alert** — If the unit price increases beyond a threshold, we notify you — so you can decide whether to switch products, switch stores, or just be aware.

You choose what counts as significant. Some users set alerts for any change. Others only want to know about large unit price jumps.

---

## Store Comparison

CartSnitch compares your total grocery basket across stores.

When you connect your store accounts, we can see what you bought and where. We calculate the total cost of your typical basket at each store we support — so you know where you're getting the best overall deal.

This is different from just comparing the price of one item. Some stores are cheaper on produce, others on pantry staples. CartSnitch shows you the full picture.

---

## What We Don't Do

- **We don't collect receipts** — Store account connections give us enough data to track prices and compare baskets. Receipt-based tracking is being evaluated.
- **We don't have every product** — Beta is limited to supported stores and categories. We're adding more every week.
- **We don't affect shelf prices** — We show you the data. What you do with it is up to you.

---

## How We Protect Your Data

- We read price data from your connected store accounts — we never see your login credentials
- We store only the minimum data needed to calculate unit prices and compare baskets
- We don't sell your data to third parties
- You can disconnect your store account at any time and delete your data

---

## Ready to Start?

[Sign up for beta →]
