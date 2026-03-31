import { test as base, expect } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";

export const test = base.extend<{ axeCheck: void }>({
  axeCheck: [async ({ page }, use) => {
    await use();
    const results = await new AxeBuilder({ page }).analyze();
    expect(results.violations).toEqual([]);
  }, { auto: true }],
});

export { expect } from "@playwright/test";
