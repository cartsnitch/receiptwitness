import { test, expect, mockAuthRoutes } from './fixtures';

test('app loads', async ({ page }) => {
  await mockAuthRoutes(page, false);
  await page.goto('/');
  await expect(page).toHaveURL(/\/login/);
  await expect(page.getByRole('heading', { name: /CartSnitch/i })).toBeVisible();
});
