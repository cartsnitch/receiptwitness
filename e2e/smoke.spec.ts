import { test, expect } from './fixtures';

test('app loads', async ({ page }) => {
  await page.goto('/');
  // Unauthenticated users are redirected to /login
  await expect(page).toHaveURL(/\/login/);
  await expect(page.getByRole('heading', { name: /sign in|log in/i })).toBeVisible();
});
