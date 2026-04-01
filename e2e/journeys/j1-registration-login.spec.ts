import { test, expect } from '@playwright/test';

const uniqueEmail = () => `betty+e2e-${Date.now()}@cartsnitch.test`;

test.describe('J1: Registration and Login', () => {
  test('can register a new account and lands on dashboard', async ({ page }) => {
    await page.goto('/register');
    await page.fill('[placeholder="Full Name"]', 'Betty Tester');
    await page.fill('[placeholder="Email"]', uniqueEmail());
    await page.fill('[placeholder="Password (min. 8 characters)"]', 'TestPass123!');
    await page.click('button[type="submit"]');

    // With VITE_MOCK_AUTH=true the app navigates to "/" on success
    await expect(page).toHaveURL('http://localhost:5173/');
    await expect(page.getByRole('heading', { name: /cart/i })).toBeVisible();
  });

  test('shows validation error when registration fields are empty', async ({ page }) => {
    await page.goto('/register');
    await page.click('button[type="submit"]');

    await expect(page.locator('.bg-red-50')).toContainText('Please fill in all fields');
  });

  test('can navigate from register to login', async ({ page }) => {
    await page.goto('/register');
    await page.getByRole('link', { name: /sign in/i }).click();

    await expect(page).toHaveURL(/\/login/);
    await expect(page.getByRole('heading', { name: /cartsnitch/i })).toBeVisible();
  });

  test('can sign in with credentials and land on dashboard', async ({ page }) => {
    // Register first so we have a real account
    const email = uniqueEmail();
    await page.goto('/register');
    await page.fill('[placeholder="Full Name"]', 'Login Betty');
    await page.fill('[placeholder="Email"]', email);
    await page.fill('[placeholder="Password (min. 8 characters)"]', 'TestPass123!');
    await page.click('button[type="submit"]');
    await expect(page).toHaveURL('http://localhost:5173/');

    // Sign out by clearing the mock session (reload with no session)
    await page.goto('/');
    await page.reload();

    // Now sign in
    await page.goto('/login');
    await page.fill('[placeholder="Email"]', email);
    await page.fill('[placeholder="Password"]', 'TestPass123!');
    await page.click('button[type="submit"]');

    await expect(page).toHaveURL('http://localhost:5173/');
  });

});
