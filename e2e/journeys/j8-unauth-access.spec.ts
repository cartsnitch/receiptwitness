import { test, expect } from '@playwright/test';
import { mockAuthRoutes, mockSessionDelayed } from '../fixtures';

test.describe('J8: Unauthenticated Access', () => {
  test('redirects /dashboard (/) to /login when not authenticated', async ({ page }) => {
    await mockAuthRoutes(page, false);
    await page.goto('/');

    await expect(page).toHaveURL(/\/login/);
    await expect(page.getByRole('heading', { name: /cartsnitch/i })).toBeVisible();
  });

  test('redirects /purchases to /login when not authenticated', async ({ page }) => {
    await mockAuthRoutes(page, false);
    await page.goto('/purchases');

    await expect(page).toHaveURL(/\/login/);
    await expect(page.getByRole('heading', { name: /cartsnitch/i })).toBeVisible();
  });

  test('redirects /products to /login when not authenticated', async ({ page }) => {
    await mockAuthRoutes(page, false);
    await page.goto('/products');

    await expect(page).toHaveURL(/\/login/);
    await expect(page.getByRole('heading', { name: /cartsnitch/i })).toBeVisible();
  });

  test('redirects /coupons to /login when not authenticated', async ({ page }) => {
    await mockAuthRoutes(page, false);
    await page.goto('/coupons');

    await expect(page).toHaveURL(/\/login/);
    await expect(page.getByRole('heading', { name: /cartsnitch/i })).toBeVisible();
  });

  test('shows loading spinner while auth session is pending', async ({ page }) => {
    await mockSessionDelayed(page, 3000);
    await page.goto('/purchases');
    await expect(page.locator('.animate-spin')).toBeVisible({ timeout: 2000 });
    await expect(page).toHaveURL(/\/login/, { timeout: 10_000 });
  });
});
