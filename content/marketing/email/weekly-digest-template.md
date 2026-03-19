---
title: "Email Template — Weekly Price Alert Digest"
status: draft
last_updated: 2026-03-18
description: "Template for weekly email digest showing price changes, deals, and shrinkflation alerts for subscriber's tracked products."
---

# Weekly Price Alert Digest

**Trigger:** Every Monday at 8:00 AM ET (for users with connected store accounts)
**Subject line options:**
- "Your weekly grocery prices: [X] items changed"
- "Eggs are down 12% this week — plus [X] more price moves"
- "Weekly price update: [X] drops, [Y] increases, [Z] shrinkflation alerts"

**From:** CartSnitch <alerts@cartsnitch.com>

---

Hey {{first_name}},

Here's what happened to your grocery prices this week.

---

### 📉 Price Drops

{{#if price_drops}}
| Product | Store | Was | Now | Change |
|---|---|---|---|---|
| {{product_name}} | {{store}} | {{old_price}} | {{new_price}} | {{percent_change}} |

**Best deal this week:** {{best_deal_product}} is at its lowest price in {{time_period}} at {{store}} — {{price}}.
{{else}}
No price drops on your tracked items this week. We'll keep watching.
{{/if}}

---

### 📈 Price Increases

{{#if price_increases}}
| Product | Store | Was | Now | Change |
|---|---|---|---|---|
| {{product_name}} | {{store}} | {{old_price}} | {{new_price}} | {{percent_change}} |

{{#if cheaper_alternative}}
**Tip:** {{product_name}} is {{percent_cheaper}}% cheaper at {{alt_store}} right now ({{alt_price}}).
{{/if}}
{{else}}
No increases on your tracked items. Nice week.
{{/if}}

---

### 🔍 Shrinkflation Alerts

{{#if shrinkflation_alerts}}
**{{product_name}}** ({{brand}})
Was: {{old_size}} — Now: {{new_size}} — Same price
That's a **{{hidden_increase}}% hidden price increase**.
{{else}}
No new shrinkflation detected on your products this week.
{{/if}}

---

### 💡 This Week's Tip

{{weekly_tip}}

---

[View your full price dashboard →](#)

You're tracking {{tracked_count}} products across {{store_count}} stores. [Manage your alerts →](#)

— The CartSnitch Team

*You're receiving this because you signed up for CartSnitch price alerts. [Unsubscribe](#) | [Update preferences](#)*
