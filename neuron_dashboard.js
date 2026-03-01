/**
 * Neuron Dashboard - D3.js Force-Directed Graph Visualization
 * PilotSuite Neural Network Frontend
 * 
 * @version 1.0.0
 * @author PilotSuite Team
 * @description Canvas-based neural network visualization with real-time updates
 */

'use strict';

/**
 * Neuron-Zustände Konstanten
 */
const NEURON_STATES = {
  INACTIVE: 'inactive',
  ACTIVE: 'active',
  FIRING: 'firing'
};

/**
 * Farb-Konfiguration für Neuronen-Zustände
 */
const NEURON_COLORS = {
  inactive: '#666666',
  active: '#4CAF50',
  firing: '#FF5722'
};

/**
 * Layer-Farben für Neuronen-Typen
 */
const LAYER_COLORS = {
  input: '#2196F3',    // Blau
  hidden: '#9C27B0',   // Lila
  output: '#FF9800'    // Orange
};

/**
 * NeuronNetwork Klasse - Hauptkomponente für die Visualisierung
 */
class NeuronNetwork {
  /**
   * Initialisiert das Neuronennetzwerk
   * @param {Object} options - Konfigurationsoptionen
   * @param {string} options.canvasId - Canvas Element ID
   * @param {string} options.tooltipId - Tooltip Element ID
   * @param {boolean} options.demoMode - Demo-Modus aktivieren
   * @param {string} options.wsUrl - WebSocket URL (optional)
   */
  constructor(options = {}) {
    this.canvasId = options.canvasId || 'neuronCanvas';
    this.tooltipId = options.tooltipId || 'tooltip';
    this.demoMode = options.demoMode !== false;
    this.wsUrl = options.wsUrl || null;

    // Canvas Setup
    this.canvas = document.getElementById(this.canvasId);
    if (!this.canvas) {
      console.error('[NeuronNetwork] Canvas element not found!');
      return;
    }

    this.ctx = this.canvas.getContext('2d');
    if (!this.ctx) {
      console.error('[NeuronNetwork] Canvas 2D context not supported!');
      return;
    }

    // Netzwerk-Daten
    this.nodes = [];
    this.links = [];

    // Simulation
    this.simulation = null;
    this.width = 0;
    this.height = 0;
    this.dpr = window.devicePixelRatio || 1;

    // Interaktion
    this.hoveredNode = null;
    this.draggedNode = null;
    this.drag = null;

    // Animation
    this.animationFrame = null;
    this.pulsePhase = 0;

    // WebSocket
    this.ws = null;
    this.wsReconnectTimer = null;

    // Stats
    this.stats = {
      total: 0,
      active: 0,
      firing: 0
    };

    // Initialisierung
    this._setupCanvasSize();
    this._createNodes();
    this._createLinks();
    this._setupSimulation();
    this._setupInteractions();
    this._setupWebSocket();
    this._startRenderLoop();

    // Event Listeners
    window.addEventListener('resize', () => this._handleResize());

    console.log('[NeuronNetwork] Initialisiert mit', this.nodes.length, 'Neuronen und', this.links.length, 'Verbindungen');
  }

  /**
   * Erstellt 14 Neuronen (3 Input, 8 Hidden, 3 Output)
   * @private
   */
  _createNodes() {
    const width = this.width;
    const height = this.height;

    // Input Layer (3 Neuronen) - Links
    for (let i = 0; i < 3; i++) {
      this.nodes.push({
        id: `N${i + 1}`,
        type: 'input',
        layer: 0,
        state: NEURON_STATES.ACTIVE,
        x: width * 0.15,
        y: height * (0.2 + i * 0.3),
        vx: 0,
        vy: 0,
        connections: 0
      });
    }

    // Hidden Layer (8 Neuronen) - Mitte
    for (let i = 0; i < 8; i++) {
      const row = i % 4;
      const col = Math.floor(i / 4);
      this.nodes.push({
        id: `N${i + 4}`,
        type: 'hidden',
        layer: 1,
        state: NEURON_STATES.INACTIVE,
        x: width * (0.45 + col * 0.1),
        y: height * (0.15 + row * 0.25),
        vx: 0,
        vy: 0,
        connections: 0
      });
    }

    // Output Layer (3 Neuronen) - Rechts
    for (let i = 0; i < 3; i++) {
      this.nodes.push({
        id: `N${i + 12}`,
        type: 'output',
        layer: 2,
        state: NEURON_STATES.INACTIVE,
        x: width * 0.85,
        y: height * (0.2 + i * 0.3),
        vx: 0,
        vy: 0,
        connections: 0
      });
    }

    this.stats.total = this.nodes.length;
    this._updateStats();
  }

  /**
   * Erstellt 24 gewichtete Verbindungen
   * @private
   */
  _createLinks() {
    const connections = [
      // Input → Hidden (12 Verbindungen)
      { source: 'N1', target: 'N4', weight: 0.8 },
      { source: 'N1', target: 'N5', weight: 0.5 },
      { source: 'N1', target: 'N6', weight: -0.3 },
      { source: 'N2', target: 'N5', weight: 0.7 },
      { source: 'N2', target: 'N6', weight: 0.4 },
      { source: 'N2', target: 'N7', weight: -0.2 },
      { source: 'N3', target: 'N6', weight: 0.6 },
      { source: 'N3', target: 'N7', weight: 0.9 },
      { source: 'N3', target: 'N8', weight: -0.4 },
      { source: 'N1', target: 'N8', weight: 0.3 },
      { source: 'N2', target: 'N4', weight: 0.5 },
      { source: 'N3', target: 'N5', weight: 0.4 },

      // Hidden → Hidden (6 Verbindungen)
      { source: 'N4', target: 'N9', weight: 0.6 },
      { source: 'N5', target: 'N9', weight: 0.7 },
      { source: 'N6', target: 'N10', weight: -0.5 },
      { source: 'N7', target: 'N10', weight: 0.8 },
      { source: 'N8', target: 'N11', weight: 0.4 },
      { source: 'N9', target: 'N11', weight: 0.5 },

      // Hidden → Output (6 Verbindungen)
      { source: 'N9', target: 'N12', weight: 0.9 },
      { source: 'N10', target: 'N12', weight: 0.6 },
      { source: 'N9', target: 'N13', weight: 0.4 },
      { source: 'N10', target: 'N13', weight: -0.3 },
      { source: 'N11', target: 'N13', weight: 0.7 },
      { source: 'N11', target: 'N14', weight: 0.5 }
    ];

    this.links = connections.map(conn => ({
      source: conn.source,
      target: conn.target,
      weight: conn.weight,
      active: false
    }));

    // Connection-Count pro Node berechnen
    this.nodes.forEach(node => {
      node.connections = this.links.filter(
        l => l.source === node.id || l.target === node.id
      ).length;
    });
  }

  /**
   * Setup Canvas-Größe mit DPI-Support
   * @private
   */
  _setupCanvasSize() {
    const container = this.canvas.parentElement;
    const rect = container.getBoundingClientRect();

    this.width = rect.width;
    this.height = rect.height;

    this.canvas.width = this.width * this.dpr;
    this.canvas.height = this.height * this.dpr;
    this.canvas.style.width = `${this.width}px`;
    this.canvas.style.height = `${this.height}px`;

    this.ctx.scale(this.dpr, this.dpr);

    console.log('[NeuronNetwork] Canvas-Größe:', this.width, 'x', this.height, 'px');
  }

  /**
   * Setup D3 Force-Directed Simulation
   * @private
   */
  _setupSimulation() {
    this.simulation = d3.forceSimulation(this.nodes)
      .force('link', d3.forceLink(this.links)
        .id(d => d.id)
        .distance(100))
      .force('charge', d3.forceManyBody().strength(-400))
      .force('center', d3.forceCenter(this.width / 2, this.height / 2))
      .force('collide', d3.forceCollide().radius(20))
      .force('x', d3.forceX(d => {
        // Layer-basierte X-Positionen für bessere Struktur
        const layerPositions = [this.width * 0.15, this.width * 0.5, this.width * 0.85];
        return layerPositions[d.layer] || this.width / 2;
      }).strength(0.1))
      .velocityDecay(0.4)
      .alphaMin(0.01);

    this.simulation.on('tick', () => {
      // Positionen werden im Render-Loop verwendet
    });

    this.simulation.on('end', () => {
      console.log('[NeuronNetwork] Simulation stabilisiert');
    });
  }

  /**
   * Setup Interaktionen (Drag, Hover)
   * @private
   */
  _setupInteractions() {
    // D3 Drag Behavior
    this.drag = d3.drag()
      .on('start', (event) => this._handleDragStart(event))
      .on('drag', (event) => this._handleDrag(event))
      .on('end', (event) => this._handleDragEnd(event));

    // Canvas Event Listeners
    this.canvas.addEventListener('mousemove', (e) => this._handleMouseMove(e));
    this.canvas.addEventListener('mouseleave', () => this._handleMouseLeave());
    this.canvas.addEventListener('click', (e) => this._handleClick(e));

    // Drag auf Canvas anwenden
    this.canvas.addEventListener('mousedown', (e) => {
      const mouse = this._getMousePosition(e);
      const node = this._findNodeAtPosition(mouse);
      if (node) {
        this.drag(new Event('drag'), node);
      }
    });
  }

  /**
   * Setup WebSocket für Live-Updates
   * @private
   */
  _setupWebSocket() {
    if (!this.wsUrl) {
      console.log('[NeuronNetwork] WebSocket deaktiviert (keine URL)');
      return;
    }

    this._connectWebSocket();
  }

  /**
   * Verbindet mit WebSocket Server
   * @private
   */
  _connectWebSocket() {
    try {
      this.ws = new WebSocket(this.wsUrl);

      this.ws.onopen = () => {
        console.log('[NeuronNetwork] WebSocket verbunden');
        this.ws.send(JSON.stringify({ type: 'subscribe', channel: 'neurons' }));
      };

      this.ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        this._handleWebSocketMessage(data);
      };

      this.ws.onclose = () => {
        console.log('[NeuronNetwork] WebSocket geschlossen, reconnect in 5s...');
        this.wsReconnectTimer = setTimeout(() => this._connectWebSocket(), 5000);
      };

      this.ws.onerror = (error) => {
        console.error('[NeuronNetwork] WebSocket Fehler:', error);
      };
    } catch (error) {
      console.error('[NeuronNetwork] WebSocket Connect Fehler:', error);
    }
  }

  /**
   * Verarbeitet WebSocket Nachrichten
   * @param {Object} data - Nachrichtendaten
   * @private
   */
  _handleWebSocketMessage(data) {
    switch (data.type) {
      case 'neuron_state':
        this._updateNeuronState(data.neuronId, data.state);
        break;
      case 'connection_activity':
        this._updateConnectionActivity(data.source, data.target, data.active);
        break;
      case 'network_snapshot':
        this._fullUpdate(data.nodes, data.links);
        break;
    }
  }

  /**
   * Aktualisiert Neuronen-Zustand
   * @param {string} neuronId - Neuron ID
   * @param {string} state - Neuer Zustand
   * @private
   */
  _updateNeuronState(neuronId, state) {
    const node = this.nodes.find(n => n.id === neuronId);
    if (node) {
      node.state = state;
      this._updateStats();
      console.log('[NeuronNetwork] Update:', neuronId, '→', state);
    }
  }

  /**
   * Aktualisiert Verbindungs-Aktivität
   * @param {string} source - Source Node ID
   * @param {string} target - Target Node ID
   * @param {boolean} active - Aktivitätsstatus
   * @private
   */
  _updateConnectionActivity(source, target, active) {
    const link = this.links.find(l => l.source === source && l.target === target);
    if (link) {
      link.active = active;
    }
  }

  /**
   * Vollständiges Netzwerk-Update
   * @param {Array} nodes - Neue Node-Daten
   * @param {Array} links - Neue Link-Daten
   * @private
   */
  _fullUpdate(nodes, links) {
    if (nodes) {
      nodes.forEach(n => {
        const node = this.nodes.find(node => node.id === n.id);
        if (node) {
          node.state = n.state;
        }
      });
    }
    if (links) {
      links.forEach(l => {
        const link = this.links.find(link => 
          link.source === l.source && link.target === l.target
        );
        if (link) {
          link.active = l.active;
        }
      });
    }
    this._updateStats();
  }

  /**
   * Startet den Render-Loop
   * @private
   */
  _startRenderLoop() {
    const render = () => {
      this._render();
      this.animationFrame = requestAnimationFrame(render);
    };
    render();
  }

  /**
   * Haupt-Render-Funktion
   * @private
   */
  _render() {
    // Canvas leeren
    this.ctx.clearRect(0, 0, this.width, this.height);

    // Puls-Phase für Animation
    this.pulsePhase += 0.05;

    // Verbindungen zeichnen
    this._drawLinks();

    // Neuronen zeichnen
    this._drawNodes();

    // Demo-Modus Updates
    if (this.demoMode) {
      this._simulateUpdates();
    }
  }

  /**
   * Zeichnet alle Verbindungen
   * @private
   */
  _drawLinks() {
    this.links.forEach(link => {
      const source = typeof link.source === 'object' ? link.source : 
                     this.nodes.find(n => n.id === link.source);
      const target = typeof link.target === 'object' ? link.target : 
                     this.nodes.find(n => n.id === link.target);

      if (!source || !target) return;

      this.ctx.beginPath();
      this.ctx.moveTo(source.x, source.y);
      this.ctx.lineTo(target.x, target.y);

      // Farbe basierend auf Gewicht
      if (link.weight > 0) {
        this.ctx.strokeStyle = `rgba(76, 175, 80, ${0.3 + Math.abs(link.weight) * 0.4})`;
      } else if (link.weight < 0) {
        this.ctx.strokeStyle = `rgba(255, 87, 34, ${0.3 + Math.abs(link.weight) * 0.4})`;
      } else {
        this.ctx.strokeStyle = 'rgba(150, 150, 150, 0.3)';
      }

      // Dicke basierend auf Gewicht
      this.ctx.lineWidth = 1 + Math.abs(link.weight) * 3;
      this.ctx.stroke();

      // Aktive Verbindung hervorheben
      if (link.active) {
        this.ctx.strokeStyle = 'rgba(255, 255, 255, 0.8)';
        this.ctx.lineWidth = 3;
        this.ctx.stroke();
      }
    });
  }

  /**
   * Zeichnet alle Neuronen
   * @private
   */
  _drawNodes() {
    this.nodes.forEach(node => {
      // Basis-Radius
      let radius = 12;

      // Puls-Effekt für feuernde Neuronen
      if (node.state === NEURON_STATES.FIRING) {
        radius += Math.sin(this.pulsePhase + node.x) * 4;
      }

      // Hover-Effekt
      if (this.hoveredNode === node) {
        radius += 3;
      }

      // Neuron zeichnen
      this.ctx.beginPath();
      this.ctx.arc(node.x, node.y, radius, 0, Math.PI * 2);

      // Füllfarbe basierend auf Zustand
      this.ctx.fillStyle = NEURON_COLORS[node.state];
      this.ctx.fill();

      // Randfarbe basierend auf Layer
      this.ctx.strokeStyle = LAYER_COLORS[node.type];
      this.ctx.lineWidth = 2;
      this.ctx.stroke();

      // Glow-Effekt für feuernde Neuronen
      if (node.state === NEURON_STATES.FIRING) {
        this.ctx.beginPath();
        this.ctx.arc(node.x, node.y, radius + 6, 0, Math.PI * 2);
        this.ctx.strokeStyle = `rgba(255, 87, 34, ${0.3 + Math.sin(this.pulsePhase) * 0.2})`;
        this.ctx.lineWidth = 2;
        this.ctx.stroke();
      }

      // Label für Node-ID
      this.ctx.fillStyle = '#ffffff';
      this.ctx.font = '10px sans-serif';
      this.ctx.textAlign = 'center';
      this.ctx.textBaseline = 'middle';
      this.ctx.fillText(node.id, node.x, node.y);
    });
  }

  /**
   * Simuliert zufällige Updates im Demo-Modus
   * @private
   */
  _simulateUpdates() {
    if (Math.random() < 0.02) { // ~2% Chance pro Frame
      const randomNode = this.nodes[Math.floor(Math.random() * this.nodes.length)];
      const states = Object.values(NEURON_STATES);
      randomNode.state = states[Math.floor(Math.random() * states.length)];
      this._updateStats();
    }
  }

  /**
   * Aktualisiert die Statistik-Anzeige
   * @private
   */
  _updateStats() {
    this.stats.active = this.nodes.filter(n => n.state === NEURON_STATES.ACTIVE).length;
    this.stats.firing = this.nodes.filter(n => n.state === NEURON_STATES.FIRING).length;

    const activeEl = document.getElementById('activeCount');
    const firingEl = document.getElementById('firingCount');

    if (activeEl) activeEl.textContent = this.stats.active;
    if (firingEl) firingEl.textContent = this.stats.firing;
  }

  /**
   * Mausposition relativ zum Canvas
   * @param {MouseEvent} e - Maus-Event
   * @returns {Object} Position {x, y}
   * @private
   */
  _getMousePosition(e) {
    const rect = this.canvas.getBoundingClientRect();
    return {
      x: e.clientX - rect.left,
      y: e.clientY - rect.top
    };
  }

  /**
   * Findet Node an Mausposition
   * @param {Object} mouse - Mausposition
   * @returns {Object|null} Gefundene Node oder null
   * @private
   */
  _findNodeAtPosition(mouse) {
    for (const node of this.nodes) {
      const dx = mouse.x - node.x;
      const dy = mouse.y - node.y;
      if (dx * dx + dy * dy < 400) { // 20px Radius
        return node;
      }
    }
    return null;
  }

  /**
   * Handler für Maus-Bewegung
   * @param {MouseEvent} e - Maus-Event
   * @private
   */
  _handleMouseMove(e) {
    const mouse = this._getMousePosition(e);
    const node = this._findNodeAtPosition(mouse);

    if (node !== this.hoveredNode) {
      this.hoveredNode = node;
      this._updateTooltip(node, mouse);
    }
  }

  /**
   * Handler für Maus-Verlassen
   * @private
   */
  _handleMouseLeave() {
    this.hoveredNode = null;
    this._hideTooltip();
  }

  /**
   * Handler für Klick
   * @param {MouseEvent} e - Maus-Event
   * @private
   */
  _handleClick(e) {
    const mouse = this._getMousePosition(e);
    const node = this._findNodeAtPosition(mouse);

    if (node) {
      // Toggle Node-Zustand bei Klick
      const states = Object.values(NEURON_STATES);
      const currentIndex = states.indexOf(node.state);
      node.state = states[(currentIndex + 1) % states.length];
      this._updateStats();
      console.log('[NeuronNetwork] Klick:', node.id, '→', node.state);
    }
  }

  /**
   * Handler für Drag-Start
   * @param {Object} event - D3 Drag Event
   * @private
   */
  _handleDragStart(event) {
    if (!event.subject) return;
    this.draggedNode = event.subject;
    this.simulation.alphaTarget(0.3).restart();
  }

  /**
   * Handler für Drag
   * @param {Object} event - D3 Drag Event
   * @private
   */
  _handleDrag(event) {
    if (!event.subject) return;
    event.subject.fx = event.x;
    event.subject.fy = event.y;
  }

  /**
   * Handler für Drag-Ende
   * @param {Object} event - D3 Drag Event
   * @private
   */
  _handleDragEnd(event) {
    if (!event.subject) return;
    this.draggedNode = null;
    this.simulation.alphaTarget(0);
    event.subject.fx = null;
    event.subject.fy = null;
  }

  /**
   * Tooltip aktualisieren
   * @param {Object} node - Node-Daten
   * @param {Object} mouse - Mausposition
   * @private
   */
  _updateTooltip(node, mouse) {
    const tooltip = document.getElementById(this.tooltipId);
    if (!tooltip) return;

    if (node) {
      tooltip.innerHTML = `
        <div class="tooltip-title">${node.id}</div>
        <div class="tooltip-row">
          <span>Typ:</span>
          <span class="value">${node.type}</span>
        </div>
        <div class="tooltip-row">
          <span>Zustand:</span>
          <span class="value">${node.state}</span>
        </div>
        <div class="tooltip-row">
          <span>Layer:</span>
          <span class="value">${node.layer + 1}</span>
        </div>
        <div class="tooltip-row">
          <span>Verbindungen:</span>
          <span class="value">${node.connections}</span>
        </div>
      `;

      tooltip.style.left = `${mouse.x + 15}px`;
      tooltip.style.top = `${mouse.y + 15}px`;
      tooltip.classList.add('visible');
    } else {
      this._hideTooltip();
    }
  }

  /**
   * Tooltip ausblenden
   * @private
   */
  _hideTooltip() {
    const tooltip = document.getElementById(this.tooltipId);
    if (tooltip) {
      tooltip.classList.remove('visible');
    }
  }

  /**
   * Handler für Window-Resize
   * @private
   */
  _handleResize() {
    this._setupCanvasSize();
    this.simulation.force('center', d3.forceCenter(this.width / 2, this.height / 2));
    this.simulation.alpha(0.3).restart();
    console.log('[NeuronNetwork] Resize:', this.width, 'x', this.height);
  }

  /**
   * Setzt Layout auf Startposition zurück
   */
  resetLayout() {
    this._createNodes();
    this.simulation.nodes(this.nodes);
    this.simulation.alpha(1).restart();
    console.log('[NeuronNetwork] Layout zurückgesetzt');
  }

  /**
   * Toggle Demo-Modus
   * @param {boolean} enabled - Demo-Modus aktivieren/deaktivieren
   */
  setDemoMode(enabled) {
    this.demoMode = enabled;
    console.log('[NeuronNetwork] Demo-Modus:', enabled ? 'AN' : 'AUS');
  }

  /**
   * Zufälliges Neuron feuern lassen
   */
  fireRandom() {
    const inactiveNodes = this.nodes.filter(n => n.state !== NEURON_STATES.FIRING);
    if (inactiveNodes.length > 0) {
      const randomNode = inactiveNodes[Math.floor(Math.random() * inactiveNodes.length)];
      randomNode.state = NEURON_STATES.FIRING;
      this._updateStats();
      console.log('[NeuronNetwork] Fire:', randomNode.id);
    }
  }

  /**
   * Stoppt die Animation und räumt auf
   */
  destroy() {
    if (this.animationFrame) {
      cancelAnimationFrame(this.animationFrame);
    }
    if (this.ws) {
      this.ws.close();
    }
    if (this.wsReconnectTimer) {
      clearTimeout(this.wsReconnectTimer);
    }
    if (this.simulation) {
      this.simulation.stop();
    }
    console.log('[NeuronNetwork] Zerstört');
  }
}

/**
 * Initialisierung beim DOM-Ready
 */
document.addEventListener('DOMContentLoaded', () => {
  console.log('[NeuronDashboard] Initialisierung gestartet...');

  // NeuronNetwork Instanz erstellen
  const network = new NeuronNetwork({
    canvasId: 'neuronCanvas',
    tooltipId: 'tooltip',
    demoMode: true,
    wsUrl: null // WebSocket später konfigurieren
  });

  // Button-Event-Listeners
  const toggleDemoBtn = document.getElementById('toggleDemoBtn');
  const resetLayoutBtn = document.getElementById('resetLayoutBtn');
  const fireRandomBtn = document.getElementById('fireRandomBtn');

  if (toggleDemoBtn) {
    toggleDemoBtn.addEventListener('click', () => {
      network.setDemoMode(!network.demoMode);
      toggleDemoBtn.textContent = network.demoMode ? 'Demo Pause' : 'Demo Start';
    });
  }

  if (resetLayoutBtn) {
    resetLayoutBtn.addEventListener('click', () => {
      network.resetLayout();
    });
  }

  if (fireRandomBtn) {
    fireRandomBtn.addEventListener('click', () => {
      network.fireRandom();
    });
  }

  // URL-Parameter für Konfiguration
  const urlParams = new URLSearchParams(window.location.search);
  if (urlParams.has('demo')) {
    network.setDemoMode(urlParams.get('demo') === '1');
  }
  if (urlParams.has('ws')) {
    network.wsUrl = urlParams.get('ws');
    network._connectWebSocket();
  }

  console.log('[NeuronDashboard] Initialisierung abgeschlossen');

  // Globale Referenz für Debugging
  window.neuronNetwork = network;
});
