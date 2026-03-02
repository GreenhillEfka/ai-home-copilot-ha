/**
 * PilotSuite Styx - E2E Test Fixtures
 * Playwright fixtures for Dashboard UI tests
 * 
 * Provides:
 * - Authentication helpers
 * - Navigation utilities
 * - Theme toggle helpers
 * - Viewport configurations
 */

import { test as base, expect, Page, BrowserContext } from '@playwright/test';

// Viewport configurations for responsive testing
export const viewports = {
  mobile: { width: 375, height: 667, name: 'mobile' },
  tablet: { width: 768, height: 1024, name: 'tablet' },
  desktop: { width: 1920, height: 1080, name: 'desktop' }
};

// Dashboard URL configuration
const DASHBOARD_URL = process.env.DASHBOARD_URL || 'http://localhost:8766/dashboard';

// Test fixture extensions
type Fixtures = {
  dashboardPage: DashboardPage;
  authenticatedContext: BrowserContext;
};

/**
 * Dashboard Page Object Model
 */
export class DashboardPage {
  constructor(public page: Page) {}

  /**
   * Navigate to dashboard
   */
  async goto() {
    await this.page.goto(DASHBOARD_URL);
    await this.page.waitForLoadState('networkidle');
  }

  /**
   * Wait for dashboard to be fully loaded
   */
  async waitForLoaded() {
    await this.page.waitForSelector('.dashboard-container', { state: 'visible' });
    await this.page.waitForSelector('.tab-navigation', { state: 'visible' });
    await this.page.waitForSelector('.main-content', { state: 'visible' });
  }

  /**
   * Wait for loading overlay to disappear
   */
  async waitForLoadingComplete() {
    await this.page.waitForSelector('#loading-overlay', { state: 'hidden' });
  }

  /**
   * Get all zone tabs
   */
  async getZoneTabs() {
    return this.page.locator('.tab-item');
  }

  /**
   * Switch to a specific zone tab
   */
  async switchToZone(zoneId: string) {
    const tab = this.page.locator(`.tab-item[data-zone="${zoneId}"]`);
    await tab.click();
    await this.page.waitForTimeout(500); // Allow transition
  }

  /**
   * Get current active tab
   */
  async getActiveTab() {
    const activeTab = this.page.locator('.tab-item.active');
    return await activeTab.getAttribute('data-zone');
  }

  /**
   * Toggle theme (dark/light mode)
   */
  async toggleTheme() {
    const themeToggle = this.page.locator('#theme-toggle');
    await themeToggle.click();
    await this.page.waitForTimeout(300);
  }

  /**
   * Get current theme
   */
  async getTheme() {
    return await this.page.evaluate(() => {
      return document.documentElement.getAttribute('data-theme') || 'light';
    });
  }

  /**
   * Check if zone cards are loaded
   */
  async waitForZoneCards(zoneId: string) {
    const zoneGrid = this.page.locator(`#grid-${zoneId}`);
    await zoneGrid.waitFor({ state: 'visible' });
  }

  /**
   * Get active alerts count
   */
  async getAlertsCount() {
    const alertBadge = this.page.locator('#alert-badge');
    const text = await alertBadge.textContent();
    return parseInt(text || '0', 10);
  }

  /**
   * Take full page screenshot
   */
  async takeScreenshot(name: string) {
    return await this.page.screenshot({
      fullPage: true,
      path: `tests/e2e/screenshots/${name}.png`
    });
  }

  /**
   * Take screenshot of specific element
   */
  async takeElementScreenshot(selector: string, name: string) {
    const element = this.page.locator(selector);
    await element.waitFor({ state: 'visible' });
    return await element.screenshot({
      path: `tests/e2e/screenshots/${name}.png`
    });
  }
}

/**
 * Base test fixture with dashboard page
 */
export const test = base.extend<Fixtures>({
  dashboardPage: async ({ page }, use) => {
    const dashboardPage = new DashboardPage(page);
    await use(dashboardPage);
  },

  authenticatedContext: async ({ context }, use) => {
    // Add authentication headers if needed
    // For now, dashboard is publicly accessible
    await use(context);
  }
});

/**
 * Helper to run tests across all viewports
 */
export function testAcrossViewports(
  name: string,
  fn: (page: Page, viewport: typeof viewports[keyof typeof viewports]) => Promise<void>
) {
  Object.entries(viewports).forEach(([viewportName, viewport]) => {
    test(`${name} - ${viewportName}`, async ({ page }) => {
      await page.setViewportSize({ 
        width: viewport.width, 
        height: viewport.height 
      });
      await fn(page, viewport);
    });
  });
}

/**
 * Helper to run tests in both themes
 */
export function testAcrossThemes(
  name: string,
  fn: (page: Page, theme: string) => Promise<void>
) {
  ['light', 'dark'].forEach((theme) => {
    test(`${name} - ${theme} mode`, async ({ page, dashboardPage }) => {
      const currentTheme = await dashboardPage.getTheme();
      if (currentTheme !== theme) {
        await dashboardPage.toggleTheme();
      }
      await fn(page, theme);
    });
  });
}

export { expect };
export default test;
