---
title: "Email Template — Shrinkflation Alert Notification"
status: draft
last_updated: 2026-03-18
description: "Real-time alert email sent when shrinkflation is detected on a product the user buys."
---

# Shrinkflation Alert Notification

**Trigger:** Real-time, when shrinkflation is detected on a product in the user's purchase history
**Subject line options:**
- "🔍 Shrinkflation alert: {{product_name}} just got smaller"
- "{{brand}} {{product_name}} shrank — here's what it costs you"
- "Same price, less {{product_name}}. We caught it."

**From:** CartSnitch <alerts@cartsnitch.com>

---

Hey {{first_name}},

We detected shrinkflation on a product you buy.

---

## {{brand}} {{product_name}}

| | Before | After |
|---|---|---|
| **Package size** | {{old_size}} | {{new_size}} |
| **Price** | {{price}} | {{price}} |
| **Unit price** | {{old_unit_price}}/{{unit}} | {{new_unit_price}}/{{unit}} |

**What this means:** You're now paying **{{hidden_increase}}% more per {{unit}}** for the same product at the same sticker price.

**Your annual impact:** Based on your purchase history, you buy this product about {{purchase_frequency}} times per year. This shrinkflation costs you an estimated **{{annual_cost}}** more annually for less product.

---

### What you can do

{{#if cheaper_alternative}}
**Switch stores:** {{product_name}} is {{percent_cheaper}}% cheaper per {{unit}} at {{alt_store}} right now.
{{/if}}

{{#if store_brand_option}}
**Try the store brand:** {{store_brand_name}} is {{sb_unit_price}}/{{unit}} — {{sb_savings}}% less per {{unit}} than the name brand.
{{/if}}

**Set a price alert:** [Get notified](#) if the price drops below {{target_price}}.

---

[View full product history →](#)

— The CartSnitch Team

*You're receiving this because you have shrinkflation alerts enabled. [Manage your alerts →](#) | [Unsubscribe](#)*
