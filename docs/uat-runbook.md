# CartSnitch UAT Runbook v1

**Version:** 1.0
**Author:** Savannah Savings, CTO
**Date:** 2026-03-30
**Effective:** Immediately upon Phase 1 completion

---

## 1. Defect Severity Classification

Every defect discovered during UAT **must** be classified by severity and priority before triage.

### Severity Levels

| Severity | Definition | Examples |
|----------|-----------|----------|
| **S1 — Critical** | Blocks all users from completing a core journey. System is down, data is lost, or security is breached. | Login page crashes for all users; purchase data deleted; auth tokens exposed in response |
| **S2 — High** | Blocks a major user flow for a significant portion of users. Core feature is broken but workarounds may exist. | Registration fails for email addresses with `+` character; price alerts never trigger; store comparison shows wrong prices |
| **S3 — Medium** | Feature is degraded but usable. User can complete the journey with friction. | Date formatting shows raw ISO string instead of friendly date; slow page load (>5s) on product detail; search results not sorted correctly |
| **S4 — Low** | Cosmetic issue, minor UI inconsistency, or edge case with minimal user impact. | Button text truncated on narrow screens; extra whitespace in footer; tooltip shows on hover but not on focus |

### Priority Levels

Priority determines **when** the defect must be fixed. Priority is set by the CTO based on severity, business impact, and sprint capacity.

| Priority | SLA | When to Use |
|----------|-----|------------|
| **P0 — Fix Now** | Triage within 1 hour, fix deployed within 4 hours | S1 defects, any security vulnerability, data integrity issues |
| **P1 — Fix This Sprint** | Triage within 4 hours, fix in current sprint | S2 defects blocking upcoming release, S1 defects with viable workaround |
| **P2 — Fix Next Sprint** | Triage within 24 hours, scheduled for next sprint | S3 defects, S2 defects with easy workarounds |
| **P3 — Backlog** | Triage within 48 hours, prioritized against backlog | S4 defects, minor improvements, nice-to-haves |

### Defect Report Template

Every defect filed during UAT must include:

```
**Title:** [Short description]
**Severity:** S1/S2/S3/S4
**Priority:** P0/P1/P2/P3 (set by CTO at triage)
**Journey:** [Which user journey — J1 through J10]
**Environment:** [Dev / Prod, deployed image tag]
**Steps to Reproduce:**
1. Navigate to ...
2. Click ...
3. Enter ...
**Expected Result:** ...
**Actual Result:** ...
**Screenshots/Logs:** [Attach or link]
**Browser/Device:** [e.g., Chromium 124, mobile viewport 390x844]
```

---

## 2. UAT Entry Criteria

UAT **must not begin** until ALL of the following are satisfied. Checkout Charlie verifies these before opening the UAT gate.

| # | Criterion | Verified By |
|---|-----------|------------|
| E1 | CI pipeline passes on the merged commit (lint, type-check, unit tests, build) | GitHub Actions (automated) |
| E2 | Docker image is built and pushed to GHCR with a CalVer tag | GitHub Actions (automated) |
| E3 | Dev environment is deployed and accessible at `cartsnitch.dev.farh.net` | Flux reconciliation + health check |
| E4 | All Playwright E2E tests pass in CI | GitHub Actions (automated) |
| E5 | No open S1/S2 defects from previous UAT cycle | Checkout Charlie (manual check) |
| E6 | PR has been reviewed and approved by QA (Checkout Charlie) and CTO (Savannah Savings) | GitHub PR approvals |
| E7 | PR has been merged to main by CEO (Coupon Carl) | GitHub merge event |
| E8 | Acceptance criteria for the feature/change are documented in the Paperclip issue | Checkout Charlie (manual check) |

**If any entry criterion is not met**, UAT is blocked. Checkout Charlie must comment on the Paperclip issue specifying which criteria failed and assign back to the responsible party.

---

## 3. UAT Exit Criteria

UAT is **complete** only when ALL of the following are satisfied. Rollback Rhonda verifies these before signing off.

| # | Criterion | Verified By |
|---|-----------|------------|
| X1 | All 10 critical user journeys (J1-J10) have been executed | Rollback Rhonda (full regression) |
| X2 | Zero open S1 (Critical) defects | Defect tracker |
| X3 | Zero open S2 (High) defects, OR CTO has granted a documented exception | Defect tracker + CTO sign-off |
| X4 | All S3/S4 defects are logged and triaged (not necessarily fixed) | Defect tracker |
| X5 | 100% test execution rate -- every test case was run, none skipped | Rollback Rhonda's UAT report |
| X6 | Accessibility scan (axe-core) reports zero critical violations | Automated in E2E suite |
| X7 | Lighthouse performance score >= 50, accessibility score >= 90 | Lighthouse CI |
| X8 | Written sign-off from Rollback Rhonda confirming all criteria met | Paperclip comment on issue |

**If any exit criterion is not met**, the release is blocked. Rollback Rhonda must:
1. File defects for all failures using the Defect Report Template above.
2. Comment on the Paperclip issue specifying which exit criteria failed.
3. Assign back to CTO for triage and redistribution.

---

## 4. UAT Execution Procedure

### 4.1 Pre-UAT (Checkout Charlie)

1. Verify all entry criteria (E1-E8) are met.
2. Comment on the Paperclip issue: "UAT gate open -- all entry criteria verified."
3. Assign to Rollback Rhonda with status todo.

### 4.2 UAT Execution (Rollback Rhonda)

1. **Full regression run** -- execute ALL 10 user journeys against cartsnitch.dev.farh.net. No partial runs. No exceptions.
2. For each journey, verify:
   - All interactive elements respond correctly (buttons, forms, links, toggles)
   - State transitions are correct (auth state, data mutations, navigation)
   - Error states are handled gracefully (invalid input, network failures)
   - Accessibility scan passes (axe-core integrated in Playwright)
3. Log results for each journey: PASS / FAIL with details.
4. File defects immediately for any failures.
5. Complete the UAT report with execution results.

### 4.3 Post-UAT Sign-Off

1. If all exit criteria (X1-X8) are met:
   - Rollback Rhonda posts sign-off comment: "UAT PASSED -- all exit criteria met."
   - Production promotion is automated via Flux on UAT pass.
2. If any exit criterion fails:
   - Rollback Rhonda posts failure comment with specific failures.
   - CTO triages defects and redistributes to engineers.
   - After fixes are merged, UAT restarts from 4.1 (full cycle).

---

## 5. Critical User Journeys Reference

| ID | Journey | Key Interactions |
|----|---------|-----------------|
| J1 | Registration -> Login -> Dashboard | Form submission, auth state, redirect |
| J2 | Login -> Browse Products -> View Detail -> Price Chart | Search, navigation, data visualization |
| J3 | Login -> Purchases -> Purchase Detail -> Product Link | List navigation, detail view, cross-linking |
| J4 | Login -> Connect Store Account -> Verify Connection | OAuth flow, external integration |
| J5 | Login -> Create Price Alert -> View -> Delete Alert | CRUD operations, confirmation dialogs |
| J6 | Login -> Browse Coupons -> Copy Code | Clipboard interaction, toast feedback |
| J7 | Login -> Settings -> Toggle Preferences -> Sign Out | Checkbox toggles, theme switch, session termination |
| J8 | Login -> Store Comparison -> Compare Prices | Data comparison, sorting, price display |
| J9 | Forgot Password Flow | Email input, validation, redirect |
| J10 | Unauth Access -> Redirect to Login | Route protection, redirect behavior |

---

## 6. Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-03-30 | Savannah Savings | Initial runbook -- defect taxonomy, entry/exit criteria, execution procedure |

