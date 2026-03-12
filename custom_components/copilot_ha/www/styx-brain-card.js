/**
 * PilotSuite Brain Graph Card v3.0.0
 *
 * Living, pulsing, multi-colored Lovelace custom card that renders
 * a force-directed SVG brain graph with neural cross-dependencies,
 * animated synaptic connections, and real-time neuron firing visualization.
 *
 * Features:
 * - Pulsing nodes with domain-specific colors (multi-colored Neuronennetz)
 * - Animated synaptic edge flow (living connections)
 * - Cross-dependency highlighting on hover
 * - Neural layer grouping (Context -> State -> Mood)
 * - Automation suggestion indicators
 * - Smooth breathing animation for the entire graph
 */

const DOMAIN_COLORS = {
  light: "#f9d71c",
  switch: "#4caf50",
  sensor: "#2196f3",
  binary_sensor: "#03a9f4",
  climate: "#ff9800",
  media_player: "#e91e63",
  cover: "#9c27b0",
  person: "#00bcd4",
  automation: "#ff5722",
  script: "#795548",
  device_tracker: "#607d8b",
  zone: "#daa520",
  area: "#daa520",
  service: "#e06666",
  input_boolean: "#8bc34a",
  input_number: "#cddc39",
  scene: "#ab47bc",
  group: "#78909c",
  default: "#4aa3df",
};

/** Neural layer colors for neuron-type nodes */
const NEURAL_LAYER_COLORS = {
  context: "#2196F3",
  state: "#9C27B0",
  mood: "#FF9800",
  input: "#2196F3",
  hidden: "#9C27B0",
  output: "#FF9800",
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
    this._initialized = false;
  }

  static getConfigElement() {
    return document.createElement("hui-generic-entity-row");
  }

  static getStubConfig() {
    return { entity: "sensor.pilotsuite_brain_graph_nodes" };
  }

  setConfig(config) {
    if (!config.entity) {
      throw new Error("Please define an entity");
    }
    this._config = config;
  }

  set hass(hass) {
    this._hass = hass;
    const nodeEntity = hass.states[this._config.entity];
    const edgeEntityId =
      this._config.edge_entity || "sensor.pilotsuite_brain_graph_edges";
    const edgeEntity = hass.states[edgeEntityId];

    const nodes = nodeEntity
      ? nodeEntity.attributes.nodes || nodeEntity.attributes.graph_nodes || []
      : [];
    const edges = edgeEntity
      ? edgeEntity.attributes.edges || edgeEntity.attributes.graph_edges || []
      : [];

    if (
      JSON.stringify(nodes) !== JSON.stringify(this._nodes) ||
      JSON.stringify(edges) !== JSON.stringify(this._edges)
    ) {
      this._nodes = nodes;
      this._edges = edges;
      this._render();
    }
  }

  disconnectedCallback() {
    if (this._animFrame) {
      cancelAnimationFrame(this._animFrame);
      this._animFrame = null;
    }
  }

  getCardSize() {
    return 6;
  }

  _colorForDomain(domain) {
    return DOMAIN_COLORS[domain] || DOMAIN_COLORS.default;
  }

  _neuralColor(node) {
    const layer = (node.layer || node.neural_layer || "").toLowerCase();
    if (NEURAL_LAYER_COLORS[layer]) return NEURAL_LAYER_COLORS[layer];
    const domain = (node.domain || "default").split(".")[0];
    return this._colorForDomain(domain);
  }

  _layoutNodes(nodes, w, h) {
    const cx = w / 2;
    const cy = h / 2;
    const r = Math.min(w, h) * 0.36;
    const count = Math.max(1, nodes.length);

    // Group nodes by domain/layer for cluster layout
    const groups = {};
    nodes.forEach((n, i) => {
      const key = n.layer || n.neural_layer || (n.domain || "default").split(".")[0];
      if (!groups[key]) groups[key] = [];
      groups[key].push({ ...n, _idx: i });
    });

    const groupKeys = Object.keys(groups);
    const result = new Array(nodes.length);

    groupKeys.forEach((key, gi) => {
      const group = groups[key];
      const groupAngle = (2 * Math.PI * gi) / Math.max(1, groupKeys.length);
      const groupCx = cx + r * 0.5 * Math.cos(groupAngle);
      const groupCy = cy + r * 0.5 * Math.sin(groupAngle);
      const subR = r * 0.35 * Math.sqrt(group.length / count + 0.1);

      group.forEach((n, si) => {
        const subAngle = (2 * Math.PI * si) / Math.max(1, group.length);
        const jitter = Math.sin(n._idx * 7) * subR * 0.15;
        result[n._idx] = {
          ...n,
          x: groupCx + (subR + jitter) * Math.cos(subAngle),
          y: groupCy + (subR + jitter) * Math.sin(subAngle),
          _group: key,
        };
      });
    });

    return result.filter(Boolean);
  }

  _getConnectedNodes(nodeId) {
    const connected = new Set();
    this._edges.forEach((e) => {
      const from = e.from || e.source_id;
      const to = e.to || e.target_id;
      if (from === nodeId) connected.add(to);
      if (to === nodeId) connected.add(from);
    });
    return connected;
  }

  _render() {
    const w = 520;
    const h = 400;
    const positioned = this._layoutNodes(this._nodes.slice(0, 150), w, h);

    const idMap = {};
    positioned.forEach((n, i) => {
      const id = n.id || n.node_id || `n${i}`;
      idMap[id] = { ...n, _nid: id };
    });

    const nodeCount = this._nodes.length;
    const edgeCount = this._edges.length;

    // Count cross-dependencies (edges spanning different domains)
    let crossDeps = 0;
    this._edges.slice(0, 300).forEach((e) => {
      const src = idMap[e.from || e.source_id];
      const tgt = idMap[e.to || e.target_id];
      if (src && tgt && src._group !== tgt._group) crossDeps++;
    });

    this.shadowRoot.innerHTML = `
      <style>
        :host { display: block; }
        .card {
          background: var(--card-background-color, #0a0e14);
          border-radius: var(--ha-card-border-radius, 12px);
          padding: 16px;
          color: var(--primary-text-color, #e6eef6);
          font-family: var(--paper-font-body1_-_font-family, system-ui, sans-serif);
        }
        .header {
          display: flex; justify-content: space-between; align-items: center;
          margin-bottom: 8px;
        }
        .title { font-size: 16px; font-weight: 600; }
        .pulse-dot {
          display: inline-block; width: 8px; height: 8px; border-radius: 50%;
          background: #4caf50; margin-right: 6px; vertical-align: middle;
          animation: pulseDot 2s ease-in-out infinite;
        }
        @keyframes pulseDot {
          0%, 100% { opacity: 1; box-shadow: 0 0 4px #4caf50; }
          50% { opacity: 0.4; box-shadow: 0 0 12px #4caf50; }
        }
        .meta { font-size: 11px; color: var(--secondary-text-color, #9fb1c3); }
        .stats {
          display: flex; gap: 12px; margin-bottom: 8px; flex-wrap: wrap;
        }
        .stat {
          background: rgba(74, 163, 223, 0.08);
          padding: 4px 10px; border-radius: 12px; font-size: 11px;
          border: 1px solid rgba(74, 163, 223, 0.15);
        }
        .stat b { color: #4aa3df; }
        svg {
          width: 100%; height: auto;
          background: #0b121a; border: 1px solid #263343; border-radius: 8px;
        }
        .edge-line { transition: stroke-opacity 0.3s, stroke-width 0.3s; }
        .node-g { cursor: pointer; }
        .node-g:hover .node-circle { filter: brightness(1.4); }
        .node-label { pointer-events: none; user-select: none; }
        /* Pulsing glow for active nodes */
        @keyframes pulseGlow {
          0%, 100% { r: var(--base-r); opacity: 0; }
          50% { r: calc(var(--base-r) + 6px); opacity: 0.35; }
        }
        .glow-ring {
          animation: pulseGlow 3s ease-in-out infinite;
          fill: none; pointer-events: none;
        }
        /* Synaptic flow animation on edges */
        @keyframes synapticFlow {
          0% { stroke-dashoffset: 20; }
          100% { stroke-dashoffset: 0; }
        }
        .edge-flow {
          stroke-dasharray: 4 16;
          animation: synapticFlow 2s linear infinite;
        }
        .cross-dep { stroke-dasharray: 3 6; }
        /* Legend */
        .legend {
          display: flex; flex-wrap: wrap; gap: 6px; margin-top: 8px;
          font-size: 10px; color: var(--secondary-text-color, #8ba3b8);
        }
        .legend-item { display: flex; align-items: center; gap: 3px; }
        .legend-dot {
          width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0;
        }
        .tooltip-panel {
          position: absolute; top: 8px; right: 8px; max-width: 200px;
          background: rgba(15, 23, 32, 0.95); border: 1px solid #263343;
          border-radius: 8px; padding: 10px; font-size: 11px; display: none;
          z-index: 10; pointer-events: none;
        }
        .tooltip-panel.visible { display: block; }
        .tooltip-panel .tp-title { font-weight: 600; margin-bottom: 4px; }
        .tooltip-panel .tp-row { display: flex; justify-content: space-between; color: #8ba3b8; padding: 1px 0; }
        .tooltip-panel .tp-val { color: #e6eef6; }
        .graph-wrap { position: relative; }
      </style>
      <ha-card>
        <div class="card">
          <div class="header">
            <span class="title"><span class="pulse-dot"></span>Brain Graph</span>
            <span class="meta">${nodeCount} nodes · ${edgeCount} edges</span>
          </div>
          <div class="stats">
            <span class="stat"><b>${nodeCount}</b> Neuronen</span>
            <span class="stat"><b>${edgeCount}</b> Synapsen</span>
            <span class="stat"><b>${crossDeps}</b> Cross-Deps</span>
          </div>
          <div class="graph-wrap">
            <svg id="brain-svg" viewBox="0 0 ${w} ${h}" role="img" aria-label="Living brain graph">
              <defs>
                <radialGradient id="bg-grad" cx="50%" cy="50%" r="55%">
                  <stop offset="0%" stop-color="#101820"/>
                  <stop offset="100%" stop-color="#080c12"/>
                </radialGradient>
                <filter id="glow">
                  <feGaussianBlur stdDeviation="3" result="blur"/>
                  <feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>
                </filter>
              </defs>
              <rect x="0" y="0" width="${w}" height="${h}" fill="url(#bg-grad)"/>
              <g class="edges-layer"></g>
              <g class="nodes-layer"></g>
            </svg>
            <div class="tooltip-panel" id="tp"></div>
          </div>
          <div class="legend" id="legend-container"></div>
        </div>
      </ha-card>`;

    this._svgEl = this.shadowRoot.querySelector("#brain-svg");
    const edgesLayer = this._svgEl.querySelector(".edges-layer");
    const nodesLayer = this._svgEl.querySelector(".nodes-layer");
    const tooltipPanel = this.shadowRoot.querySelector("#tp");

    // Draw edges with synaptic flow
    this._edges.slice(0, 300).forEach((e, ei) => {
      const src = idMap[e.from || e.source_id];
      const tgt = idMap[e.to || e.target_id];
      if (!src || !tgt) return;

      const isCross = src._group !== tgt._group;
      const weight = Math.max(0.3, Math.min(1, e.weight || 0.5));

      // Base edge
      const line = document.createElementNS("http://www.w3.org/2000/svg", "line");
      line.setAttribute("x1", src.x.toFixed(1));
      line.setAttribute("y1", src.y.toFixed(1));
      line.setAttribute("x2", tgt.x.toFixed(1));
      line.setAttribute("y2", tgt.y.toFixed(1));
      line.setAttribute("stroke", isCross ? "#5a7a9a" : "#3a5060");
      line.setAttribute("stroke-opacity", (0.15 + weight * 0.25).toFixed(2));
      line.setAttribute("stroke-width", (0.5 + weight * 1.5).toFixed(1));
      line.classList.add("edge-line");
      if (isCross) line.classList.add("cross-dep");
      line.dataset.from = src._nid;
      line.dataset.to = tgt._nid;
      edgesLayer.appendChild(line);

      // Synaptic flow overlay (animated)
      if (weight > 0.5 || isCross) {
        const flow = document.createElementNS("http://www.w3.org/2000/svg", "line");
        flow.setAttribute("x1", src.x.toFixed(1));
        flow.setAttribute("y1", src.y.toFixed(1));
        flow.setAttribute("x2", tgt.x.toFixed(1));
        flow.setAttribute("y2", tgt.y.toFixed(1));
        flow.setAttribute("stroke", isCross ? "#88ccff" : "#4aa3df");
        flow.setAttribute("stroke-opacity", "0.25");
        flow.setAttribute("stroke-width", "1.5");
        flow.classList.add("edge-flow");
        flow.style.animationDelay = `${(ei * 0.1) % 2}s`;
        edgesLayer.appendChild(flow);
      }
    });

    // Draw nodes with pulsing glow
    const usedDomains = new Set();
    positioned.forEach((n, ni) => {
      const nid = n.id || n.node_id || `n${ni}`;
      const score = Math.max(0, Math.min(1, n.score || 0.5));
      const baseR = 3.5 + 8 * score;
      const fill = this._neuralColor(n);
      const domain = (n.domain || "default").split(".")[0];
      usedDomains.add(domain);
      const label = (n.label || n.name || n.id || "").substring(0, 22);

      const g = document.createElementNS("http://www.w3.org/2000/svg", "g");
      g.classList.add("node-g");
      g.dataset.nid = nid;

      // Glow ring (pulsing)
      if (score > 0.3) {
        const glow = document.createElementNS("http://www.w3.org/2000/svg", "circle");
        glow.setAttribute("cx", n.x.toFixed(1));
        glow.setAttribute("cy", n.y.toFixed(1));
        glow.setAttribute("r", (baseR + 5).toFixed(1));
        glow.setAttribute("stroke", fill);
        glow.setAttribute("stroke-width", "2");
        glow.classList.add("glow-ring");
        glow.style.setProperty("--base-r", `${baseR}px`);
        glow.style.animationDelay = `${(ni * 0.2) % 3}s`;
        g.appendChild(glow);
      }

      // Main node circle
      const circle = document.createElementNS("http://www.w3.org/2000/svg", "circle");
      circle.setAttribute("cx", n.x.toFixed(1));
      circle.setAttribute("cy", n.y.toFixed(1));
      circle.setAttribute("r", baseR.toFixed(1));
      circle.setAttribute("fill", fill);
      circle.setAttribute("fill-opacity", (0.35 + 0.65 * score).toFixed(2));
      circle.setAttribute("stroke", fill);
      circle.setAttribute("stroke-opacity", "0.6");
      circle.setAttribute("stroke-width", "1");
      circle.classList.add("node-circle");
      g.appendChild(circle);

      // Label for high-score or sparse graphs
      if (positioned.length <= 50 || score > 0.6) {
        const text = document.createElementNS("http://www.w3.org/2000/svg", "text");
        text.setAttribute("x", (n.x + baseR + 3).toFixed(1));
        text.setAttribute("y", (n.y + 3).toFixed(1));
        text.setAttribute("font-size", "9");
        text.setAttribute("fill", "#aab8c5");
        text.setAttribute("fill-opacity", "0.75");
        text.setAttribute("font-family", "system-ui,sans-serif");
        text.classList.add("node-label");
        text.textContent = label;
        g.appendChild(text);
      }

      // Hover interactions
      g.addEventListener("mouseenter", () => {
        this._hoveredNode = nid;
        // Highlight cross-dependencies
        const connected = this._getConnectedNodes(nid);
        edgesLayer.querySelectorAll(".edge-line").forEach((el) => {
          if (el.dataset.from === nid || el.dataset.to === nid) {
            el.setAttribute("stroke-opacity", "0.8");
            el.setAttribute("stroke-width", "2.5");
            el.setAttribute("stroke", "#88ccff");
          } else {
            el.setAttribute("stroke-opacity", "0.05");
          }
        });
        nodesLayer.querySelectorAll(".node-g").forEach((ng) => {
          if (ng.dataset.nid !== nid && !connected.has(ng.dataset.nid)) {
            ng.style.opacity = "0.2";
          }
        });
        // Tooltip
        tooltipPanel.classList.add("visible");
        tooltipPanel.innerHTML = `
          <div class="tp-title">${label}</div>
          <div class="tp-row"><span>Domain</span><span class="tp-val">${domain}</span></div>
          <div class="tp-row"><span>Score</span><span class="tp-val">${(score * 100).toFixed(0)}%</span></div>
          <div class="tp-row"><span>Connections</span><span class="tp-val">${connected.size}</span></div>
          ${n.zone ? `<div class="tp-row"><span>Zone</span><span class="tp-val">${n.zone}</span></div>` : ""}
          ${n.layer || n.neural_layer ? `<div class="tp-row"><span>Layer</span><span class="tp-val">${n.layer || n.neural_layer}</span></div>` : ""}
        `;
      });

      g.addEventListener("mouseleave", () => {
        this._hoveredNode = null;
        edgesLayer.querySelectorAll(".edge-line").forEach((el) => {
          const isCross = el.classList.contains("cross-dep");
          el.setAttribute("stroke", isCross ? "#5a7a9a" : "#3a5060");
          el.setAttribute("stroke-opacity", el._origOpacity || "0.25");
          el.setAttribute("stroke-width", el._origWidth || "1");
        });
        nodesLayer.querySelectorAll(".node-g").forEach((ng) => {
          ng.style.opacity = "1";
        });
        tooltipPanel.classList.remove("visible");
      });

      nodesLayer.appendChild(g);
    });

    // Build legend
    const legendEl = this.shadowRoot.querySelector("#legend-container");
    if (legendEl) {
      let legendHtml = "";
      usedDomains.forEach((d) => {
        const c = DOMAIN_COLORS[d] || DOMAIN_COLORS.default;
        legendHtml += `<span class="legend-item"><span class="legend-dot" style="background:${c}"></span>${d}</span>`;
      });
      legendEl.innerHTML = legendHtml;
    }

    // Start breathing animation
    this._startAnimation();
  }

  _startAnimation() {
    if (this._animFrame) cancelAnimationFrame(this._animFrame);

    const animate = () => {
      this._phase += 0.015;
      if (this._svgEl) {
        // Subtle breathing transform on the whole graph
        const breathe = 1 + Math.sin(this._phase) * 0.008;
        const nodesLayer = this._svgEl.querySelector(".nodes-layer");
        const edgesLayer = this._svgEl.querySelector(".edges-layer");
        if (nodesLayer) {
          nodesLayer.style.transform = `scale(${breathe.toFixed(4)})`;
          nodesLayer.style.transformOrigin = "center center";
        }
        if (edgesLayer) {
          edgesLayer.style.transform = `scale(${breathe.toFixed(4)})`;
          edgesLayer.style.transformOrigin = "center center";
        }
      }
      this._animFrame = requestAnimationFrame(animate);
    };
    this._animFrame = requestAnimationFrame(animate);
  }
}

customElements.define("styx-brain-card", StyxBrainCard);

window.customCards = window.customCards || [];
window.customCards.push({
  type: "styx-brain-card",
  name: "PilotSuite Living Brain Graph",
  description:
    "Living, pulsing brain graph with multi-colored neurons, synaptic flow animations, and neural cross-dependency highlighting.",
  preview: true,
});
