/**
 * PilotSuite Brain Graph Card v4.0.0
 *
 * Living, pulsing, multi-colored Lovelace custom card that renders
 * a force-directed SVG brain graph with neural pipeline visualization.
 *
 * Features:
 * - 3-Layer pipeline layout: Context (green) → State (blue) → Mood (orange)
 * - Animated data flow particles between layers
 * - Pulsing nodes with domain-specific colors
 * - Cross-dependency highlighting on hover
 * - Firing ripple effects on active neurons
 * - Pipeline status bar with live metrics
 * - Input entity indicators per layer
 * - Smooth breathing animation
 */

const DOMAIN_COLORS = {
  light: "#f9d71c", switch: "#4caf50", sensor: "#2196f3",
  binary_sensor: "#03a9f4", climate: "#ff9800", media_player: "#e91e63",
  cover: "#9c27b0", person: "#00bcd4", automation: "#ff5722",
  script: "#795548", device_tracker: "#607d8b", zone: "#daa520",
  area: "#daa520", service: "#e06666", input_boolean: "#8bc34a",
  input_number: "#cddc39", scene: "#ab47bc", group: "#78909c",
  default: "#4aa3df",
};

const LAYER_CONFIG = {
  context: { color: "#22d3ee", bg: "#22d3ee", label: "Context", icon: "C", order: 0 },
  state:   { color: "#a78bfa", bg: "#a78bfa", label: "State",   icon: "S", order: 1 },
  mood:    { color: "#fb923c", bg: "#fb923c", label: "Mood",    icon: "M", order: 2 },
  input:   { color: "#22d3ee", bg: "#22d3ee", label: "Input",   icon: "I", order: 0 },
  hidden:  { color: "#a78bfa", bg: "#a78bfa", label: "Hidden",  icon: "H", order: 1 },
  output:  { color: "#fb923c", bg: "#fb923c", label: "Output",  icon: "O", order: 2 },
};

class StyxBrainCard extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._config = {};
    this._nodes = [];
    this._edges = [];
    this._animFrame = null;
    this._phase = 0;
    this._hoveredNode = null;
    this._svgEl = null;
    this._flowParticles = [];
  }

  static getConfigElement() {
    return document.createElement("hui-generic-entity-row");
  }

  static getStubConfig() {
    return { entity: "sensor.pilotsuite_brain_graph_nodes" };
  }

  setConfig(config) {
    if (!config.entity) throw new Error("Please define an entity");
    this._config = config;
  }

  set hass(hass) {
    this._hass = hass;
    const nodeEntity = hass.states[this._config.entity];
    const edgeEntityId = this._config.edge_entity || "sensor.pilotsuite_brain_graph_edges";
    const edgeEntity = hass.states[edgeEntityId];

    const nodes = nodeEntity
      ? nodeEntity.attributes.nodes || nodeEntity.attributes.graph_nodes || []
      : [];
    const edges = edgeEntity
      ? edgeEntity.attributes.edges || edgeEntity.attributes.graph_edges || []
      : [];

    if (this._hasDataChanged(nodes, edges)) {
      this._nodes = nodes;
      this._edges = edges;
      this._render();
    }
  }

  _hasDataChanged(newNodes, newEdges) {
    if (newNodes.length !== this._nodes.length || newEdges.length !== this._edges.length) return true;
    if (newNodes.length === 0) return false;
    const sumScore = arr => arr.reduce((s, n) => s + (n.score || 0), 0);
    if (Math.abs(sumScore(newNodes) - sumScore(this._nodes)) > 0.01) return true;
    const nid = n => n.id || n.node_id || '';
    if (nid(newNodes[0]) !== nid(this._nodes[0])) return true;
    return false;
  }

  disconnectedCallback() {
    if (this._animFrame) { cancelAnimationFrame(this._animFrame); this._animFrame = null; }
  }

  getCardSize() { return 7; }

  _nodeColor(node) {
    const layer = (node.layer || node.neural_layer || "").toLowerCase();
    if (LAYER_CONFIG[layer]) return LAYER_CONFIG[layer].color;
    const domain = (node.domain || "default").split(".")[0];
    return DOMAIN_COLORS[domain] || DOMAIN_COLORS.default;
  }

  _nodeLayer(node) {
    const layer = (node.layer || node.neural_layer || "").toLowerCase();
    if (LAYER_CONFIG[layer]) return LAYER_CONFIG[layer].order;
    const domain = (node.domain || "default").split(".")[0];
    if (["sensor", "binary_sensor", "device_tracker", "person"].includes(domain)) return 0;
    if (["switch", "cover", "lock", "climate", "input_boolean"].includes(domain)) return 1;
    if (["light", "media_player", "scene", "automation"].includes(domain)) return 2;
    return 1;
  }

  _layoutNodes(nodes, w, h) {
    // 3-column pipeline layout: Context | State | Mood
    const layers = [[], [], []];
    nodes.forEach((n, i) => {
      const layerIdx = this._nodeLayer(n);
      layers[layerIdx].push({ ...n, _idx: i });
    });

    const colW = w / 3;
    const padX = 40;
    const padY = 40;
    const result = new Array(nodes.length);

    layers.forEach((layer, li) => {
      const cx = padX + li * colW + colW / 2 - padX;
      const count = Math.max(1, layer.length);
      const maxPerCol = Math.ceil(Math.sqrt(count));

      layer.forEach((n, ni) => {
        const row = Math.floor(ni / maxPerCol);
        const col = ni % maxPerCol;
        const rows = Math.ceil(count / maxPerCol);
        const cols = Math.min(count, maxPerCol);

        const spacingX = Math.min(colW * 0.7, cols > 1 ? (colW - padX * 1.2) / (cols - 1) : 0);
        const spacingY = rows > 1 ? (h - padY * 2) / (rows - 1) : 0;

        const x = cx - (cols - 1) * spacingX / 2 + col * spacingX;
        const y = padY + row * spacingY + (h - padY * 2) / 2 - (rows - 1) * spacingY / 2;

        // Add organic jitter
        const jx = Math.sin(n._idx * 5.7 + li * 2) * 8;
        const jy = Math.cos(n._idx * 3.3 + li) * 6;

        result[n._idx] = {
          ...n,
          x: Math.max(15, Math.min(w - 15, x + jx)),
          y: Math.max(15, Math.min(h - 15, y + jy)),
          _layerIdx: li,
        };
      });
    });

    return result.filter(Boolean);
  }

  _getConnectedNodes(nodeId) {
    const connected = new Set();
    this._edges.forEach(e => {
      const from = e.from || e.source_id;
      const to = e.to || e.target_id;
      if (from === nodeId) connected.add(to);
      if (to === nodeId) connected.add(from);
    });
    return connected;
  }

  _render() {
    const w = 580, h = 380;
    const positioned = this._layoutNodes(this._nodes.slice(0, 150), w, h);

    const idMap = {};
    positioned.forEach((n, i) => {
      const id = n.id || n.node_id || `n${i}`;
      idMap[id] = { ...n, _nid: id };
    });

    const nodeCount = this._nodes.length;
    const edgeCount = this._edges.length;

    // Layer stats
    const layerCounts = [0, 0, 0];
    positioned.forEach(n => { layerCounts[n._layerIdx]++; });

    // Active neurons (score > 0.5)
    const activeCount = positioned.filter(n => (n.score || 0) > 0.5).length;

    // Cross-layer edges
    let crossCount = 0;
    this._edges.slice(0, 300).forEach(e => {
      const src = idMap[e.from || e.source_id];
      const tgt = idMap[e.to || e.target_id];
      if (src && tgt && src._layerIdx !== tgt._layerIdx) crossCount++;
    });

    const layerLabels = ["Context", "State", "Mood"];
    const layerColors = ["#22d3ee", "#a78bfa", "#fb923c"];

    this.shadowRoot.innerHTML = `
      <style>
        :host { display: block; }
        ha-card { overflow: hidden; background: var(--card-background-color, #1a1a2e); border: 1px solid rgba(255,255,255,0.06); }

        .brain-header {
          padding: 16px 20px 10px;
          display: flex;
          justify-content: space-between;
          align-items: center;
        }
        .brain-title {
          font-size: 0.9375rem;
          font-weight: 600;
          color: var(--primary-text-color, #e0e0f0);
          display: flex;
          align-items: center;
          gap: 8px;
        }
        .pulse-dot {
          width: 8px; height: 8px; border-radius: 50%;
          background: #34d399;
          animation: pulse-glow 2s ease-in-out infinite;
          box-shadow: 0 0 6px #34d39960;
        }
        @keyframes pulse-glow {
          0%, 100% { opacity: 1; box-shadow: 0 0 4px #34d39960; }
          50% { opacity: 0.5; box-shadow: 0 0 12px #34d39990; }
        }
        .brain-meta {
          font-size: 0.6875rem;
          color: var(--secondary-text-color, #9e9eb8);
        }

        /* Pipeline status chips */
        .pipeline-bar {
          display: flex;
          gap: 6px;
          padding: 0 20px 12px;
          flex-wrap: wrap;
        }
        .pipe-chip {
          font-size: 0.6875rem;
          padding: 3px 10px;
          border-radius: 12px;
          font-weight: 500;
          letter-spacing: 0.3px;
          display: flex;
          align-items: center;
          gap: 4px;
        }
        .pipe-chip .chip-dot {
          width: 6px; height: 6px; border-radius: 50%;
        }
        .pipe-chip.context { background: #22d3ee12; color: #22d3ee; border: 1px solid #22d3ee25; }
        .pipe-chip.context .chip-dot { background: #22d3ee; }
        .pipe-chip.state { background: #a78bfa12; color: #a78bfa; border: 1px solid #a78bfa25; }
        .pipe-chip.state .chip-dot { background: #a78bfa; }
        .pipe-chip.mood { background: #fb923c12; color: #fb923c; border: 1px solid #fb923c25; }
        .pipe-chip.mood .chip-dot { background: #fb923c; }
        .pipe-chip.active { background: #34d39912; color: #34d399; border: 1px solid #34d39925; }
        .pipe-chip.cross { background: #60a5fa12; color: #60a5fa; border: 1px solid #60a5fa25; }

        /* SVG container */
        .graph-wrap { position: relative; padding: 0 8px 8px; }
        svg {
          width: 100%; height: auto;
          border-radius: 8px;
          background: #0c1118;
          border: 1px solid rgba(255,255,255,0.04);
        }

        .edge-line { transition: stroke-opacity 0.3s; }
        .node-g { cursor: pointer; }
        .node-g:hover .node-circle { filter: brightness(1.5) drop-shadow(0 0 6px currentColor); }
        .node-label { pointer-events: none; user-select: none; }

        /* Pulsing glow ring */
        @keyframes pulseRing {
          0%, 100% { opacity: 0; transform: scale(1); }
          50% { opacity: 0.4; transform: scale(1.6); }
        }
        .glow-ring {
          animation: pulseRing 3s ease-in-out infinite;
          fill: none; pointer-events: none;
          transform-origin: center;
        }

        /* Firing ripple */
        @keyframes fireRipple {
          0% { r: 4; opacity: 0.8; }
          100% { r: 20; opacity: 0; }
        }
        .fire-ripple {
          fill: none; stroke-width: 1.5; pointer-events: none;
          animation: fireRipple 2s ease-out infinite;
        }

        /* Synaptic flow particles */
        @keyframes flowDash {
          0% { stroke-dashoffset: 24; }
          100% { stroke-dashoffset: 0; }
        }
        .edge-flow {
          stroke-dasharray: 3 21;
          animation: flowDash 1.5s linear infinite;
        }

        /* Pipeline flow arrows */
        .flow-arrow {
          fill: none;
          stroke-dasharray: 6 10;
          animation: flowDash 2s linear infinite;
        }

        /* Layer region backgrounds */
        .layer-region { pointer-events: none; }

        /* Tooltip */
        .tooltip-panel {
          position: absolute;
          top: 12px; right: 20px;
          max-width: 220px;
          background: rgba(10, 14, 20, 0.95);
          border: 1px solid rgba(255,255,255,0.1);
          border-radius: 10px;
          padding: 12px;
          font-size: 0.75rem;
          display: none;
          z-index: 10;
          pointer-events: none;
          backdrop-filter: blur(8px);
        }
        .tooltip-panel.visible { display: block; }
        .tp-title { font-weight: 600; margin-bottom: 6px; font-size: 0.8125rem; }
        .tp-row { display: flex; justify-content: space-between; color: var(--secondary-text-color, #9e9eb8); padding: 2px 0; }
        .tp-val { color: var(--primary-text-color, #e0e0f0); font-variant-numeric: tabular-nums; }
        .tp-layer-badge {
          display: inline-block;
          padding: 1px 6px;
          border-radius: 6px;
          font-size: 0.625rem;
          font-weight: 600;
          text-transform: uppercase;
        }

        /* Legend */
        .brain-legend {
          display: flex;
          flex-wrap: wrap;
          gap: 8px;
          padding: 8px 20px 14px;
          font-size: 0.6875rem;
          color: var(--secondary-text-color, #9e9eb8);
        }
        .legend-item {
          display: flex;
          align-items: center;
          gap: 4px;
        }
        .legend-dot {
          width: 7px; height: 7px; border-radius: 50%; flex-shrink: 0;
        }
      </style>
      <ha-card>
        <div class="brain-header">
          <span class="brain-title"><span class="pulse-dot"></span>Neural Pipeline</span>
          <span class="brain-meta">${nodeCount} Neuronen &middot; ${edgeCount} Synapsen</span>
        </div>
        <div class="pipeline-bar">
          <span class="pipe-chip context"><span class="chip-dot"></span>Context ${layerCounts[0]}</span>
          <span class="pipe-chip state"><span class="chip-dot"></span>State ${layerCounts[1]}</span>
          <span class="pipe-chip mood"><span class="chip-dot"></span>Mood ${layerCounts[2]}</span>
          <span class="pipe-chip active"><span class="chip-dot"></span>Aktiv ${activeCount}</span>
          <span class="pipe-chip cross"><span class="chip-dot"></span>Cross ${crossCount}</span>
        </div>
        <div class="graph-wrap">
          <svg id="brain-svg" viewBox="0 0 ${w} ${h}" role="img" aria-label="PilotSuite Neural Pipeline">
            <defs>
              <radialGradient id="bg-grad" cx="50%" cy="50%" r="55%">
                <stop offset="0%" stop-color="#0f1720"/>
                <stop offset="100%" stop-color="#080c12"/>
              </radialGradient>
              <filter id="glow">
                <feGaussianBlur stdDeviation="3" result="blur"/>
                <feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>
              </filter>
              <filter id="soft-glow">
                <feGaussianBlur stdDeviation="6" result="blur"/>
                <feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>
              </filter>
              <marker id="arrow-ctx" markerWidth="6" markerHeight="4" refX="5" refY="2" orient="auto">
                <path d="M0,0 L6,2 L0,4" fill="#22d3ee" fill-opacity="0.3"/>
              </marker>
              <marker id="arrow-mood" markerWidth="6" markerHeight="4" refX="5" refY="2" orient="auto">
                <path d="M0,0 L6,2 L0,4" fill="#fb923c" fill-opacity="0.3"/>
              </marker>
            </defs>
            <rect x="0" y="0" width="${w}" height="${h}" fill="url(#bg-grad)"/>
            <g class="layer-regions"></g>
            <g class="flow-arrows"></g>
            <g class="edges-layer"></g>
            <g class="nodes-layer"></g>
          </svg>
          <div class="tooltip-panel" id="tp"></div>
        </div>
        <div class="brain-legend" id="legend-container"></div>
      </ha-card>`;

    this._svgEl = this.shadowRoot.querySelector("#brain-svg");
    const layerRegions = this._svgEl.querySelector(".layer-regions");
    const flowArrows = this._svgEl.querySelector(".flow-arrows");
    const edgesLayer = this._svgEl.querySelector(".edges-layer");
    const nodesLayer = this._svgEl.querySelector(".nodes-layer");
    const tooltipPanel = this.shadowRoot.querySelector("#tp");

    // Draw layer region backgrounds
    const colW = w / 3;
    for (let i = 0; i < 3; i++) {
      const rect = document.createElementNS("http://www.w3.org/2000/svg", "rect");
      rect.setAttribute("x", (i * colW).toFixed(0));
      rect.setAttribute("y", "0");
      rect.setAttribute("width", colW.toFixed(0));
      rect.setAttribute("height", h);
      rect.setAttribute("fill", layerColors[i]);
      rect.setAttribute("fill-opacity", "0.03");
      rect.classList.add("layer-region");
      layerRegions.appendChild(rect);

      // Layer label at top
      const text = document.createElementNS("http://www.w3.org/2000/svg", "text");
      text.setAttribute("x", (i * colW + colW / 2).toFixed(0));
      text.setAttribute("y", "16");
      text.setAttribute("text-anchor", "middle");
      text.setAttribute("font-size", "9");
      text.setAttribute("font-weight", "600");
      text.setAttribute("fill", layerColors[i]);
      text.setAttribute("fill-opacity", "0.5");
      text.setAttribute("font-family", "system-ui,sans-serif");
      text.setAttribute("letter-spacing", "1.5");
      text.textContent = layerLabels[i].toUpperCase();
      layerRegions.appendChild(text);

      // Separator lines
      if (i > 0) {
        const line = document.createElementNS("http://www.w3.org/2000/svg", "line");
        line.setAttribute("x1", (i * colW).toFixed(0));
        line.setAttribute("y1", "0");
        line.setAttribute("x2", (i * colW).toFixed(0));
        line.setAttribute("y2", h);
        line.setAttribute("stroke", "rgba(255,255,255,0.04)");
        line.setAttribute("stroke-width", "1");
        line.setAttribute("stroke-dasharray", "4 4");
        layerRegions.appendChild(line);
      }
    }

    // Draw pipeline flow arrows between layers
    for (let i = 0; i < 2; i++) {
      const x1 = (i + 1) * colW - 10;
      const x2 = (i + 1) * colW + 10;
      const midY = h / 2;
      for (let dy = -60; dy <= 60; dy += 40) {
        const arrow = document.createElementNS("http://www.w3.org/2000/svg", "line");
        arrow.setAttribute("x1", x1.toFixed(0));
        arrow.setAttribute("y1", (midY + dy).toFixed(0));
        arrow.setAttribute("x2", x2.toFixed(0));
        arrow.setAttribute("y2", (midY + dy).toFixed(0));
        arrow.setAttribute("stroke", i === 0 ? "#22d3ee" : "#fb923c");
        arrow.setAttribute("stroke-opacity", "0.15");
        arrow.setAttribute("stroke-width", "2");
        arrow.classList.add("flow-arrow");
        arrow.setAttribute("marker-end", i === 0 ? "url(#arrow-ctx)" : "url(#arrow-mood)");
        arrow.style.animationDelay = `${(dy + 60) * 0.02}s`;
        flowArrows.appendChild(arrow);
      }
    }

    // Draw edges
    this._edges.slice(0, 300).forEach((e, ei) => {
      const src = idMap[e.from || e.source_id];
      const tgt = idMap[e.to || e.target_id];
      if (!src || !tgt) return;

      const isCross = src._layerIdx !== tgt._layerIdx;
      const weight = Math.max(0.3, Math.min(1, e.weight || 0.5));

      const line = document.createElementNS("http://www.w3.org/2000/svg", "line");
      line.setAttribute("x1", src.x.toFixed(1));
      line.setAttribute("y1", src.y.toFixed(1));
      line.setAttribute("x2", tgt.x.toFixed(1));
      line.setAttribute("y2", tgt.y.toFixed(1));

      const edgeColor = isCross
        ? `hsl(${200 + src._layerIdx * 40}, 60%, 55%)`
        : `hsl(${190 + src._layerIdx * 50}, 30%, 35%)`;

      line.setAttribute("stroke", edgeColor);
      line.setAttribute("stroke-opacity", (0.1 + weight * 0.2).toFixed(2));
      line.setAttribute("stroke-width", (0.5 + weight * 1.2).toFixed(1));
      line.classList.add("edge-line");
      line.dataset.from = src._nid;
      line.dataset.to = tgt._nid;
      line._origOpacity = (0.1 + weight * 0.2).toFixed(2);
      line._origWidth = (0.5 + weight * 1.2).toFixed(1);
      line._origStroke = edgeColor;
      edgesLayer.appendChild(line);

      // Flow particles on strong or cross-layer edges
      if (weight > 0.5 || isCross) {
        const flow = document.createElementNS("http://www.w3.org/2000/svg", "line");
        flow.setAttribute("x1", src.x.toFixed(1));
        flow.setAttribute("y1", src.y.toFixed(1));
        flow.setAttribute("x2", tgt.x.toFixed(1));
        flow.setAttribute("y2", tgt.y.toFixed(1));
        const flowColor = isCross ? layerColors[Math.max(src._layerIdx, tgt._layerIdx)] : "#4aa3df";
        flow.setAttribute("stroke", flowColor);
        flow.setAttribute("stroke-opacity", "0.25");
        flow.setAttribute("stroke-width", "1.5");
        flow.classList.add("edge-flow");
        flow.style.animationDelay = `${(ei * 0.13) % 2}s`;
        edgesLayer.appendChild(flow);
      }
    });

    // Draw nodes
    const usedDomains = new Set();
    positioned.forEach((n, ni) => {
      const nid = n.id || n.node_id || `n${ni}`;
      const score = Math.max(0, Math.min(1, n.score || 0.5));
      const baseR = 3.5 + 7 * score;
      const fill = this._nodeColor(n);
      const domain = (n.domain || "default").split(".")[0];
      usedDomains.add(domain);
      const label = (n.label || n.name || n.id || "").substring(0, 20);
      const layerIdx = n._layerIdx;

      const g = document.createElementNS("http://www.w3.org/2000/svg", "g");
      g.classList.add("node-g");
      g.dataset.nid = nid;

      // Firing ripple for high-score neurons
      if (score > 0.7) {
        const ripple = document.createElementNS("http://www.w3.org/2000/svg", "circle");
        ripple.setAttribute("cx", n.x.toFixed(1));
        ripple.setAttribute("cy", n.y.toFixed(1));
        ripple.setAttribute("r", "4");
        ripple.setAttribute("stroke", fill);
        ripple.classList.add("fire-ripple");
        ripple.style.animationDelay = `${(ni * 0.3) % 2}s`;
        g.appendChild(ripple);
      }

      // Glow ring
      if (score > 0.3) {
        const glow = document.createElementNS("http://www.w3.org/2000/svg", "circle");
        glow.setAttribute("cx", n.x.toFixed(1));
        glow.setAttribute("cy", n.y.toFixed(1));
        glow.setAttribute("r", (baseR + 4).toFixed(1));
        glow.setAttribute("stroke", fill);
        glow.setAttribute("stroke-width", "1.5");
        glow.classList.add("glow-ring");
        glow.style.animationDelay = `${(ni * 0.25) % 3}s`;
        g.appendChild(glow);
      }

      // Main node circle
      const circle = document.createElementNS("http://www.w3.org/2000/svg", "circle");
      circle.setAttribute("cx", n.x.toFixed(1));
      circle.setAttribute("cy", n.y.toFixed(1));
      circle.setAttribute("r", baseR.toFixed(1));
      circle.setAttribute("fill", fill);
      circle.setAttribute("fill-opacity", (0.4 + 0.6 * score).toFixed(2));
      circle.setAttribute("stroke", fill);
      circle.setAttribute("stroke-opacity", "0.5");
      circle.setAttribute("stroke-width", "0.8");
      circle.classList.add("node-circle");
      g.appendChild(circle);

      // Label (show for sparse graphs or high-score nodes)
      if (positioned.length <= 40 || score > 0.6) {
        const text = document.createElementNS("http://www.w3.org/2000/svg", "text");
        text.setAttribute("x", (n.x + baseR + 3).toFixed(1));
        text.setAttribute("y", (n.y + 3).toFixed(1));
        text.setAttribute("font-size", "8");
        text.setAttribute("fill", "#8899aa");
        text.setAttribute("fill-opacity", "0.7");
        text.setAttribute("font-family", "system-ui,sans-serif");
        text.classList.add("node-label");
        text.textContent = label;
        g.appendChild(text);
      }

      // Hover interactions
      g.addEventListener("mouseenter", () => {
        this._hoveredNode = nid;
        const connected = this._getConnectedNodes(nid);
        edgesLayer.querySelectorAll(".edge-line").forEach(el => {
          if (el.dataset.from === nid || el.dataset.to === nid) {
            el.setAttribute("stroke-opacity", "0.8");
            el.setAttribute("stroke-width", "2.5");
            el.setAttribute("stroke", layerColors[layerIdx] || "#88ccff");
          } else {
            el.setAttribute("stroke-opacity", "0.03");
          }
        });
        nodesLayer.querySelectorAll(".node-g").forEach(ng => {
          if (ng.dataset.nid !== nid && !connected.has(ng.dataset.nid)) ng.style.opacity = "0.15";
        });
        const layerName = layerLabels[layerIdx] || "Unknown";
        const layerCol = layerColors[layerIdx] || "#888";
        tooltipPanel.classList.add("visible");
        tooltipPanel.innerHTML = `
          <div class="tp-title" style="color:${layerCol}">${this._esc(label || nid)}</div>
          <div class="tp-row"><span>Layer</span><span class="tp-layer-badge" style="background:${layerCol}20;color:${layerCol}">${layerName}</span></div>
          <div class="tp-row"><span>Domain</span><span class="tp-val">${domain}</span></div>
          <div class="tp-row"><span>Score</span><span class="tp-val">${(score * 100).toFixed(0)}%</span></div>
          <div class="tp-row"><span>Verbindungen</span><span class="tp-val">${connected.size}</span></div>
          ${n.zone ? `<div class="tp-row"><span>Zone</span><span class="tp-val">${n.zone}</span></div>` : ""}
        `;
      });

      g.addEventListener("mouseleave", () => {
        this._hoveredNode = null;
        edgesLayer.querySelectorAll(".edge-line").forEach(el => {
          el.setAttribute("stroke", el._origStroke || "#3a5060");
          el.setAttribute("stroke-opacity", el._origOpacity || "0.15");
          el.setAttribute("stroke-width", el._origWidth || "1");
        });
        nodesLayer.querySelectorAll(".node-g").forEach(ng => { ng.style.opacity = "1"; });
        tooltipPanel.classList.remove("visible");
      });

      nodesLayer.appendChild(g);
    });

    // Legend
    const legendEl = this.shadowRoot.querySelector("#legend-container");
    if (legendEl) {
      let html = "";
      // Layer legend first
      layerLabels.forEach((l, i) => {
        html += `<span class="legend-item"><span class="legend-dot" style="background:${layerColors[i]}"></span>${l}</span>`;
      });
      // Domain legend
      usedDomains.forEach(d => {
        const c = DOMAIN_COLORS[d] || DOMAIN_COLORS.default;
        html += `<span class="legend-item"><span class="legend-dot" style="background:${c}"></span>${d}</span>`;
      });
      legendEl.innerHTML = html;
    }

    this._startAnimation();
  }

  _esc(s) {
    const el = document.createElement('span');
    el.textContent = s || '';
    return el.innerHTML;
  }

  _startAnimation() {
    if (this._animFrame) cancelAnimationFrame(this._animFrame);
    const animate = () => {
      this._phase += 0.012;
      if (this._svgEl) {
        const breathe = 1 + Math.sin(this._phase) * 0.005;
        const nl = this._svgEl.querySelector(".nodes-layer");
        const el = this._svgEl.querySelector(".edges-layer");
        if (nl) { nl.style.transform = `scale(${breathe.toFixed(4)})`; nl.style.transformOrigin = "center center"; }
        if (el) { el.style.transform = `scale(${breathe.toFixed(4)})`; el.style.transformOrigin = "center center"; }
      }
      this._animFrame = requestAnimationFrame(animate);
    };
    this._animFrame = requestAnimationFrame(animate);
  }
}

if (typeof registerStyxCard === 'function') {
  registerStyxCard("styx-brain-card", StyxBrainCard, {
    name: "PilotSuite Neural Pipeline",
    description: "Neurale Pipeline mit 3-Layer-Layout, Flow-Partikeln und Firing-Ripples.",
  });
} else {
  customElements.define("styx-brain-card", StyxBrainCard);
  window.customCards = window.customCards || [];
  window.customCards.push({
    type: "styx-brain-card",
    name: "PilotSuite Neural Pipeline",
    description: "Neurale Pipeline mit 3-Layer-Layout, Flow-Partikeln und Firing-Ripples.",
    preview: true,
  });
}
