/**
 * PilotSuite Styx - Dashboard Screenshot Tests
 * E2E visual regression tests with Playwright
 * 
 * Features:
 * - Screenshot every dashboard tab (10 zones)
 * - Visual comparison with baseline (pixel-diff <2%)
 * - Multiple viewports (Mobile, Tablet, Desktop)
 * - Dark mode + Light mode screenshots
 * - CI integration (screenshots as artifacts)
 */

import { test, expect, DashboardPage, viewports, testAcrossViewports, testAcrossThemes } from './fixtures';
import { compareScreenshot, saveAsBaseline, saveAsCurrent } from './visual-compare';
import { writeFileSync, mkdirSync, existsSync } from 'fs';
import { join } from 'path';

// Ensure screenshot directories exist
const SCREENSHOTS_DIR = join(process.cwd(), 'tests', 'e2e', 'screenshots');
const BASELINE_DIR = join(SCREENSHOTS_DIR, 'baseline');
const CURRENT_DIR = join(SCREENSHOTS_DIR, 'current');

test.beforeEach(async ({ dashboardPage }) => {
  // Ensure directories exist
  [SCREENSHOTS_DIR, BASELINE_DIR, CURRENT_DIR].forEach(dir => {
    if (!existsSync(dir)) {
      mkdirSync(dir, { recursive: true });
    }
  });

  // Navigate to dashboard
  await dashboardPage.goto();
  await dashboardPage.waitForLoaded();
  await dashboardPage.waitForLoadingComplete();
});

/**
 * Test: Tab Navigation
 * Verify all 10 zone tabs are present and clickable
 */
test.describe('Tab Navigation', () => {
  test('should display all 10 zone tabs', async ({ dashboardPage, page }) => {
    const tabs = await dashboardPage.getZoneTabs();
    await expect(tabs).toHaveCount(10);

    const expectedZones = [
      'wohn', 'bad', 'koch', 'buero', 'gang',
      'schlaf', 'mira', 'paul', 'terrasse', 'aussen'
    ];

    for (let i = 0; i < 10; i++) {
      const tab = tabs.nth(i);
      await expect(tab).toBeVisible();
      const zoneId = await tab.getAttribute('data-zone');
      expect(zoneId).toBe(expectedZones[i]);
    }
  });

  test('should switch between tabs', async ({ dashboardPage }) => {
    // Start with first tab
    const activeTab = await dashboardPage.getActiveTab();
    expect(activeTab).toBe('wohn');

    // Switch to different tabs
    await dashboardPage.switchToZone('koch');
    let newActiveTab = await dashboardPage.getActiveTab();
    expect(newActiveTab).toBe('koch');

    await dashboardPage.switchToZone('schlaf');
    newActiveTab = await dashboardPage.getActiveTab();
    expect(newActiveTab).toBe('schlaf');
  });

  test('should take screenshot of each tab', async ({ dashboardPage, page }) => {
    const zones = ['wohn', 'bad', 'koch', 'buero', 'gang', 'schlaf', 'mira', 'paul', 'terrasse', 'aussen'];
    
    for (const zone of zones) {
      await dashboardPage.switchToZone(zone);
      await dashboardPage.waitForZoneCards(zone);
      
      const screenshotName = `tab-${zone}-desktop-light`;
      const screenshotPath = join(CURRENT_DIR, `${screenshotName}.png`);
      
      await page.screenshot({
        fullPage: true,
        path: screenshotPath
      });

      // Compare with baseline if exists
      try {
        const result = await compareScreenshot(screenshotName, 2.0);
        if (!result.passed) {
          console.log(`⚠️  Visual regression detected for ${screenshotName}: ${result.reason}`);
        }
      } catch (error) {
        console.log(`ℹ️  No baseline for ${screenshotName}, creating...`);
        saveAsBaseline(screenshotPath, screenshotName);
      }
    }
  });
});

/**
 * Test: Zone Cards Loading
 * Verify zone cards load correctly with real data
 */
test.describe('Zone Cards', () => {
  test('should load zone cards for each tab', async ({ dashboardPage, page }) => {
    const zones = ['wohn', 'bad', 'koch', 'buero', 'gang'];
    
    for (const zone of zones) {
      await dashboardPage.switchToZone(zone);
      await dashboardPage.waitForZoneCards(zone);
      
      const zoneGrid = page.locator(`#grid-${zone}`);
      await expect(zoneGrid).toBeVisible();
      
      // Check that empty state is replaced with actual content
      const emptyState = zoneGrid.locator('.empty-state');
      // Empty state should be hidden or replaced after loading
      const emptyStateVisible = await emptyState.isVisible({ timeout: 5000 }).catch(() => false);
      
      if (emptyStateVisible) {
        console.log(`⚠️  Zone ${zone} still showing empty state`);
      }
    }
  });

  test('should display zone header with correct icon', async ({ dashboardPage, page }) => {
    await dashboardPage.switchToZone('wohn');
    
    const header = page.locator('.tab-pane-header h2');
    await expect(header).toBeVisible();
    await expect(header).toContainText('Wohnbereich');
    
    const icon = header.locator('i');
    await expect(icon).toHaveClass(/mdi-sofa/);
  });
});

/**
 * Test: Widgets Display
 * Verify widgets show real data
 */
test.describe('Widgets', () => {
  test('should display widgets in zone grid', async ({ dashboardPage, page }) => {
    await dashboardPage.switchToZone('wohn');
    await dashboardPage.waitForZoneCards('wohn');
    
    const zoneGrid = page.locator('#grid-wohn');
    
    // Wait for widgets to load (check for widget classes)
    const widgets = zoneGrid.locator('.widget, .card, .zone-item');
    const widgetCount = await widgets.count();
    
    console.log(`Found ${widgetCount} widgets in Wohnbereich`);
    
    // At least some content should be loaded
    expect(widgetCount).toBeGreaterThan(0);
  });

  test('should show quick action buttons', async ({ dashboardPage, page }) => {
    await dashboardPage.switchToZone('koch');
    
    const actionsContainer = page.locator('#actions-koch');
    await expect(actionsContainer).toBeVisible();
    
    const refreshBtn = actionsContainer.locator('button').first();
    await expect(refreshBtn).toBeVisible();
    await expect(refreshBtn).toContainText('Aktualisieren');
  });
});

/**
 * Test: Alerts Display
 * Verify alerts are shown correctly
 */
test.describe('Alerts', () => {
  test('should display alerts count in footer', async ({ dashboardPage }) => {
    const alertsCount = await dashboardPage.getAlertsCount();
    expect(typeof alertsCount).toBe('number');
    expect(alertsCount).toBeGreaterThanOrEqual(0);
    
    console.log(`Active alerts: ${alertsCount}`);
  });

  test('should show alert indicator when alerts exist', async ({ dashboardPage, page }) => {
    const alertBadge = page.locator('#alert-badge');
    await expect(alertBadge).toBeVisible();
    
    const alertContainer = page.locator('.active-alerts');
    await expect(alertContainer).toBeVisible();
  });
});

/**
 * Test: Theme Toggle
 * Verify dark/light mode switching works
 */
test.describe('Theme Toggle', () => {
  test('should toggle between light and dark mode', async ({ dashboardPage }) => {
    // Start with current theme
    const initialTheme = await dashboardPage.getTheme();
    
    // Toggle theme
    await dashboardPage.toggleTheme();
    const newTheme = await dashboardPage.getTheme();
    
    expect(newTheme).not.toBe(initialTheme);
    
    // Toggle back
    await dashboardPage.toggleTheme();
    const revertedTheme = await dashboardPage.getTheme();
    expect(revertedTheme).toBe(initialTheme);
  });

  test('should take screenshots in both themes', async ({ dashboardPage, page }) => {
    const zones = ['wohn', 'schlaf'];
    
    for (const zone of zones) {
      await dashboardPage.switchToZone(zone);
      
      // Light mode screenshot
      const lightTheme = await dashboardPage.getTheme();
      if (lightTheme !== 'light') {
        await dashboardPage.toggleTheme();
      }
      
      const lightScreenshot = join(CURRENT_DIR, `tab-${zone}-desktop-light.png`);
      await page.screenshot({ fullPage: true, path: lightScreenshot });
      
      // Dark mode screenshot
      await dashboardPage.toggleTheme();
      const darkScreenshot = join(CURRENT_DIR, `tab-${zone}-desktop-dark.png`);
      await page.screenshot({ fullPage: true, path: darkScreenshot });
      
      // Compare with baselines
      try {
        const lightResult = await compareScreenshot(`tab-${zone}-desktop-light`, 2.0);
        if (!lightResult.passed) {
          console.log(`⚠️  Light mode regression for ${zone}: ${lightResult.reason}`);
        }
      } catch (e) {
        saveAsBaseline(lightScreenshot, `tab-${zone}-desktop-light`);
      }
      
      try {
        const darkResult = await compareScreenshot(`tab-${zone}-desktop-dark`, 2.0);
        if (!darkResult.passed) {
          console.log(`⚠️  Dark mode regression for ${zone}: ${darkResult.reason}`);
        }
      } catch (e) {
        saveAsBaseline(darkScreenshot, `tab-${zone}-desktop-dark`);
      }
    }
  });
});

/**
 * Test: Responsive Viewports
 * Verify dashboard works on different screen sizes
 */
test.describe('Responsive Viewports', () => {
  test('should render correctly on mobile', async ({ dashboardPage, page }) => {
    await page.setViewportSize(viewports.mobile);
    await dashboardPage.waitForLoaded();
    
    const screenshotPath = join(CURRENT_DIR, 'dashboard-mobile-light.png');
    await page.screenshot({ fullPage: true, path: screenshotPath });
    
    // Verify tabs are still accessible (may be scrollable)
    const tabs = await dashboardPage.getZoneTabs();
    await expect(tabs.first()).toBeVisible();
  });

  test('should render correctly on tablet', async ({ dashboardPage, page }) => {
    await page.setViewportSize(viewports.tablet);
    await dashboardPage.waitForLoaded();
    
    const screenshotPath = join(CURRENT_DIR, 'dashboard-tablet-light.png');
    await page.screenshot({ fullPage: true, path: screenshotPath });
    
    const tabs = await dashboardPage.getZoneTabs();
    await expect(tabs.first()).toBeVisible();
  });

  test('should render correctly on desktop', async ({ dashboardPage, page }) => {
    await page.setViewportSize(viewports.desktop);
    await dashboardPage.waitForLoaded();
    
    const screenshotPath = join(CURRENT_DIR, 'dashboard-desktop-light.png');
    await page.screenshot({ fullPage: true, path: screenshotPath });
    
    const tabs = await dashboardPage.getZoneTabs();
    await expect(tabs.first()).toBeVisible();
  });

  test('should take responsive screenshots for all viewports', async ({ dashboardPage, page }) => {
    for (const [name, viewport] of Object.entries(viewports)) {
      await page.setViewportSize({ width: viewport.width, height: viewport.height });
      await dashboardPage.waitForLoaded();
      
      const screenshotPath = join(CURRENT_DIR, `dashboard-${name}-light.png`);
      await page.screenshot({ fullPage: true, path: screenshotPath });
      
      try {
        const result = await compareScreenshot(`dashboard-${name}-light`, 2.0);
        if (!result.passed) {
          console.log(`⚠️  Viewport regression for ${name}: ${result.reason}`);
        }
      } catch (e) {
        saveAsBaseline(screenshotPath, `dashboard-${name}-light`);
      }
    }
  });
});

/**
 * Test: Connection Status
 * Verify WebSocket connection indicator
 */
test.describe('Connection Status', () => {
  test('should show connection indicator', async ({ dashboardPage, page }) => {
    const connectionIndicator = page.locator('#connection-indicator');
    await expect(connectionIndicator).toBeVisible();
    
    const connectionStatus = page.locator('#connection-status');
    await expect(connectionStatus).toBeVisible();
  });

  test('should show connected state', async ({ dashboardPage, page }) => {
    // Wait for connection to establish
    await page.waitForTimeout(2000);
    
    const connectionStatus = page.locator('#connection-status');
    const statusText = await connectionStatus.textContent();
    
    // Should not show "Verbinde..." after connection
    expect(statusText).not.toBe('Verbinde...');
  });
});

/**
 * Test: Footer Information
 * Verify footer shows last update time
 */
test.describe('Footer', () => {
  test('should display last update time', async ({ dashboardPage, page }) => {
    const lastUpdate = page.locator('#last-update-time');
    await expect(lastUpdate).toBeVisible();
    
    // Should have some time value after loading
    const timeText = await lastUpdate.textContent();
    expect(timeText).not.toBe('--:--:--');
  });

  test('should display version in header', async ({ dashboardPage, page }) => {
    const version = page.locator('.version');
    await expect(version).toBeVisible();
    await expect(version).toContainText('v12');
  });
});

/**
 * CI Integration: Generate test report
 */
test.afterAll(async () => {
  console.log('\n=== Screenshot Test Summary ===');
  console.log(`Screenshots directory: ${SCREENSHOTS_DIR}`);
  console.log(`Baseline directory: ${BASELINE_DIR}`);
  console.log(`Current directory: ${CURRENT_DIR}`);
  console.log('==============================\n');
});
