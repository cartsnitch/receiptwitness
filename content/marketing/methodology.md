# How We Calculate Shrinkflation: Our Methodology

We believe consumers deserve to verify our work. Here's exactly how we calculate shrinkflation percentages and where our data comes from.

---

## The Core Formula

For every product we track, we calculate:

**Unit Price = Shelf Price ÷ Package Size**

Then we calculate the shrinkflation percentage:

**Shrinkflation % = (New Unit Price ÷ Old Unit Price) − 1**

This gives us the effective price increase — accounting for both size changes and price changes.

**Example:**
- 2021: Cereal at $4.99 for 18 oz → Unit price: $4.99 ÷ 18 oz = $0.277/oz
- 2024: Same cereal at $4.99 for 15.5 oz → Unit price: $4.99 ÷ 15.5 oz = $0.322/oz

Shrinkflation % = ($4.99 ÷ 15.5) ÷ ($4.99 ÷ 18) − 1 = 16.1%

The shelf price is the same. The unit price went up 16.1%.

---

## Data Sources

We use multiple data sources to build our shrinkflation rankings:

### 1. Manufacturer Packaging Data
We track documented changes in product sizes as reported by manufacturers. This includes:
- Net weight changes on packaging
- Count-per-package changes (e.g., 4 rolls → 3 rolls)
- Volume changes in liquid products

### 2. USDA FoodData Central
The USDA FoodData Central database provides reference data on product sizes and nutrition, which we use as baselines for historical comparison.

**URL:** https://fdc.nal.usda.gov/

### 3. Public Retail Data
When available, we cross-reference shelf prices from public retailer sources to validate price continuity.

---

## How We Rank Shrinkflation Offenders

Our top shrinkflation offenders rankings are based on the calculated shrinkflation percentage for each product. We rank products by:

1. **Highest shrinkflation percentage** — the largest effective unit price increase
2. **Across consistent time periods** — comparing current sizes/prices to documented baselines from 2020–2024
3. **By product category** — cereals, snacks, dairy, household goods, etc.

We only include products where we have documented evidence of a size or price change. We do not estimate shrinkflation for products we cannot verify.

---

## Shrinkflation vs Regular Price Increases

We distinguish between:

- **Shrinkflation** — Package size decreases while shelf price stays the same or increases. Unit price goes up.
- **Regular price increase** — Package size stays the same, shelf price goes up. Unit price goes up.
- **Combined shrinkflation + price increase** — Package size decreases AND shelf price increases. Unit price goes up significantly.

All three result in a higher unit price. Our percentages capture the total effective increase.

---

## What We Don't Do

- We don't estimate shrinkflation without documented evidence
- We don't include products we cannot verify
- We don't adjust our calculations based on brand or retailer pressure
- We don't publish specific rankings until we can verify the underlying data

---

## Production Data vs Estimates

**Before launch (current):** Our shrinkflation percentages are based on publicly available manufacturer packaging data. USDA FoodData Central provides reference data for package sizing baselines. These are directional estimates — they tell you the pattern is real.

**After production deployment:** Once we have a live product with real transaction data, we'll be able to run the numbers against actual purchase data. This will validate and refine our estimates.

We will always note when statistics are directional estimates versus based on production data.

---

## Future: Publishing Our Queries

Once production is live, we plan to publish the SQL queries behind our shrinkflation calculations — so anyone can run them against our data and verify our work.

This is part of our commitment to transparency.

---

## Questions?

If you have questions about our methodology or believe we've made an error, email us: hello@cartsnitch.app
