/**
 * Neuron Dashboard v2.0.0 - Living, Pulsing Neural Network
 * PilotSuite Neural Network Frontend
 *
 * @version 2.0.0
 * @description Canvas-based neural network with multi-colored pulsing neurons,
 *   synaptic flow animations, cross-dependency highlighting, and real-time updates.
 */

'use strict';

const NEURON_STATES = {
  INACTIVE: 'inactive',
  ACTIVE: 'active',
  FIRING: 'firing',
  INHIBITED: 'inhibited'
};

/** Multi-colored neuron state palette */
const NEURON_COLORS = {
  inactive: '#444c55',
  active: '#4CAF50',
  firing: '#FF5722',
  inhibited: '#7B1FA2'
};

/** Layer colors for neural layers */
const LAYER_COLORS = {
  input: '#2196F3',
  hidden: '#9C27B0',
  output: '#FF9800',
  context: '#00BCD4',
  state: '#E91E63',
  mood: '#FF9800'
};

/** Domain-specific neuron colors for HA entity mapping */
const DOMAIN_NEURON_COLORS = {
  light: '#f9d71c',
  switch: '#4caf50',
  sensor: '#2196f3',
  climate: '#ff9800',
  media_player: '#e91e63',
  person: '#00bcd4',
  automation: '#ff5722',
  presence: '#00e676',
  energy: '#ffd600',
  default: '#78909c'
};

/**
 * NeuronNetwork Klasse v2.0 - Living Pulsing Neural Network
 */
class NeuronNetwork {
  constructor(options = {}) {
    this.canvasId = options.canvasId || 'neuronCanvas';
    this.tooltipId = options.tooltipId || 'tooltip';
    this.demoMode = options.demoMode !== false;
    this.wsUrl = options.wsUrl || null;

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

    this.nodes = [];
    this.links = [];
    this.crossDependencies = [];

    this.simulation = null;
    this.width = 0;
    this.height = 0;
    this.dpr = window.devicePixelRatio || 1;

    this.hoveredNode = null;
    this.draggedNode = null;

    this.animationFrame = null;
    this.pulsePhase = 0;
    this.breathePhase = 0;
    this.synapticPhase = 0;

    this.ws = null;
    this.wsReconnectTimer = null;

    // Particle system for synaptic flow
    this.particles = [];
    this.maxParticles = 60;

    this.stats = {
      total: 0,
      active: 0,
      firing: 0,
      inhibited: 0,
      crossDeps: 0
    };

    this._setupCanvasSize();
    this._createNodes();
    this._createLinks();
    this._identifyCrossDependencies();
    this._setupSimulation();
    this._setupInteractions();
    this._setupWebSocket();
    this._startRenderLoop();

    window.addEventListener('resize', () => this._handleResize());

    console.log('[NeuronNetwork] v2.0 initialisiert mit', this.nodes.length, 'Neuronen,', this.links.length, 'Verbindungen,', this.crossDependencies.length, 'Cross-Dependencies');
  }

  /**
   * Creates 25 neurons across 5 layers:
   * Input(4) -> Context(5) -> State(6) -> Hidden(6) -> Output(4)
   */
  _createNodes() {
    const w = this.width;
    const h = this.height;

    const layers = [
      { name: 'input', count: 4, x: 0.08, labels: ['Presence', 'Light-Lux', 'Time', 'Weather'] },
      { name: 'context', count: 5, x: 0.28, labels: ['Zone-Context', 'Calendar', 'Energy', 'Media-State', 'Person-State'] },
      { name: 'state', count: 6, x: 0.48, labels: ['Automation', 'Mood-Input', 'Anomaly', 'Prediction', 'Pattern', 'Habitus'] },
      { name: 'hidden', count: 6, x: 0.68, labels: ['Brain-Fuse', 'Cross-Link', 'Optimizer', 'Scheduler', 'Repair', 'Suggest'] },
      { name: 'output', count: 4, x: 0.88, labels: ['Light-Ctrl', 'Music-Ctrl', 'Climate-Ctrl', 'Alert'] }
    ];

    let nodeIndex = 0;
    layers.forEach((layer, li) => {
      for (let i = 0; i < layer.count; i++) {
        const ySpread = 0.8 / Math.max(1, layer.count - 1);
        const yPos = layer.count === 1 ? 0.5 : 0.1 + i * ySpread;

        this.nodes.push({
          id: `N${nodeIndex + 1}`,
          type: layer.name,
          layer: li,
          layerName: layer.name,
          label: layer.labels[i] || `${layer.name}_${i}`,
          state: i === 0 ? NEURON_STATES.ACTIVE : NEURON_STATES.INACTIVE,
          domain: this._labelToDomain(layer.labels[i] || ''),
          x: w * layer.x,
          y: h * yPos,
          vx: 0,
          vy: 0,
          connections: 0,
          pulseOffset: Math.random() * Math.PI * 2,
          firingIntensity: 0,
          lastFired: 0
        });
        nodeIndex++;
      }
    });

    this.stats.total = this.nodes.length;
    this._updateStats();
  }

  _labelToDomain(label) {
    const l = label.toLowerCase();
    if (l.includes('light') || l.includes('lux')) return 'light';
    if (l.includes('media') || l.includes('music')) return 'media_player';
    if (l.includes('climate') || l.includes('weather')) return 'climate';
    if (l.includes('presence') || l.includes('person')) return 'presence';
    if (l.includes('energy')) return 'energy';
    if (l.includes('automation') || l.includes('suggest')) return 'automation';
    if (l.includes('sensor') || l.includes('anomaly')) return 'sensor';
    return 'default';
  }

  _getDomainColor(domain) {
    return DOMAIN_NEURON_COLORS[domain] || DOMAIN_NEURON_COLORS.default;
  }

  /**
   * Creates weighted connections with cross-layer dependencies
   */
  _createLinks() {
    const connections = [];

    // Input -> Context (forward)
    [[0,4],[0,5],[1,4],[1,6],[2,5],[2,7],[3,6],[3,7],[3,8]].forEach(([s,t]) => {
      connections.push({ source: `N${s+1}`, target: `N${t+1}`, weight: 0.5 + Math.random() * 0.5 });
    });

    // Context -> State
    [[4,9],[4,10],[5,10],[5,11],[6,12],[6,13],[7,11],[7,13],[8,9],[8,14]].forEach(([s,t]) => {
      connections.push({ source: `N${s+1}`, target: `N${t+1}`, weight: 0.4 + Math.random() * 0.6 });
    });

    // State -> Hidden
    [[9,15],[9,16],[10,16],[10,17],[11,17],[11,18],[12,18],[12,19],[13,15],[13,20],[14,19],[14,20]].forEach(([s,t]) => {
      connections.push({ source: `N${s+1}`, target: `N${t+1}`, weight: 0.3 + Math.random() * 0.7 });
    });

    // Hidden -> Output
    [[15,21],[16,21],[16,22],[17,22],[17,23],[18,23],[19,24],[20,24],[15,24],[20,21]].forEach(([s,t]) => {
      connections.push({ source: `N${s+1}`, target: `N${t+1}`, weight: 0.5 + Math.random() * 0.5 });
    });

    // Cross-layer skip connections (neural cross-dependencies)
    [[0,10],[1,15],[2,17],[3,22],[6,21],[8,24],[4,18]].forEach(([s,t]) => {
      connections.push({ source: `N${s+1}`, target: `N${t+1}`, weight: 0.3 + Math.random() * 0.3, isCross: true });
    });

    // Inhibitory connections (negative weights)
    [[10,9],[17,16],[14,12]].forEach(([s,t]) => {
      connections.push({ source: `N${s+1}`, target: `N${t+1}`, weight: -(0.2 + Math.random() * 0.4), inhibitory: true });
    });

    this.links = connections.map(conn => ({
      source: conn.source,
      target: conn.target,
      weight: conn.weight,
      isCross: conn.isCross || false,
      inhibitory: conn.inhibitory || false,
      active: false,
      flowPhase: Math.random() * Math.PI * 2
    }));

    this.nodes.forEach(node => {
      node.connections = this.links.filter(
        l => l.source === node.id || l.target === node.id
      ).length;
    });
  }

  _identifyCrossDependencies() {
    this.crossDependencies = this.links.filter(l => {
      const src = this.nodes.find(n => n.id === l.source);
      const tgt = this.nodes.find(n => n.id === l.target);
      return src && tgt && Math.abs(src.layer - tgt.layer) > 1;
    });
    this.stats.crossDeps = this.crossDependencies.length;
  }

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
  }

  _setupSimulation() {
    this.simulation = d3.forceSimulation(this.nodes)
      .force('link', d3.forceLink(this.links)
        .id(d => d.id)
        .distance(80))
      .force('charge', d3.forceManyBody().strength(-350))
      .force('center', d3.forceCenter(this.width / 2, this.height / 2))
      .force('collide', d3.forceCollide().radius(22))
      .force('x', d3.forceX(d => {
        const positions = [this.width * 0.08, this.width * 0.28, this.width * 0.48, this.width * 0.68, this.width * 0.88];
        return positions[d.layer] || this.width / 2;
      }).strength(0.15))
      .velocityDecay(0.4)
      .alphaMin(0.005);
  }

  _setupInteractions() {
    this.canvas.addEventListener('mousemove', (e) => this._handleMouseMove(e));
    this.canvas.addEventListener('mouseleave', () => this._handleMouseLeave());
    this.canvas.addEventListener('click', (e) => this._handleClick(e));

    let dragging = false;
    let dragNode = null;

    this.canvas.addEventListener('mousedown', (e) => {
      const mouse = this._getMousePosition(e);
      dragNode = this._findNodeAtPosition(mouse);
      if (dragNode) {
        dragging = true;
        this.simulation.alphaTarget(0.3).restart();
      }
    });

    this.canvas.addEventListener('mousemove', (e) => {
      if (dragging && dragNode) {
        const mouse = this._getMousePosition(e);
        dragNode.fx = mouse.x;
        dragNode.fy = mouse.y;
      }
    });

    const endDrag = () => {
      if (dragging && dragNode) {
        dragNode.fx = null;
        dragNode.fy = null;
        dragging = false;
        dragNode = null;
        this.simulation.alphaTarget(0);
      }
    };
    this.canvas.addEventListener('mouseup', endDrag);
    this.canvas.addEventListener('mouseleave', endDrag);
  }

  _setupWebSocket() {
    if (!this.wsUrl) return;
    this._connectWebSocket();
  }

  _connectWebSocket() {
    try {
      this.ws = new WebSocket(this.wsUrl);
      this.ws.onopen = () => {
        this.ws.send(JSON.stringify({ type: 'subscribe', channel: 'neurons' }));
      };
      this.ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        this._handleWebSocketMessage(data);
      };
      this.ws.onclose = () => {
        this.wsReconnectTimer = setTimeout(() => this._connectWebSocket(), 5000);
      };
      this.ws.onerror = () => {};
    } catch (error) {
      console.error('[NeuronNetwork] WebSocket error:', error);
    }
  }

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

  _updateNeuronState(neuronId, state) {
    const node = this.nodes.find(n => n.id === neuronId);
    if (node) {
      node.state = state;
      if (state === NEURON_STATES.FIRING) {
        node.firingIntensity = 1.0;
        node.lastFired = performance.now();
        this._spawnParticles(node);
      }
      this._updateStats();
    }
  }

  _updateConnectionActivity(source, target, active) {
    const link = this.links.find(l =>
      (typeof l.source === 'object' ? l.source.id : l.source) === source &&
      (typeof l.target === 'object' ? l.target.id : l.target) === target
    );
    if (link) link.active = active;
  }

  _fullUpdate(nodes, links) {
    if (nodes) {
      nodes.forEach(n => {
        const node = this.nodes.find(nd => nd.id === n.id);
        if (node) node.state = n.state;
      });
    }
    if (links) {
      links.forEach(l => {
        const link = this.links.find(lk =>
          (typeof lk.source === 'object' ? lk.source.id : lk.source) === l.source &&
          (typeof lk.target === 'object' ? lk.target.id : lk.target) === l.target
        );
        if (link) link.active = l.active;
      });
    }
    this._updateStats();
  }

  _spawnParticles(node) {
    const outLinks = this.links.filter(l => {
      const sid = typeof l.source === 'object' ? l.source.id : l.source;
      return sid === node.id;
    });

    outLinks.forEach(link => {
      const target = typeof link.target === 'object' ? link.target : this.nodes.find(n => n.id === link.target);
      if (!target || this.particles.length >= this.maxParticles) return;

      this.particles.push({
        sx: node.x, sy: node.y,
        tx: target.x, ty: target.y,
        progress: 0,
        speed: 0.012 + Math.random() * 0.015,
        color: link.inhibitory ? '#9C27B0' : this._getDomainColor(node.domain),
        size: 2 + Math.abs(link.weight) * 2
      });
    });
  }

  _startRenderLoop() {
    const render = () => {
      this._render();
      this.animationFrame = requestAnimationFrame(render);
    };
    render();
  }

  _render() {
    this.ctx.clearRect(0, 0, this.width, this.height);

    // Radial gradient background
    const bgGrad = this.ctx.createRadialGradient(
      this.width / 2, this.height / 2, 0,
      this.width / 2, this.height / 2, this.width * 0.6
    );
    bgGrad.addColorStop(0, '#0d1420');
    bgGrad.addColorStop(1, '#080c12');
    this.ctx.fillStyle = bgGrad;
    this.ctx.fillRect(0, 0, this.width, this.height);

    this.pulsePhase += 0.04;
    this.breathePhase += 0.012;
    this.synapticPhase += 0.03;

    // Global breathing
    const breathe = 1 + Math.sin(this.breathePhase) * 0.005;
    this.ctx.save();
    this.ctx.translate(this.width / 2 * (1 - breathe), this.height / 2 * (1 - breathe));
    this.ctx.scale(breathe, breathe);

    this._drawLinks();
    this._drawParticles();
    this._drawNodes();
    this._drawLayerLabels();

    this.ctx.restore();

    if (this.demoMode) this._simulateUpdates();

    // Decay firing intensity
    this.nodes.forEach(n => {
      if (n.firingIntensity > 0) n.firingIntensity = Math.max(0, n.firingIntensity - 0.008);
    });
  }

  _drawLinks() {
    this.links.forEach(link => {
      const source = typeof link.source === 'object' ? link.source : this.nodes.find(n => n.id === link.source);
      const target = typeof link.target === 'object' ? link.target : this.nodes.find(n => n.id === link.target);
      if (!source || !target) return;

      const absW = Math.abs(link.weight);
      const isHovered = this.hoveredNode &&
        (source.id === this.hoveredNode.id || target.id === this.hoveredNode.id);

      this.ctx.beginPath();
      this.ctx.moveTo(source.x, source.y);
      this.ctx.lineTo(target.x, target.y);

      if (link.inhibitory) {
        this.ctx.strokeStyle = `rgba(156, 39, 176, ${0.2 + absW * 0.3})`;
      } else if (link.isCross) {
        const pulse = 0.3 + Math.sin(this.synapticPhase + link.flowPhase) * 0.15;
        this.ctx.strokeStyle = `rgba(0, 188, 212, ${pulse + absW * 0.2})`;
      } else if (link.weight > 0) {
        this.ctx.strokeStyle = `rgba(76, 175, 80, ${0.15 + absW * 0.35})`;
      } else {
        this.ctx.strokeStyle = `rgba(255, 87, 34, ${0.15 + absW * 0.35})`;
      }

      if (isHovered) {
        this.ctx.strokeStyle = 'rgba(136, 204, 255, 0.8)';
        this.ctx.lineWidth = 2.5;
      } else {
        this.ctx.lineWidth = 0.8 + absW * 2.5;
      }

      if (this.hoveredNode && !isHovered) this.ctx.globalAlpha = 0.1;
      this.ctx.stroke();
      this.ctx.globalAlpha = 1;

      // Synaptic flow dots
      if ((link.active || link.isCross) && !this.hoveredNode) {
        const t = ((this.synapticPhase + link.flowPhase) % (Math.PI * 2)) / (Math.PI * 2);
        const fx = source.x + (target.x - source.x) * t;
        const fy = source.y + (target.y - source.y) * t;
        this.ctx.beginPath();
        this.ctx.arc(fx, fy, 2, 0, Math.PI * 2);
        this.ctx.fillStyle = link.isCross ? 'rgba(0, 188, 212, 0.7)' : 'rgba(136, 204, 255, 0.5)';
        this.ctx.fill();
      }
    });
  }

  _drawParticles() {
    this.particles = this.particles.filter(p => {
      p.progress += p.speed;
      if (p.progress >= 1) return false;

      const t = p.progress;
      p.x = p.sx + (p.tx - p.sx) * t;
      p.y = p.sy + (p.ty - p.sy) * t;

      this.ctx.beginPath();
      this.ctx.arc(p.x, p.y, p.size * (1 - t * 0.5), 0, Math.PI * 2);
      this.ctx.fillStyle = p.color;
      this.ctx.globalAlpha = 1 - t;
      this.ctx.fill();
      this.ctx.globalAlpha = 1;

      return true;
    });
  }

  _drawNodes() {
    this.nodes.forEach(node => {
      let radius = 14;
      const domainColor = this._getDomainColor(node.domain);
      const layerColor = LAYER_COLORS[node.layerName] || '#78909c';

      if (node.state === NEURON_STATES.FIRING) {
        radius += Math.sin(this.pulsePhase * 2 + node.pulseOffset) * 5;
      } else if (node.state === NEURON_STATES.ACTIVE) {
        radius += Math.sin(this.pulsePhase + node.pulseOffset) * 2;
      }

      if (this.hoveredNode === node) radius += 4;

      // Dim non-connected nodes when hovering
      if (this.hoveredNode && this.hoveredNode !== node) {
        const isConnected = this.links.some(l => {
          const sid = typeof l.source === 'object' ? l.source.id : l.source;
          const tid = typeof l.target === 'object' ? l.target.id : l.target;
          return (sid === this.hoveredNode.id && tid === node.id) ||
                 (tid === this.hoveredNode.id && sid === node.id);
        });
        if (!isConnected) this.ctx.globalAlpha = 0.15;
      }

      // Firing glow ring
      if (node.state === NEURON_STATES.FIRING || node.firingIntensity > 0.1) {
        const glowR = radius + 8 + Math.sin(this.pulsePhase * 3 + node.pulseOffset) * 4;
        const glowAlpha = node.state === NEURON_STATES.FIRING ? 0.35 : node.firingIntensity * 0.3;
        this.ctx.beginPath();
        this.ctx.arc(node.x, node.y, glowR, 0, Math.PI * 2);
        this.ctx.strokeStyle = `rgba(255, 87, 34, ${glowAlpha})`;
        this.ctx.lineWidth = 3;
        this.ctx.stroke();
      }

      // Domain color glow ring
      if (node.state !== NEURON_STATES.INACTIVE) {
        const domGlowR = radius + 4 + Math.sin(this.pulsePhase * 0.7 + node.pulseOffset) * 2;
        const savedAlpha = this.ctx.globalAlpha;
        this.ctx.beginPath();
        this.ctx.arc(node.x, node.y, domGlowR, 0, Math.PI * 2);
        this.ctx.strokeStyle = domainColor;
        this.ctx.globalAlpha = savedAlpha * 0.2;
        this.ctx.lineWidth = 2;
        this.ctx.stroke();
        this.ctx.globalAlpha = savedAlpha;
      }

      // Neuron body with gradient
      const grad = this.ctx.createRadialGradient(
        node.x - radius * 0.3, node.y - radius * 0.3, radius * 0.1,
        node.x, node.y, radius
      );
      grad.addColorStop(0, this._lightenColor(domainColor, 0.3));
      grad.addColorStop(0.6, domainColor);
      grad.addColorStop(1, this._darkenColor(domainColor, 0.4));

      this.ctx.beginPath();
      this.ctx.arc(node.x, node.y, radius, 0, Math.PI * 2);
      this.ctx.fillStyle = node.state === NEURON_STATES.INACTIVE ? NEURON_COLORS.inactive : grad;
      this.ctx.fill();

      // Layer border
      this.ctx.strokeStyle = layerColor;
      this.ctx.lineWidth = 2.5;
      this.ctx.stroke();

      // State indicator
      if (node.state !== NEURON_STATES.INACTIVE) {
        this.ctx.beginPath();
        this.ctx.arc(node.x, node.y, radius - 3, 0, Math.PI * 2);
        this.ctx.strokeStyle = NEURON_COLORS[node.state];
        this.ctx.lineWidth = 1.5;
        this.ctx.stroke();
      }

      // ID label
      this.ctx.fillStyle = '#ffffff';
      this.ctx.font = 'bold 8px sans-serif';
      this.ctx.textAlign = 'center';
      this.ctx.textBaseline = 'middle';
      this.ctx.fillText(node.id, node.x, node.y);

      // Name label below
      this.ctx.font = '9px sans-serif';
      this.ctx.fillStyle = 'rgba(200, 220, 240, 0.7)';
      this.ctx.fillText(node.label, node.x, node.y + radius + 12);

      this.ctx.globalAlpha = 1;
    });
  }

  _drawLayerLabels() {
    const labels = ['INPUT', 'CONTEXT', 'STATE', 'HIDDEN', 'OUTPUT'];
    const positions = [0.08, 0.28, 0.48, 0.68, 0.88];
    const colors = ['#2196F3', '#00BCD4', '#E91E63', '#9C27B0', '#FF9800'];

    this.ctx.font = 'bold 11px sans-serif';
    this.ctx.textAlign = 'center';

    labels.forEach((label, i) => {
      const x = this.width * positions[i];
      this.ctx.fillStyle = colors[i];
      this.ctx.globalAlpha = 0.4;
      this.ctx.fillText(label, x, 20);
      this.ctx.globalAlpha = 1;
    });
  }

  _lightenColor(hex, amount) {
    const r = parseInt(hex.slice(1, 3), 16);
    const g = parseInt(hex.slice(3, 5), 16);
    const b = parseInt(hex.slice(5, 7), 16);
    return `rgb(${Math.min(255, r + (255 - r) * amount)}, ${Math.min(255, g + (255 - g) * amount)}, ${Math.min(255, b + (255 - b) * amount)})`;
  }

  _darkenColor(hex, amount) {
    const r = parseInt(hex.slice(1, 3), 16);
    const g = parseInt(hex.slice(3, 5), 16);
    const b = parseInt(hex.slice(5, 7), 16);
    return `rgb(${Math.max(0, r * (1 - amount))}, ${Math.max(0, g * (1 - amount))}, ${Math.max(0, b * (1 - amount))})`;
  }

  _simulateUpdates() {
    if (Math.random() < 0.03) {
      const node = this.nodes[Math.floor(Math.random() * this.nodes.length)];
      const states = Object.values(NEURON_STATES);
      this._updateNeuronState(node.id, states[Math.floor(Math.random() * states.length)]);
    }

    // Cascade firing
    this.nodes.filter(n => n.state === NEURON_STATES.FIRING).forEach(firing => {
      if (Math.random() < 0.1) {
        const outLinks = this.links.filter(l => {
          const sid = typeof l.source === 'object' ? l.source.id : l.source;
          return sid === firing.id;
        });
        if (outLinks.length > 0) {
          const link = outLinks[Math.floor(Math.random() * outLinks.length)];
          const target = typeof link.target === 'object' ? link.target : this.nodes.find(n => n.id === link.target);
          if (target && target.state === NEURON_STATES.INACTIVE) {
            target.state = link.inhibitory ? NEURON_STATES.INHIBITED : NEURON_STATES.ACTIVE;
            this._updateStats();
          }
        }
      }
    });
  }

  _updateStats() {
    this.stats.active = this.nodes.filter(n => n.state === NEURON_STATES.ACTIVE).length;
    this.stats.firing = this.nodes.filter(n => n.state === NEURON_STATES.FIRING).length;
    this.stats.inhibited = this.nodes.filter(n => n.state === NEURON_STATES.INHIBITED).length;

    const els = {
      activeCount: this.stats.active,
      firingCount: this.stats.firing,
      inhibitedCount: this.stats.inhibited,
      crossDepCount: this.stats.crossDeps,
      neuronCount: this.stats.total,
      connectionCount: this.links.length
    };

    Object.entries(els).forEach(([id, val]) => {
      const el = document.getElementById(id);
      if (el) el.textContent = val;
    });
  }

  _getMousePosition(e) {
    const rect = this.canvas.getBoundingClientRect();
    return { x: e.clientX - rect.left, y: e.clientY - rect.top };
  }

  _findNodeAtPosition(mouse) {
    for (const node of this.nodes) {
      const dx = mouse.x - node.x;
      const dy = mouse.y - node.y;
      if (dx * dx + dy * dy < 500) return node;
    }
    return null;
  }

  _handleMouseMove(e) {
    const mouse = this._getMousePosition(e);
    const node = this._findNodeAtPosition(mouse);
    if (node !== this.hoveredNode) {
      this.hoveredNode = node;
      this._updateTooltip(node, mouse);
    }
  }

  _handleMouseLeave() {
    this.hoveredNode = null;
    this._hideTooltip();
  }

  _handleClick(e) {
    const mouse = this._getMousePosition(e);
    const node = this._findNodeAtPosition(mouse);
    if (node) {
      this._updateNeuronState(node.id, NEURON_STATES.FIRING);
      this._spawnParticles(node);
    }
  }

  _updateTooltip(node, mouse) {
    const tooltip = document.getElementById(this.tooltipId);
    if (!tooltip) return;

    if (node) {
      const connCount = this.links.filter(l => {
        const sid = typeof l.source === 'object' ? l.source.id : l.source;
        const tid = typeof l.target === 'object' ? l.target.id : l.target;
        return sid === node.id || tid === node.id;
      }).length;

      const crossCount = this.crossDependencies.filter(l => {
        const sid = typeof l.source === 'object' ? l.source.id : l.source;
        const tid = typeof l.target === 'object' ? l.target.id : l.target;
        return sid === node.id || tid === node.id;
      }).length;

      tooltip.innerHTML = `
        <div class="tooltip-title">${node.label} (${node.id})</div>
        <div class="tooltip-row"><span>Layer:</span><span class="value">${node.layerName}</span></div>
        <div class="tooltip-row"><span>Domain:</span><span class="value">${node.domain}</span></div>
        <div class="tooltip-row"><span>Zustand:</span><span class="value" style="color:${NEURON_COLORS[node.state]}">${node.state}</span></div>
        <div class="tooltip-row"><span>Verbindungen:</span><span class="value">${connCount}</span></div>
        <div class="tooltip-row"><span>Cross-Deps:</span><span class="value" style="color:#00BCD4">${crossCount}</span></div>
      `;
      tooltip.style.left = `${mouse.x + 15}px`;
      tooltip.style.top = `${mouse.y + 15}px`;
      tooltip.classList.add('visible');
    } else {
      this._hideTooltip();
    }
  }

  _hideTooltip() {
    const tooltip = document.getElementById(this.tooltipId);
    if (tooltip) tooltip.classList.remove('visible');
  }

  _handleResize() {
    this._setupCanvasSize();
    this.simulation.force('center', d3.forceCenter(this.width / 2, this.height / 2));
    this.simulation.alpha(0.3).restart();
  }

  resetLayout() {
    this.nodes = [];
    this.links = [];
    this.particles = [];
    this._createNodes();
    this._createLinks();
    this._identifyCrossDependencies();
    this.simulation.nodes(this.nodes);
    this.simulation.force('link').links(this.links);
    this.simulation.alpha(1).restart();
  }

  setDemoMode(enabled) { this.demoMode = enabled; }

  fireRandom() {
    const candidates = this.nodes.filter(n => n.state !== NEURON_STATES.FIRING);
    if (candidates.length > 0) {
      const node = candidates[Math.floor(Math.random() * candidates.length)];
      this._updateNeuronState(node.id, NEURON_STATES.FIRING);
      this._spawnParticles(node);
    }
  }

  fireCascade() {
    const inputNodes = this.nodes.filter(n => n.layerName === 'input');
    inputNodes.forEach((n, i) => {
      setTimeout(() => {
        this._updateNeuronState(n.id, NEURON_STATES.FIRING);
        this._spawnParticles(n);
      }, i * 200);
    });
  }

  destroy() {
    if (this.animationFrame) cancelAnimationFrame(this.animationFrame);
    if (this.ws) this.ws.close();
    if (this.wsReconnectTimer) clearTimeout(this.wsReconnectTimer);
    if (this.simulation) this.simulation.stop();
  }
}

document.addEventListener('DOMContentLoaded', () => {
  const network = new NeuronNetwork({
    canvasId: 'neuronCanvas',
    tooltipId: 'tooltip',
    demoMode: true,
    wsUrl: null
  });

  const toggleDemoBtn = document.getElementById('toggleDemoBtn');
  const resetLayoutBtn = document.getElementById('resetLayoutBtn');
  const fireRandomBtn = document.getElementById('fireRandomBtn');
  const fireCascadeBtn = document.getElementById('fireCascadeBtn');

  if (toggleDemoBtn) {
    toggleDemoBtn.addEventListener('click', () => {
      network.setDemoMode(!network.demoMode);
      toggleDemoBtn.textContent = network.demoMode ? 'Demo Pause' : 'Demo Start';
    });
  }
  if (resetLayoutBtn) resetLayoutBtn.addEventListener('click', () => network.resetLayout());
  if (fireRandomBtn) fireRandomBtn.addEventListener('click', () => network.fireRandom());
  if (fireCascadeBtn) fireCascadeBtn.addEventListener('click', () => network.fireCascade());

  const urlParams = new URLSearchParams(window.location.search);
  if (urlParams.has('demo')) network.setDemoMode(urlParams.get('demo') === '1');
  if (urlParams.has('ws')) {
    network.wsUrl = urlParams.get('ws');
    network._connectWebSocket();
  }

  window.neuronNetwork = network;
});
