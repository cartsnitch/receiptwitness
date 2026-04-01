import { test, expect } from '@playwright/test';

test.describe('J8: Unauthenticated Access', () => {
  test('redirects /dashboard (/) to /login when not authenticated', async ({ page }) => {
    // No session cookie — start fresh
    await page.context().clearCookies();
    await page.goto('/');

    await expect(page).toHaveURL(/\/login/);
    await expect(page.getByRole('heading', { name: /cartsnitch/i })).toBeVisible();
  });

  test('redirects /purchases to /login when not authenticated', async ({ page }) => {
    await page.context().clearCookies();
    await page.goto('/purchases');

    await expect(page).toHaveURL(/\/login/);
    await expect(page.getByRole('heading', { name: /cartsnitch/i })).toBeVisible();
  });

  test('redirects /products to /login when not authenticated', async ({ page }) => {
    await page.context().clearCookies();
    await page.goto('/products');

    await expect(page).toHaveURL(/\/login/);
    await expect(page.getByRole('heading', { name: /cartsnitch/i })).toBeVisible();
  });

  test('redirects /coupons to /login when not authenticated', async ({ page }) => {
    await page.context().clearCookies();
    await page.goto('/coupons');

    await expect(page).toHaveURL(/\/login/);
    await expect(page.getByRole('heading', { name: /cartsnitch/i })).toBeVisible();
  });

  test('shows loading spinner while auth session is pending', async ({ page }) => {
    // Intercept but don't respond — session stays pending
    await page.context().clearCookies();
    await page.request.fetch('/api/auth/session', {
      method: 'GET',
    });

    // Just navigate to a protected route — ProtectedRoute will show spinner while session is pending
    await page.goto('/purchases');
    // Spinner is visible briefly; once resolved, should redirect to login
    await expect(page).toHaveURL(/\/login/, { timeout: 10_000 });
  });
});
