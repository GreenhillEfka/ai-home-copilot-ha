/**
 * Neuron Dashboard Utility Tests
 * Hilfsfunktionen und Konstanten Tests
 * 
 * @version 1.0.0
 * @description Tests für Utility-Funktionen und Konstanten
 */

'use strict';

describe('Neuron Dashboard Utils', () => {
  describe('Konstanten', () => {
    test('NEURON_STATES sollte alle Zustände definieren', () => {
      const states = ['INACTIVE', 'ACTIVE', 'FIRING'];
      states.forEach(state => {
        expect(NEURON_STATES[state]).toBeDefined();
        expect(typeof NEURON_STATES[state]).toBe('string');
      });
    });

    test('NEURON_COLORS sollte gültige Hex-Codes haben', () => {
      const colors = Object.values(NEURON_COLORS);
      const hexRegex = /^#[0-9A-Fa-f]{6}$/;

      colors.forEach(color => {
        expect(hexRegex.test(color)).toBe(true);
      });
    });

    test('LAYER_COLORS sollte alle Layer abdecken', () => {
      const layers = ['input', 'hidden', 'output'];
      layers.forEach(layer => {
        expect(LAYER_COLORS[layer]).toBeDefined();
      });
    });
  });

  describe('Farb-Konvertierung', () => {
    test('sollte Hex zu RGB konvertieren', () => {
      const hexToRgb = (hex) => {
        const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
        return result ? {
          r: parseInt(result[1], 16),
          g: parseInt(result[2], 16),
          b: parseInt(result[3], 16)
        } : null;
      };

      const rgb = hexToRgb('#4CAF50');
      expect(rgb).toEqual({ r: 76, g: 175, b: 80 });
    });

    test('sollte RGB zu Hex konvertieren', () => {
      const rgbToHex = (r, g, b) => {
        return '#' + [r, g, b].map(x => {
          const hex = x.toString(16);
          return hex.length === 1 ? '0' + hex : hex;
        }).join('');
      };

      const hex = rgbToHex(76, 175, 80);
      expect(hex).toBe('#4caf50');
    });
  });

  describe('Distanz-Berechnung', () => {
    test('sollte euklidische Distanz berechnen', () => {
      const distance = (p1, p2) => {
        const dx = p2.x - p1.x;
        const dy = p2.y - p1.y;
        return Math.sqrt(dx * dx + dy * dy);
      };

      const p1 = { x: 0, y: 0 };
      const p2 = { x: 3, y: 4 };

      expect(distance(p1, p2)).toBe(5);
    });

    test('sollte Distanz 0 bei gleichen Punkten', () => {
      const distance = (p1, p2) => {
        const dx = p2.x - p1.x;
        const dy = p2.y - p1.y;
        return Math.sqrt(dx * dx + dy * dy);
      };

      const p1 = { x: 5, y: 5 };
      const p2 = { x: 5, y: 5 };

      expect(distance(p1, p2)).toBe(0);
    });
  });

  describe('Collision Detection', () => {
    test('sollte Kollision erkennen', () => {
      const isColliding = (p1, p2, radius) => {
        const dx = p2.x - p1.x;
        const dy = p2.y - p1.y;
        const distance = Math.sqrt(dx * dx + dy * dy);
        return distance < radius * 2;
      };

      const p1 = { x: 0, y: 0 };
      const p2 = { x: 10, y: 0 };

      expect(isColliding(p1, p2, 10)).toBe(true);
      expect(isColliding(p1, p2, 3)).toBe(false);
    });
  });

  describe('State Transitions', () => {
    test('sollte State-Zyklus durchlaufen', () => {
      const states = Object.values(NEURON_STATES);
      const nextState = (current) => {
        const index = states.indexOf(current);
        return states[(index + 1) % states.length];
      };

      expect(nextState(NEURON_STATES.INACTIVE)).toBe(NEURON_STATES.ACTIVE);
      expect(nextState(NEURON_STATES.ACTIVE)).toBe(NEURON_STATES.FIRING);
      expect(nextState(NEURON_STATES.FIRING)).toBe(NEURON_STATES.INACTIVE);
    });
  });

  describe('Weight Normalization', () => {
    test('sollte Gewichte normalisieren', () => {
      const normalizeWeight = (weight, min = -1, max = 1) => {
        return Math.max(min, Math.min(max, weight));
      };

      expect(normalizeWeight(1.5)).toBe(1);
      expect(normalizeWeight(-1.5)).toBe(-1);
      expect(normalizeWeight(0.5)).toBe(0.5);
    });
  });

  describe('Alpha Blending', () => {
    test('sollte Alpha-Wert berechnen', () => {
      const calculateAlpha = (weight, base = 0.3, scale = 0.4) => {
        return base + Math.abs(weight) * scale;
      };

      expect(calculateAlpha(0)).toBe(0.3);
      expect(calculateAlpha(1)).toBe(0.7);
      expect(calculateAlpha(-0.5)).toBeCloseTo(0.5, 1);
    });
  });

  describe('Pulse Animation', () => {
    test('sollte Puls-Radius berechnen', () => {
      const calculatePulseRadius = (baseRadius, phase, amplitude = 4) => {
        return baseRadius + Math.sin(phase) * amplitude;
      };

      const base = 12;
      expect(calculatePulseRadius(base, 0)).toBe(base);
      expect(calculatePulseRadius(base, Math.PI / 2)).toBeGreaterThan(base);
      expect(calculatePulseRadius(base, Math.PI * 1.5)).toBeLessThan(base);
    });
  });

  describe('Tooltip Position', () => {
    test('sollte Tooltip-Position berechnen', () => {
      const calculateTooltipPos = (mouseX, mouseY, offsetX = 15, offsetY = 15) => {
        return {
          x: mouseX + offsetX,
          y: mouseY + offsetY
        };
      };

      const pos = calculateTooltipPos(100, 200);
      expect(pos.x).toBe(115);
      expect(pos.y).toBe(215);
    });
  });

  describe('Layer Positioning', () => {
    test('sollte Layer-X-Position berechnen', () => {
      const getLayerX = (layer, width, positions = [0.15, 0.5, 0.85]) => {
        return width * (positions[layer] || 0.5);
      };

      const width = 1000;
      expect(getLayerX(0, width)).toBe(150);
      expect(getLayerX(1, width)).toBe(500);
      expect(getLayerX(2, width)).toBe(850);
    });
  });

  describe('Connection Counting', () => {
    test('sollte Verbindungen pro Node zählen', () => {
      const countConnections = (nodeId, links) => {
        return links.filter(l => l.source === nodeId || l.target === nodeId).length;
      };

      const links = [
        { source: 'N1', target: 'N2' },
        { source: 'N1', target: 'N3' },
        { source: 'N2', target: 'N3' }
      ];

      expect(countConnections('N1', links)).toBe(2);
      expect(countConnections('N2', links)).toBe(2);
      expect(countConnections('N3', links)).toBe(2);
    });
  });

  describe('Node Filtering', () => {
    test('sollte Nodes nach Typ filtern', () => {
      const filterByType = (nodes, type) => {
        return nodes.filter(n => n.type === type);
      };

      const nodes = [
        { id: 'N1', type: 'input' },
        { id: 'N2', type: 'hidden' },
        { id: 'N3', type: 'input' }
      ];

      const inputs = filterByType(nodes, 'input');
      expect(inputs.length).toBe(2);
    });

    test('sollte Nodes nach State filtern', () => {
      const filterByState = (nodes, state) => {
        return nodes.filter(n => n.state === state);
      };

      const nodes = [
        { id: 'N1', state: 'active' },
        { id: 'N2', state: 'firing' },
        { id: 'N3', state: 'active' }
      ];

      const active = filterByState(nodes, 'active');
      expect(active.length).toBe(2);
    });
  });

  describe('Random Selection', () => {
    test('sollte zufälligen Node auswählen', () => {
      const selectRandom = (array) => {
        return array[Math.floor(Math.random() * array.length)];
      };

      const nodes = [
        { id: 'N1' },
        { id: 'N2' },
        { id: 'N3' }
      ];

      const selected = selectRandom(nodes);
      expect(nodes).toContain(selected);
    });
  });

  describe('Throttling', () => {
    test('sollte Funktion throttlen', (done) => {
      let callCount = 0;
      
      const throttle = (func, limit) => {
        let inThrottle;
        return function(...args) {
          if (!inThrottle) {
            func.apply(this, args);
            callCount++;
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
          }
        };
      };

      const throttledFn = throttle(() => {}, 100);
      
      throttledFn();
      throttledFn();
      throttledFn();

      setTimeout(() => {
        expect(callCount).toBe(1);
        done();
      }, 150);
    });
  });

  describe('Debouncing', () => {
    test('sollte Funktion debouncen', (done) => {
      let callCount = 0;
      
      const debounce = (func, delay) => {
        let timeoutId;
        return function(...args) {
          clearTimeout(timeoutId);
          timeoutId = setTimeout(() => {
            func.apply(this, args);
            callCount++;
          }, delay);
        };
      };

      const debouncedFn = debounce(() => {}, 50);
      
      debouncedFn();
      debouncedFn();
      debouncedFn();

      setTimeout(() => {
        expect(callCount).toBe(1);
        done();
      }, 100);
    });
  });

  describe('Array Utilities', () => {
    test('sollte Array shuffeln', () => {
      const shuffle = (array) => {
        const shuffled = [...array];
        for (let i = shuffled.length - 1; i > 0; i--) {
          const j = Math.floor(Math.random() * (i + 1));
          [shuffled[i], shuffled[j]] = [shuffled[j], shuffled[i]];
        }
        return shuffled;
      };

      const original = [1, 2, 3, 4, 5];
      const shuffled = shuffle(original);

      expect(shuffled.length).toBe(original.length);
      expect(shuffled.sort()).toEqual(original);
    });

    test('sollte Array chunken', () => {
      const chunk = (array, size) => {
        const chunks = [];
        for (let i = 0; i < array.length; i += size) {
          chunks.push(array.slice(i, i + size));
        }
        return chunks;
      };

      const chunked = chunk([1, 2, 3, 4, 5], 2);
      expect(chunked.length).toBe(3);
      expect(chunked[0]).toEqual([1, 2]);
      expect(chunked[2]).toEqual([5]);
    });
  });

  describe('Object Utilities', () => {
    test('sollte Object deep clone', () => {
      const deepClone = (obj) => {
        return JSON.parse(JSON.stringify(obj));
      };

      const original = { a: 1, b: { c: 2 } };
      const cloned = deepClone(original);

      cloned.b.c = 3;
      expect(original.b.c).toBe(2);
      expect(cloned.b.c).toBe(3);
    });

    test('sollte Object merge', () => {
      const merge = (...objects) => {
        return Object.assign({}, ...objects);
      };

      const merged = merge({ a: 1 }, { b: 2 }, { c: 3 });
      expect(merged).toEqual({ a: 1, b: 2, c: 3 });
    });
  });
});
