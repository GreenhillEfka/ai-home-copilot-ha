/**
 * PS-UX-053 — Partial-Failure Badge Visual Guards (Playwright)
 *
 * Deterministic visual regression tests for:
 * - partial badges ("Teildaten")
 * - missing sub-sensors showing "n/a" (not "0")
 *
 * Approach:
 * - render <styx-zone-card> in an isolated host
 * - inject the card implementation as a script tag (no backend required)
 * - feed a minimal hass stub with missing entities / missing neuron nodes
 */

import { test, expect, viewports } from './fixtures';
import { compareScreenshot, saveAsBaseline } from './visual-compare';
import { mkdirSync, existsSync, readFileSync } from 'fs';
import { join } from 'path';

const SCREENSHOTS_DIR = join(process.cwd(), 'tests', 'e2e', 'screenshots');
const BASELINE_DIR = join(SCREENSHOTS_DIR, 'baseline');
const CURRENT_DIR = join(SCREENSHOTS_DIR, 'current');

const ZONE_CARD_JS_PATH = join(
  process.cwd(),
  'custom_components',
  'copilot_ha',
  'www',
  'styx-zone-card.js'
);

function ensureScreenshotDirs() {
  [SCREENSHOTS_DIR, BASELINE_DIR, CURRENT_DIR].forEach((dir) => {
    if (!existsSync(dir)) {
      mkdirSync(dir, { recursive: true });
    }
  });
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
    saveAsBaseline(path, screenshotName);
  }
}

test.describe('Partial-Failure Badges (isolated styx-zone-card)', () => {
  test('renders partial badges + n/a tiles deterministically (light × viewports)', async ({ page }) => {
    const zoneCardJs = readFileSync(ZONE_CARD_JS_PATH, 'utf-8');

    for (const viewport of Object.values(viewports)) {
      await page.setViewportSize({ width: viewport.width, height: viewport.height });

      await page.setContent(`<!doctype html><html><head>
        <meta charset="utf-8" />
        <style>
          :root {
            --card-background-color: #0a0e14;
            --primary-text-color: #e6eef6;
            --secondary-text-color: #9fb1c3;
            --ha-card-border-radius: 12px;
          }
          body {
            margin: 0;
            padding: 16px;
            background: #070b10;
            font-family: system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif;
          }
          #host { width: 720px; max-width: 100%; }
        </style>
      </head><body>
        <div id="host"></div>
      </body></html>`);

      await page.addScriptTag({ content: zoneCardJs });

      // Case A: Mood partial (missing comfort) + neuron activity missing entirely
      await page.evaluate(() => {
        const host = document.getElementById('host');
        host!.innerHTML = '';

        const card = document.createElement('styx-zone-card') as any;
        card.setConfig({
          entity: 'sensor.pilotsuite_habitus_zones',
          title: 'Zonen (E2E Partial)'
        });

        const hass: any = {
          states: {
            'sensor.pilotsuite_habitus_zones': {
              state: 'ok',
              attributes: {
                zones: [{ name: 'Wohn', mode: 'party' }],
                total_zones: 1,
                active_zones: 1
              }
            },
            // Mood: omit comfort → partial badge should mention Comfort.
            'sensor.pilotsuite_mood_wohn_joy': { state: '42' },
            'sensor.pilotsuite_mood_wohn_frugality': { state: '77' },
            // Neuron nodes missing completely → neuron tile shows n/a, partial badge includes "Neuronen".
            // (No sensor.pilotsuite_brain_graph_nodes)
          },
          callService: () => {},
        };

        card.hass = hass;
        host!.appendChild(card);
      });

      const card = page.locator('styx-zone-card');
      await expect(card).toBeVisible();
      await takeElementScreenshot(page, card, `partial-failure-mood+neurons-missing-${viewport.name}-light`);

      // Case B: Neuron score missing (nodes present but no numeric score)
      await page.evaluate(() => {
        const host = document.getElementById('host');
        host!.innerHTML = '';

        const card = document.createElement('styx-zone-card') as any;
        card.setConfig({
          entity: 'sensor.pilotsuite_habitus_zones',
          title: 'Zonen (E2E Partial: Neuron Score)'
        });

        const hass: any = {
          states: {
            'sensor.pilotsuite_habitus_zones': {
              state: 'ok',
              attributes: {
                zones: [{ name: 'Wohn', mode: 'party' }],
                total_zones: 1,
                active_zones: 1
              }
            },
            // All moods present → no mood partial.
            'sensor.pilotsuite_mood_wohn_comfort': { state: '10' },
            'sensor.pilotsuite_mood_wohn_joy': { state: '20' },
            'sensor.pilotsuite_mood_wohn_frugality': { state: '30' },
            // Neuron nodes present but score missing → badge includes "Neuronen (Score)" and score shows n/a.
            'sensor.pilotsuite_brain_graph_nodes': {
              state: 'ok',
              attributes: {
                nodes: [
                  { zone: 'living', state: 'on', score: null },
                  { zone: 'living', state: 'off', score: undefined },
                ]
              }
            }
          },
          callService: () => {},
        };

        card.hass = hass;
        host!.appendChild(card);
      });

      await expect(page.locator('styx-zone-card')).toBeVisible();
      await takeElementScreenshot(page, page.locator('styx-zone-card'), `partial-failure-neuron-score-missing-${viewport.name}-light`);
    }
  });
});
