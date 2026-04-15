import { test as base, expect, type Page } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";

export const test = base.extend<{ axeCheck: void }>({
  axeCheck: [async ({ page }, use) => {
    await use();
    const results = await new AxeBuilder({ page }).analyze();
    expect(results.violations).toEqual([]);
  }, { auto: true }],
});

export { expect } from "@playwright/test";

const MOCK_USER_ID = "mock_user_123";
const MOCK_SESSION_ID = "mock_session_456";

async function mockAuthRoutes(page: Page, authenticated = false) {
  await page.route(/.*\/auth\/sign-up\/email.*/, async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        token: null,
        user: {
          id: MOCK_USER_ID,
          email: "mock@cartsnitch.test",
          name: "Mock User",
          emailVerified: true,
          createdAt: new Date().toISOString(),
          updatedAt: new Date().toISOString(),
        },
      }),
    });
  });

  await page.route(/.*\/auth\/sign-in\/email.*/, async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        redirect: false,
        token: "mock_token_123",
        user: {
          id: MOCK_USER_ID,
          email: "mock@cartsnitch.test",
          name: "Mock User",
          emailVerified: true,
          createdAt: new Date().toISOString(),
          updatedAt: new Date().toISOString(),
        },
      }),
    });
  });

  await page.route(/.*\/auth\/get-session.*/, async (route) => {
    if (authenticated) {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          session: {
            id: MOCK_SESSION_ID,
            expiresAt: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString(),
            createdAt: new Date().toISOString(),
            updatedAt: new Date().toISOString(),
            ipAddress: null,
            userAgent: null,
          },
          user: {
            id: MOCK_USER_ID,
            email: "mock@cartsnitch.test",
            name: "Mock User",
            emailVerified: true,
            createdAt: new Date().toISOString(),
            updatedAt: new Date().toISOString(),
          },
        }),
      });
    } else {
      await route.fulfill({
        status: 401,
        contentType: "application/json",
        body: JSON.stringify({ error: "Unauthorized" }),
      });
    }
  });
}

export async function mockSessionDelayed(page: Page, delayMs = 3000) {
  await page.route(/.*\/auth\/get-session.*/, async (route) => {
    await new Promise((r) => setTimeout(r, delayMs));
    await route.fulfill({
      status: 401,
      contentType: "application/json",
      body: JSON.stringify({ error: "Unauthorized" }),
    });
  });
}

export { mockAuthRoutes };
