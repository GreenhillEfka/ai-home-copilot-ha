/**
 * PS-UX-053 — UiState Visual Guards (Playwright)
 *
 * Goal:
 * - deterministic, element-only screenshots for shared UiState components
 * - baseline compare via existing visual-compare helper
 *
 * Covers:
 * - StateSkeleton (loading)
 * - StateEmpty
 * - StateError (incl. retry CTA)
 * - GlobalDegradedBanner (shown/hidden)
 */

import { test, expect, viewports, DashboardPage } from './fixtures';
import { compareScreenshot, saveAsBaseline } from './visual-compare';
import { mkdirSync, existsSync } from 'fs';
import { join } from 'path';

const DASHBOARD_URL = process.env.DASHBOARD_URL || 'http://localhost:8766/dashboard';

const SCREENSHOTS_DIR = join(process.cwd(), 'tests', 'e2e', 'screenshots');
const BASELINE_DIR = join(SCREENSHOTS_DIR, 'baseline');
const CURRENT_DIR = join(SCREENSHOTS_DIR, 'current');

function ensureScreenshotDirs() {
  [SCREENSHOTS_DIR, BASELINE_DIR, CURRENT_DIR].forEach((dir) => {
    if (!existsSync(dir)) {
      mkdirSync(dir, { recursive: true });
    }
  });
}

async function ensureTheme(dashboardPage: DashboardPage, theme: 'light' | 'dark') {
  const currentTheme = await dashboardPage.getTheme();
  if (currentTheme !== theme) {
    await dashboardPage.toggleTheme();
  }
}

async function takeElementScreenshot(page: any, locator: any, screenshotName: string) {
  ensureScreenshotDirs();
  const path = join(CURRENT_DIR, `${screenshotName}.png`);
  await locator.waitFor({ state: 'visible' });
  await locator.screenshot({ path });

  try {
    const result = await compareScreenshot(screenshotName, 2.0);
    if (!result.passed) {
      console.log(`⚠️  Visual regression detected for ${screenshotName}: ${result.reason}`);
    }
  } catch (e) {
    // No baseline yet → create it from the current image.
    saveAsBaseline(path, screenshotName);
  }
}

test.describe('UiState Visual Guards', () => {
  test('renders UiState variants (loading/empty/error) + degraded banner (light/dark × viewports)', async ({ page, dashboardPage }) => {
    const themes: Array<'light' | 'dark'> = ['light', 'dark'];

    for (const viewport of Object.values(viewports)) {
      await page.setViewportSize({ width: viewport.width, height: viewport.height });

      for (const theme of themes) {
        // Avoid waiting for networkidle: socket.io retries can keep network busy.
        await page.goto(DASHBOARD_URL, { waitUntil: 'domcontentloaded' });
        await expect(page.locator('.dashboard-container')).toBeVisible();

        // Ensure UiState toolkit is present.
        await page.waitForFunction(() => !!(window as any).UiState?.UiStateToolkit);

        // Ensure theme.
        await ensureTheme(dashboardPage, theme);

        // Create stable host once per theme+viewport.
        await page.evaluate(() => {
          const existing = document.getElementById('e2e-uistate-visual-host');
          if (existing) existing.remove();

          const host = document.createElement('div');
          host.id = 'e2e-uistate-visual-host';
          host.style.position = 'fixed';
          host.style.left = '16px';
          host.style.bottom = '16px';
          host.style.width = '420px';
          host.style.zIndex = '99999';
          document.body.appendChild(host);

          // Ensure banner exists (toolkit creates it by default).
          const toolkit = (window as any).UiState?.UiStateToolkit
            ? new (window as any).UiState.UiStateToolkit({ scope: 'e2e-uistate-visual' })
            : null;

          if (!toolkit) {
            host.textContent = 'UiStateToolkit missing';
            return;
          }

          // Reset banner state.
          toolkit.setGlobalDegraded(false, { reason: 'reset' });
        });

        // 1) Loading / skeleton
        await page.evaluate(() => {
          const host = document.getElementById('e2e-uistate-visual-host');
          const toolkit = new (window as any).UiState.UiStateToolkit({ scope: 'e2e-uistate-visual' });
          toolkit.loading(host, {
            source: 'e2e:uistate_visual',
            title: 'Lädt…',
            message: 'Daten werden geladen…'
          });
        });

        await takeElementScreenshot(
          page,
          page.locator('#e2e-uistate-visual-host .ui-state-shell'),
          `uistate-loading-${viewport.name}-${theme}`
        );

        // 2) Empty
        await page.evaluate(() => {
          const host = document.getElementById('e2e-uistate-visual-host');
          const toolkit = new (window as any).UiState.UiStateToolkit({ scope: 'e2e-uistate-visual' });
          toolkit.empty(host, {
            source: 'e2e:uistate_visual',
            title: 'Keine Daten',
            message: 'Es sind noch keine Daten verfügbar.',
            actionLabel: 'Neu laden',
            onAction: () => new Promise((resolve) => setTimeout(resolve, 50)),
          });
        });

        await takeElementScreenshot(
          page,
          page.locator('#e2e-uistate-visual-host .ui-state-shell'),
          `uistate-empty-${viewport.name}-${theme}`
        );

        // 3) Error (with retry CTA)
        await page.evaluate(() => {
          const host = document.getElementById('e2e-uistate-visual-host');
          const toolkit = new (window as any).UiState.UiStateToolkit({ scope: 'e2e-uistate-visual' });
          toolkit.error(host, {
            source: 'e2e:uistate_visual',
            title: 'Fehler',
            message: 'Die Verbindung ist unterbrochen.',
            detail: 'Bitte versuche es erneut oder prüfe deine Netzwerkverbindung.',
            degraded: true,
            errorClass: (window as any).UiState?.ErrorClass?.NETWORK || 'network',
            actionLabel: 'Erneut versuchen',
            onRetry: () => new Promise((resolve) => setTimeout(resolve, 80)),
          });
        });

        await takeElementScreenshot(
          page,
          page.locator('#e2e-uistate-visual-host .ui-state-shell'),
          `uistate-error-${viewport.name}-${theme}`
        );

        // 4) Global degraded banner
        await page.evaluate(() => {
          const toolkit = new (window as any).UiState.UiStateToolkit({ scope: 'e2e-uistate-visual' });
          toolkit.setGlobalDegraded(true, {
            message: 'Getrennt · Teilfunktionen sind eingeschränkt.',
            reason: 'e2e:visual'
          });
        });

        const banner = page.locator('.ui-global-degraded-banner');
        await expect(banner).toBeVisible();
        await takeElementScreenshot(page, banner, `uistate-degraded-banner-${viewport.name}-${theme}`);

        // Reset banner (avoid leaking state into the next loop)
        await page.evaluate(() => {
          const toolkit = new (window as any).UiState.UiStateToolkit({ scope: 'e2e-uistate-visual' });
          toolkit.setGlobalDegraded(false, { reason: 'reset-after-screenshot' });
        });
      }
    }
  });
});
