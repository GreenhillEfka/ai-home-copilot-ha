/**
 * PS-UX-019 — Offline/Degraded Guards (Setup/Repair)
 *
 * Goal:
 * - simulate offline/network fail (here: block dashboard socket.io transport)
 * - verify degraded banner is shown
 * - verify retry CTA is present and is disabled while retry is running
 * - verify retry is possible again after it finishes
 *
 * Notes:
 * - This spec intentionally targets the shared UI-state patterns (banner + retry button)
 *   that are also used in Setup/Repair flows.
 * - No new dependencies.
 */

import { test, expect } from './fixtures';

const DASHBOARD_URL = process.env.DASHBOARD_URL || 'http://localhost:8766/dashboard';
const DASHBOARD_ORIGIN = new URL(DASHBOARD_URL).origin;

test.describe('Offline/Degraded Guards (Setup/Repair)', () => {
  test('shows degraded banner and guards retry CTA (disabled while running, retry possible)', async ({ page }) => {
    // Simulate "offline" for the live connection, without breaking the initial page load.
    // IMPORTANT: do NOT block the CDN socket.io script (https://cdn.socket.io/...)
    await page.route('**/socket.io/**', async (route) => {
      const url = new URL(route.request().url());
      if (url.origin === DASHBOARD_ORIGIN) {
        return route.abort('failed');
      }
      return route.continue();
    });

    // Avoid waiting for networkidle: socket.io retries can keep the network busy.
    await page.goto(DASHBOARD_URL, { waitUntil: 'domcontentloaded' });

    // Basic page smoke
    await expect(page.locator('.dashboard-container')).toBeVisible();

    // Connection should go to disconnected after socket.io fails.
    await expect(page.locator('#connection-status')).toHaveText('Getrennt');

    // Degraded banner should be visible.
    const banner = page.locator('.ui-global-degraded-banner');
    await expect(banner).toBeVisible();
    await expect(banner).toHaveClass(/is-visible/);

    // Create an isolated error state host to deterministically test the retry CTA behavior.
    // (The zone retry in the dashboard replaces DOM, which makes button-state assertions flaky.)
    await page.evaluate(() => {
      const existing = document.getElementById('e2e-offline-guard-host');
      if (existing) return;

      const host = document.createElement('div');
      host.id = 'e2e-offline-guard-host';
      host.style.position = 'fixed';
      host.style.left = '16px';
      host.style.bottom = '16px';
      host.style.width = '420px';
      host.style.zIndex = '99999';
      document.body.appendChild(host);

      const toolkit = window.UiState?.UiStateToolkit
        ? new window.UiState.UiStateToolkit({ scope: 'e2e-offline-guards', degradedBanner: null })
        : null;

      if (!toolkit) {
        host.textContent = 'UiStateToolkit missing';
        return;
      }

      toolkit.error(host, {
        source: 'e2e:offline-guards',
        title: 'Offline Guard (E2E)',
        message: 'Netzwerk ist offline / Core nicht erreichbar.',
        detail: 'Primary CTA must guard against repeated clicks; retry remains possible.',
        degraded: true,
        actionLabel: 'Erneut versuchen',
        // Make it long enough to assert the disabled state.
        onRetry: () => new Promise((resolve) => setTimeout(resolve, 800)),
      });
    });

    const retry = page.locator('#e2e-offline-guard-host [data-ui-state-action="error"]');
    await expect(retry).toBeVisible();
    await expect(retry).toHaveText('Erneut versuchen');

    // 1st retry: CTA disables while running
    await retry.click();
    await expect(retry).toBeDisabled({ timeout: 1000 });
    await expect(retry).toHaveText('Bitte warten...');
    await expect(retry).toBeEnabled({ timeout: 2000 });
    await expect(retry).toHaveText('Erneut versuchen');

    // 2nd retry: still possible (guard doesn't permanently lock)
    await retry.click();
    await expect(retry).toBeDisabled({ timeout: 1000 });
    await expect(retry).toBeEnabled({ timeout: 2000 });
  });
});
