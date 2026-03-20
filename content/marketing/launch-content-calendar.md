# CartSnitch Beta Launch Content Calendar

**Beta Launch Date:** April 24, 2026
**Calendar Period:** March 20 – May 15, 2026

This calendar coordinates all marketing content across channels — blog, email, social, and in-app — to build awareness and drive activation for the CartSnitch public beta.

---

## Phase 1: Pre-Launch Warmup (March 20 – March 31)

**Goal:** Seed organic reach and establish brand voice before the launch sprint begins.

| Date | Channel | Asset | Notes |
|------|---------|-------|-------|
| Mar 24 (Mon) | Blog | [Why We Built CartSnitch](blog/why-we-built-cartsnitch.md) | Founder story; sets authentic tone |
| Mar 25 (Tue) | Twitter | Teaser thread: "We've been quietly tracking grocery prices for a year..." | Link to blog post |
| Mar 26 (Wed) | Reddit | Post to r/Frugal, r/personalfinance — founder intro + blog | Soft intro, no hard sell |
| Mar 28 (Fri) | Email | Welcome sequence finalized in ESP | [welcome-sequence.md](email/welcome-sequence.md) loaded and tested |
| Mar 31 (Mon) | Internal | Brand voice guide reviewed by team | [brand-voice-guide.md](brand-voice-guide.md) |

---

## Phase 2: Content Publishing Sprint (April 1 – April 10)

**Goal:** Get SEO and onboarding content live ahead of the launch window.

| Date | Channel | Asset | Notes |
|------|---------|-------|-------|
| Apr 1 (Wed) | Blog | Shrinkflation Series #1: [Cereal](blog/shrinkflation-cereal-2026.md) | Tag: shrinkflation, grocery prices |
| Apr 3 (Fri) | Blog | Shrinkflation Series #2: [Dairy & Eggs](blog/shrinkflation-dairy-eggs-2026.md) | |
| Apr 4 (Sat) | Twitter | Weekly price watch post (template) | [weekly-price-watch-template.md](social/weekly-price-watch-template.md) |
| Apr 7 (Mon) | Blog | Shrinkflation Series #3: [Frozen Food](blog/shrinkflation-frozen-food-2026.md) | |
| Apr 9 (Wed) | Blog | Shrinkflation Series #4: [Household Essentials](blog/shrinkflation-household-essentials-2026.md) | |
| Apr 10 (Thu) | Site | Onboarding guides live on cartsnitch.com/help | [onboarding/](onboarding/) — all 5 guides |
| Apr 10 (Thu) | Site | FAQ published | [faq.md](faq.md) |

---

## Phase 3: Launch Build-Up (April 11 – April 17)

**Goal:** Escalate cadence, prime the audience, get ready for screenshots once staging is available.

| Date | Channel | Asset | Notes |
|------|---------|-------|-------|
| Apr 11 (Fri) | Blog | Shrinkflation Series #5: [Snacks & Chips](blog/shrinkflation-snacks-chips-2026.md) | Final in series |
| Apr 12 (Sat) | Twitter | Weekly price watch post | Tag shrinkflation series recap |
| Apr 14 (Mon) | Twitter | Launch countdown thread — "10 days until beta" | Drive waitlist signups |
| Apr 15 (Tue) | Reddit | r/personalfinance launch preview post | [reddit-launch-strategy.md](social/reddit-launch-strategy.md) |
| Apr 17 (Thu) | Site | Screenshots integrated into landing page + blog posts | Depends on staging env (CAR-60); stretch if delayed |
| Apr 17 (Thu) | Email | Pre-launch email to waitlist: "You're almost in" | Tease beta access |
| Apr 17 (Thu) | Internal | Website landing page final review | [website-landing-page.md](website-landing-page.md) |

---

## Phase 4: Launch Week (April 20 – April 24)

**Goal:** Maximum visibility on launch day.

| Date | Channel | Asset | Notes |
|------|---------|-------|-------|
| Apr 20 (Mon) | All | Final content audit — all links live, all placeholders resolved | Checklist review |
| Apr 21 (Tue) | Email | "Launch day is Thursday" email to waitlist | Build anticipation |
| Apr 21 (Tue) | Twitter | [Twitter launch strategy](social/twitter-launch-strategy.md) — thread queued and scheduled | |
| Apr 22 (Wed) | Reddit | [Reddit launch post](social/reddit-launch-strategy.md) — drafted and ready to post | Post on launch day |
| **Apr 24 (Thu)** | **ALL** | **🚀 BETA LAUNCH** | |
| Apr 24 (Thu) | Blog | [Launch announcement](launch-announcement.md) published | |
| Apr 24 (Thu) | Twitter | Launch thread goes live | Link to announcement + app |
| Apr 24 (Thu) | Reddit | r/Frugal + r/personalfinance + r/grocery launch posts | |
| Apr 24 (Thu) | Email | Launch email to full waitlist | Welcome + CTA to connect first store |

---

## Phase 5: Post-Launch Nurture (April 25 – May 15)

**Goal:** Activate new users, maintain cadence, capture organic search momentum.

| Date | Channel | Asset | Notes |
|------|---------|-------|-------|
| Apr 26 (Sat) | Twitter | First weekly price watch post post-launch | [weekly-price-watch-template.md](social/weekly-price-watch-template.md) |
| Apr 28 (Mon) | Email | First weekly digest to active users | [weekly-digest-template.md](email/weekly-digest-template.md) |
| Apr 30 (Wed) | Email | Shrinkflation alert (triggered) | [shrinkflation-alert-template.md](email/shrinkflation-alert-template.md) — send when first alert fires |
| May 1 (Fri) | Blog | Post-launch reflection / data post (new) | "What we learned in week 1" |
| May 3 (Sat) | Twitter | Weekly price watch #2 | |
| May 5 (Mon) | Email | Weekly digest #2 | |
| May 10 (Sat) | Twitter | Weekly price watch #3 | |
| May 12 (Mon) | Email | Weekly digest #3 | |
| May 15 (Thu) | All | 3-week post-launch content review | Assess engagement, plan next sprint |

---

## Channel Owners

| Channel | Owner | Tool |
|---------|-------|------|
| Blog | Marketing / CMO | GitHub (`content/marketing/blog/`) |
| Email | Marketing | ESP (Mailchimp / Postmark) |
| Twitter | Marketing | Buffer / manual |
| Reddit | Marketing | Manual (no bots) |
| Site pages | Frontend (Frankie) | Deployed via CI |

---

## Dependencies & Risks

| Dependency | Blocker? | Notes |
|------------|----------|-------|
| Staging env with sample data (CAR-60) | Screenshots only | If delayed past Apr 17, screenshots launch without images |
| App Store / PWA listing copy | No (Phase 2+) | Not blocking beta; listed in CAR-114 as stretch |
| SEO comparison articles | No (stretch) | [content/marketing/blog/](blog/) — ongoing |

---

## Asset Index

All content files live under `content/marketing/` in this repo:

- `blog/` — long-form blog posts (SEO)
- `email/` — email templates and sequences
- `onboarding/` — in-app / help center guides
- `social/` — social media strategies and templates
- `launch-announcement.md` — press/blog launch post
- `website-landing-page.md` — landing page copy
- `faq.md` — FAQ / help center
- `brand-voice-guide.md` — tone, style, persona
