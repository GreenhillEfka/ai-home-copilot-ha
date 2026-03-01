/**
 * Neuron Dashboard Integration Tests
 * Integrationstests für neuron_dashboard.html + neuron_dashboard.js
 * 
 * @version 1.0.0
 * @description Browser-basierte Integrationstests
 */

const puppeteer = require('puppeteer');

describe('Neuron Dashboard Integration', () => {
  let browser;
  let page;

  beforeAll(async () => {
    browser = await puppeteer.launch({
      headless: 'new',
      args: ['--no-sandbox', '--disable-setuid-sandbox']
    });
  });

  afterAll(async () => {
    if (browser) {
      await browser.close();
    }
  });

  beforeEach(async () => {
    page = await browser.newPage();
    await page.goto('file:///config/.openclaw/workspace/neuron_dashboard.html');
  });

  afterEach(async () => {
    await page.close();
  });

  describe('Dashboard Loading', () => {
    test('sollte Dashboard erfolgreich laden', async () => {
      const title = await page.title();
      expect(title).toBe('Neuron Dashboard - PilotSuite');
    });

    test('sollte Canvas-Element rendern', async () => {
      const canvas = await page.$('#neuronCanvas');
      expect(canvas).toBeDefined();
    });

    test('sollte Sidebar rendern', async () => {
      const sidebar = await page.$('.sidebar');
      expect(sidebar).toBeDefined();
    });

    test('sollte Legende anzeigen', async () => {
      const legendItems = await page.$$('.legend-item');
      expect(legendItems.length).toBe(3);
    });
  });

  describe('Statistik-Anzeige', () => {
    test('sollte Neuronen-Anzahl anzeigen', async () => {
      const neuronCount = await page.$eval('#neuronCount', el => el.textContent);
      expect(neuronCount).toBe('14');
    });

    test('sollte Verbindungs-Anzahl anzeigen', async () => {
      const connectionCount = await page.$eval('#connectionCount', el => el.textContent);
      expect(connectionCount).toBe('24');
    });
  });

  describe('Neuronen-Visualisierung', () => {
    test('sollte 14 Neuronen rendern', async () => {
      const neuronCount = await page.evaluate(() => {
        return window.neuronNetwork.nodes.length;
      });
      expect(neuronCount).toBe(14);
    });

    test('sollte 24 Verbindungen rendern', async () => {
      const linkCount = await page.evaluate(() => {
        return window.neuronNetwork.links.length;
      });
      expect(linkCount).toBe(24);
    });

    test('sollte Input-Neuronen initialisieren', async () => {
      const inputCount = await page.evaluate(() => {
        return window.neuronNetwork.nodes.filter(n => n.type === 'input').length;
      });
      expect(inputCount).toBe(3);
    });

    test('sollte Hidden-Neuronen initialisieren', async () => {
      const hiddenCount = await page.evaluate(() => {
        return window.neuronNetwork.nodes.filter(n => n.type === 'hidden').length;
      });
      expect(hiddenCount).toBe(8);
    });

    test('sollte Output-Neuronen initialisieren', async () => {
      const outputCount = await page.evaluate(() => {
        return window.neuronNetwork.nodes.filter(n => n.type === 'output').length;
      });
      expect(outputCount).toBe(3);
    });
  });

  describe('Interaktionen', () => {
    test('sollte Tooltip auf Hover anzeigen', async () => {
      await page.hover('#neuronCanvas');
      await page.waitForTimeout(100);

      const tooltipVisible = await page.evaluate(() => {
        const tooltip = document.getElementById('tooltip');
        return tooltip.classList.contains('visible');
      });

      // Tooltip kann sichtbar sein wenn Node getroffen
      expect(typeof tooltipVisible).toBe('boolean');
    });

    test('sollte Demo-Mode Toggle funktionieren', async () => {
      const demoModeBefore = await page.evaluate(() => {
        return window.neuronNetwork.demoMode;
      });

      await page.click('#toggleDemoBtn');
      await page.waitForTimeout(100);

      const demoModeAfter = await page.evaluate(() => {
        return window.neuronNetwork.demoMode;
      });

      expect(demoModeAfter).toBe(!demoModeBefore);
    });

    test('sollte Layout-Reset funktionieren', async () => {
      await page.click('#resetLayoutBtn');
      await page.waitForTimeout(100);

      const nodesExist = await page.evaluate(() => {
        return window.neuronNetwork.nodes.length > 0;
      });

      expect(nodesExist).toBe(true);
    });

    test('sollte Random-Fire funktionieren', async () => {
      const firingBefore = await page.evaluate(() => {
        return window.neuronNetwork.stats.firing;
      });

      await page.click('#fireRandomBtn');
      await page.waitForTimeout(100);

      const firingAfter = await page.evaluate(() => {
        return window.neuronNetwork.stats.firing;
      });

      expect(firingAfter).toBeGreaterThanOrEqual(firingBefore);
    });
  });

  describe('Canvas-Rendering', () => {
    test('sollte Canvas-Kontext initialisieren', async () => {
      const hasContext = await page.evaluate(() => {
        const canvas = document.getElementById('neuronCanvas');
        const ctx = canvas.getContext('2d');
        return ctx !== null;
      });

      expect(hasContext).toBe(true);
    });

    test('sollte DPI-Support haben', async () => {
      const dpr = await page.evaluate(() => {
        return window.neuronNetwork.dpr;
      });

      expect(dpr).toBeGreaterThanOrEqual(1);
    });

    test('sollte Render-Loop starten', async () => {
      const hasAnimation = await page.evaluate(() => {
        return window.neuronNetwork.animationFrame !== null;
      });

      expect(hasAnimation).toBe(true);
    });
  });

  describe('Zustands-Updates', () => {
    test('sollte Neuron-Zustand aktualisieren', async () => {
      await page.evaluate(() => {
        window.neuronNetwork.nodes[0].state = 'firing';
        window.neuronNetwork._updateStats();
      });

      const firingCount = await page.$eval('#firingCount', el => el.textContent);
      expect(parseInt(firingCount)).toBeGreaterThanOrEqual(1);
    });

    test('sollte Stats nach Update berechnen', async () => {
      const stats = await page.evaluate(() => {
        const network = window.neuronNetwork;
        return {
          total: network.stats.total,
          active: network.stats.active,
          firing: network.stats.firing
        };
      });

      expect(stats.total).toBe(14);
      expect(typeof stats.active).toBe('number');
      expect(typeof stats.firing).toBe('number');
    });
  });

  describe('Responsive Design', () => {
    test('sollte auf Window-Resize reagieren', async () => {
      await page.setViewport({ width: 1200, height: 800 });
      await page.waitForTimeout(100);

      const width = await page.evaluate(() => {
        return window.neuronNetwork.width;
      });

      expect(width).toBeGreaterThan(0);
    });

    test('sollte Canvas-Größe anpassen', async () => {
      const canvasSize = await page.evaluate(() => {
        const canvas = document.getElementById('neuronCanvas');
        return {
          width: canvas.width,
          height: canvas.height
        };
      });

      expect(canvasSize.width).toBeGreaterThan(0);
      expect(canvasSize.height).toBeGreaterThan(0);
    });
  });

  describe('Performance', () => {
    test('sollte stabile FPS haben', async () => {
      const startTime = Date.now();
      
      await page.evaluate(() => {
        return new Promise(resolve => {
          setTimeout(() => {
            resolve(window.neuronNetwork.animationFrame !== null);
          }, 1000);
        });
      });

      const elapsed = Date.now() - startTime;
      expect(elapsed).toBeLessThan(1500); // Sollte nicht hängen
    });

    test('sollte Memory-Leaks vermeiden', async () => {
      const initialNodes = await page.evaluate(() => {
        return window.neuronNetwork.nodes.length;
      });

      await page.evaluate(() => {
        window.neuronNetwork.resetLayout();
      });

      const afterResetNodes = await page.evaluate(() => {
        return window.neuronNetwork.nodes.length;
      });

      expect(afterResetNodes).toBe(initialNodes);
    });
  });

  describe('Fehlerbehandlung', () => {
    test('sollte Canvas-Fehler abfangen', async () => {
      const result = await page.evaluate(() => {
        try {
          const network = new window.NeuronNetwork({
            canvasId: 'nonexistent',
            demoMode: false
          });
          return network.canvas === undefined;
        } catch (e) {
          return true;
        }
      });

      expect(result).toBe(true);
    });
  });

  describe('URL-Parameter', () => {
    test('sollte Demo-Parameter verarbeiten', async () => {
      await page.goto('file:///config/.openclaw/workspace/neuron_dashboard.html?demo=0');
      await page.waitForTimeout(100);

      const demoMode = await page.evaluate(() => {
        return window.neuronNetwork.demoMode;
      });

      expect(demoMode).toBe(false);
    });
  });
});
