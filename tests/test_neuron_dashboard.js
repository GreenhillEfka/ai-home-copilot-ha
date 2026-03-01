/**
 * Neuron Dashboard Tests
 * Test-Suite für neuron_dashboard.js
 * 
 * @version 1.0.0
 * @description Unit-Tests für NeuronNetwork Klasse
 */

'use strict';

// Mock DOM Environment für Node.js
const { JSDOM } = require('jsdom');

describe('NeuronNetwork', () => {
  let dom;
  let canvas;
  let tooltip;

  beforeAll(() => {
    // DOM Mock Setup
    dom = new JSDOM('<!DOCTYPE html><html><body><canvas id="neuronCanvas"></canvas><div id="tooltip"></div></body></html>', {
      url: 'http://localhost',
      pretendToBeVisual: true
    });

    global.window = dom.window;
    global.document = dom.window.document;
    global.requestAnimationFrame = (cb) => setTimeout(cb, 16);
    global.cancelAnimationFrame = (id) => clearTimeout(id);

    // D3 Mock
    global.d3 = {
      forceSimulation: jest.fn(() => ({
        force: jest.fn().mockReturnThis(),
        velocityDecay: jest.fn().mockReturnThis(),
        alphaMin: jest.fn().mockReturnThis(),
        on: jest.fn(),
        nodes: jest.fn(),
        alpha: jest.fn().mockReturnThis(),
        restart: jest.fn(),
        stop: jest.fn()
      })),
      forceLink: jest.fn(() => ({
        id: jest.fn().mockReturnThis(),
        distance: jest.fn().mockReturnThis()
      })),
      forceManyBody: jest.fn(() => ({
        strength: jest.fn().mockReturnThis())
      })),
      forceCenter: jest.fn(() => ({})),
      forceCollide: jest.fn(() => ({
        radius: jest.fn().mockReturnThis())
      })),
      forceX: jest.fn(() => ({
        strength: jest.fn().mockReturnThis())
      })),
      drag: jest.fn(() => ({
        on: jest.fn()
      }))
    };

    canvas = document.getElementById('neuronCanvas');
    tooltip = document.getElementById('tooltip');
  });

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Initialisierung', () => {
    test('sollte NeuronNetwork erfolgreich initialisieren', () => {
      const { NeuronNetwork } = require('./neuron_dashboard.js');
      const network = new NeuronNetwork({
        canvasId: 'neuronCanvas',
        tooltipId: 'tooltip',
        demoMode: false
      });

      expect(network).toBeDefined();
      expect(network.nodes).toBeDefined();
      expect(network.links).toBeDefined();
    });

    test('sollte 14 Neuronen erstellen', () => {
      const { NeuronNetwork } = require('./neuron_dashboard.js');
      const network = new NeuronNetwork({ demoMode: false });

      expect(network.nodes.length).toBe(14);
    });

    test('sollte 24 Verbindungen erstellen', () => {
      const { NeuronNetwork } = require('./neuron_dashboard.js');
      const network = new NeuronNetwork({ demoMode: false });

      expect(network.links.length).toBe(24);
    });

    test('sollte 3 Input-Neuronen haben', () => {
      const { NeuronNetwork } = require('./neuron_dashboard.js');
      const network = new NeuronNetwork({ demoMode: false });

      const inputNodes = network.nodes.filter(n => n.type === 'input');
      expect(inputNodes.length).toBe(3);
    });

    test('sollte 8 Hidden-Neuronen haben', () => {
      const { NeuronNetwork } = require('./neuron_dashboard.js');
      const network = new NeuronNetwork({ demoMode: false });

      const hiddenNodes = network.nodes.filter(n => n.type === 'hidden');
      expect(hiddenNodes.length).toBe(8);
    });

    test('sollte 3 Output-Neuronen haben', () => {
      const { NeuronNetwork } = require('./neuron_dashboard.js');
      const network = new NeuronNetwork({ demoMode: false });

      const outputNodes = network.nodes.filter(n => n.type === 'output');
      expect(outputNodes.length).toBe(3);
    });
  });

  describe('Neuronen-Zustände', () => {
    test('sollte NEURON_STATES Konstanten definieren', () => {
      expect(NEURON_STATES.INACTIVE).toBe('inactive');
      expect(NEURON_STATES.ACTIVE).toBe('active');
      expect(NEURON_STATES.FIRING).toBe('firing');
    });

    test('sollte NEURON_COLORS definieren', () => {
      expect(NEURON_COLORS.inactive).toBe('#666666');
      expect(NEURON_COLORS.active).toBe('#4CAF50');
      expect(NEURON_COLORS.firing).toBe('#FF5722');
    });

    test('sollte LAYER_COLORS definieren', () => {
      expect(LAYER_COLORS.input).toBe('#2196F3');
      expect(LAYER_COLORS.hidden).toBe('#9C27B0');
      expect(LAYER_COLORS.output).toBe('#FF9800');
    });

    test('sollte initiale Zustände korrekt setzen', () => {
      const { NeuronNetwork } = require('./neuron_dashboard.js');
      const network = new NeuronNetwork({ demoMode: false });

      const inputNodes = network.nodes.filter(n => n.type === 'input');
      inputNodes.forEach(node => {
        expect(node.state).toBe(NEURON_STATES.ACTIVE);
      });
    });
  });

  describe('Verbindungen', () => {
    test('sollte gewichtete Verbindungen erstellen', () => {
      const { NeuronNetwork } = require('./neuron_dashboard.js');
      const network = new NeuronNetwork({ demoMode: false });

      network.links.forEach(link => {
        expect(link).toHaveProperty('weight');
        expect(typeof link.weight).toBe('number');
      });
    });

    test('sollte positive und negative Gewichte haben', () => {
      const { NeuronNetwork } = require('./neuron_dashboard.js');
      const network = new NeuronNetwork({ demoMode: false });

      const positiveLinks = network.links.filter(l => l.weight > 0);
      const negativeLinks = network.links.filter(l => l.weight < 0);

      expect(positiveLinks.length).toBeGreaterThan(0);
      expect(negativeLinks.length).toBeGreaterThan(0);
    });

    test('sollte Connection-Count pro Node berechnen', () => {
      const { NeuronNetwork } = require('./neuron_dashboard.js');
      const network = new NeuronNetwork({ demoMode: false });

      network.nodes.forEach(node => {
        expect(node).toHaveProperty('connections');
        expect(typeof node.connections).toBe('number');
      });
    });
  });

  describe('Canvas-Setup', () => {
    test('sollte Canvas-Größe korrekt setzen', () => {
      const { NeuronNetwork } = require('./neuron_dashboard.js');
      const network = new NeuronNetwork({ demoMode: false });

      expect(network.width).toBeGreaterThan(0);
      expect(network.height).toBeGreaterThan(0);
    });

    test('sollte DPI-Support haben', () => {
      const { NeuronNetwork } = require('./neuron_dashboard.js');
      const network = new NeuronNetwork({ demoMode: false });

      expect(network.dpr).toBeGreaterThanOrEqual(1);
    });
  });

  describe('Statistiken', () => {
    test('sollte Stats-Objekt initialisieren', () => {
      const { NeuronNetwork } = require('./neuron_dashboard.js');
      const network = new NeuronNetwork({ demoMode: false });

      expect(network.stats).toBeDefined();
      expect(network.stats.total).toBe(14);
      expect(network.stats.active).toBeDefined();
      expect(network.stats.firing).toBeDefined();
    });

    test('sollte Stats nach Update berechnen', () => {
      const { NeuronNetwork } = require('./neuron_dashboard.js');
      const network = new NeuronNetwork({ demoMode: false });

      network.nodes[0].state = NEURON_STATES.FIRING;
      network._updateStats();

      expect(network.stats.firing).toBeGreaterThanOrEqual(1);
    });
  });

  describe('Methoden', () => {
    let network;

    beforeEach(() => {
      const { NeuronNetwork } = require('./neuron_dashboard.js');
      network = new NeuronNetwork({ demoMode: false });
    });

    test('sollte resetLayout() ausführen', () => {
      expect(() => network.resetLayout()).not.toThrow();
    });

    test('sollte setDemoMode() ausführen', () => {
      network.setDemoMode(true);
      expect(network.demoMode).toBe(true);

      network.setDemoMode(false);
      expect(network.demoMode).toBe(false);
    });

    test('sollte fireRandom() ausführen', () => {
      expect(() => network.fireRandom()).not.toThrow();
    });

    test('sollte destroy() ausführen', () => {
      expect(() => network.destroy()).not.toThrow();
    });

    test('sollte Mausposition berechnen', () => {
      const mockEvent = {
        clientX: 100,
        clientY: 200
      };

      canvas.getBoundingClientRect = jest.fn(() => ({
        left: 10,
        top: 20,
        width: 800,
        height: 600
      }));

      const pos = network._getMousePosition(mockEvent);

      expect(pos.x).toBe(90);
      expect(pos.y).toBe(180);
    });

    test('sollte Node an Position finden', () => {
      const mouse = { x: network.nodes[0].x, y: network.nodes[0].y };
      const node = network._findNodeAtPosition(mouse);

      expect(node).toBeDefined();
    });

    test('sollte Tooltip aktualisieren', () => {
      const mouse = { x: 100, y: 100 };
      network._updateTooltip(network.nodes[0], mouse);

      expect(tooltip.classList.contains('visible')).toBe(true);
    });

    test('sollte Tooltip ausblenden', () => {
      network._hideTooltip();
      expect(tooltip.classList.contains('visible')).toBe(false);
    });
  });

  describe('WebSocket', () => {
    test('sollte WebSocket ohne URL nicht initialisieren', () => {
      const { NeuronNetwork } = require('./neuron_dashboard.js');
      const network = new NeuronNetwork({ demoMode: false, wsUrl: null });

      expect(network.ws).toBeNull();
    });

    test('sollte WebSocket-Nachrichten verarbeiten', () => {
      const { NeuronNetwork } = require('./neuron_dashboard.js');
      const network = new NeuronNetwork({ demoMode: false });

      const mockData = {
        type: 'neuron_state',
        neuronId: 'N1',
        state: NEURON_STATES.FIRING
      };

      expect(() => network._handleWebSocketMessage(mockData)).not.toThrow();
    });
  });

  describe('Interaktionen', () => {
    let network;

    beforeEach(() => {
      const { NeuronNetwork } = require('./neuron_dashboard.js');
      network = new NeuronNetwork({ demoMode: false });
    });

    test('sollte MouseMove-Event verarbeiten', () => {
      const mockEvent = {
        clientX: 100,
        clientY: 100
      };

      canvas.getBoundingClientRect = jest.fn(() => ({
        left: 0,
        top: 0,
        width: 800,
        height: 600
      }));

      expect(() => network._handleMouseMove(mockEvent)).not.toThrow();
    });

    test('sollte MouseLeave-Event verarbeiten', () => {
      expect(() => network._handleMouseLeave()).not.toThrow();
    });

    test('sollte Click-Event verarbeiten', () => {
      const mockEvent = {
        clientX: network.nodes[0].x,
        clientY: network.nodes[0].y
      };

      canvas.getBoundingClientRect = jest.fn(() => ({
        left: 0,
        top: 0,
        width: 800,
        height: 600
      }));

      expect(() => network._handleClick(mockEvent)).not.toThrow();
    });
  });

  describe('Resize-Handler', () => {
    test('sollte Resize-Event verarbeiten', () => {
      const { NeuronNetwork } = require('./neuron_dashboard.js');
      const network = new NeuronNetwork({ demoMode: false });

      global.window.innerWidth = 1200;
      global.window.innerHeight = 800;

      expect(() => network._handleResize()).not.toThrow();
    });
  });
});

describe('Konstanten', () => {
  test('sollte alle NEURON_STATES exportieren', () => {
    expect(Object.keys(NEURON_STATES).length).toBe(3);
  });

  test('sollte alle NEURON_COLORS exportieren', () => {
    expect(Object.keys(NEURON_COLORS).length).toBe(3);
  });

  test('sollte alle LAYER_COLORS exportieren', () => {
    expect(Object.keys(LAYER_COLORS).length).toBe(3);
  });
});
