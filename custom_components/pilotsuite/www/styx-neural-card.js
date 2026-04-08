/**
 * PilotSuite Styx Neural Interface Card v1.0.0
 *
 * Combined Brain Visualization + Chat Interface.
 * Neurons and synapses light up when chat activity triggers neural changes.
 *
 * APIs:
 * - GET /api/v1/neurons/layers/visualization — Neuron layers + synapses
 * - POST /api/styx/chat — Send chat message
 * - GET /api/v1/conversation/history — Load chat history
 */

const NEURON_LABELS_DE = {
  presence: 'Praesenz', time_of_day: 'Tageszeit', light_level: 'Lichtstaerke',
  weather: 'Wetter', unifi_context: 'Netzwerk', temperature: 'Temperatur',
  energy_level: 'Energielevel', stress_index: 'Stressindex',
  routine_stability: 'Routine', sleep_debt: 'Schlafdefizit',
  attention_load: 'Aufmerksamkeit', comfort_index: 'Komfort',
  relax: 'Entspannung', focus: 'Fokus', active: 'Aktivitaet',
  sleep: 'Schlaf', away: 'Abwesend', alert: 'Alarm',
  social: 'Sozial', recovery: 'Erholung',
};

const LAYER_COLORS = { Context: '#2196F3', State: '#9C27B0', Mood: '#FF9800' };
const LAYER_LABELS_DE = { Context: 'Kontext', State: 'Zustand', Mood: 'Stimmung' };

const _NeuralBase = window.StyxCoreApiCard || HTMLElement;

class StyxNeuralCard extends _NeuralBase {
  constructor() {
    super();
    if (!this.shadowRoot) {
      this.attachShadow({ mode: 'open' });
      this._config = {};
      this._hass = null;
    }
    this._messages = [];
    this._loading = false;
    this._historyLoaded = false;
    this._layers = [];
    this._connections = [];
    this._neuronSnapshot = null;
    this._pipelineStatus = null;
    this._neuralLoaded = false;
  }

  static getConfigElement() {
    return document.createElement('hui-generic-entity-row');
  }

  static getStubConfig() {
    return {
      title: 'Neural Interface',
      max_messages: 50,
      show_history: true,
    };
  }

  setConfig(config) {
    this._config = {
      title: config.title || 'Neural Interface',
      max_messages: config.max_messages || 50,
      show_history: config.show_history !== false,
      core_url: config.core_url || '',
      ...config,
    };
  }

  set hass(hass) {
    this._hass = hass;
    if (!this._historyLoaded) {
      this._historyLoaded = true;
      this._render();
      this._fetchNeuralData();
      if (this._config.show_history) {
        this._loadHistory();
      }
    }
  }

  getCardSize() {
    return 8;
  }

  /* ── Core API helpers (fallback if base not loaded) ── */

  _getCoreUrl() {
    if (super._getCoreUrl) return super._getCoreUrl();
    if (this._config.core_url) return this._config.core_url;
    if (this._hass) {
      const s = this._hass.states['sensor.copilot_ha_core_api_v1'] ||
                this._hass.states['sensor.pilotsuite_core_api_v1'];
      if (s && s.attributes && s.attributes.base_url) return s.attributes.base_url;
    }
    return 'http://homeassistant.local:8909';
  }

  _getToken() {
    if (super._getToken) return super._getToken();
    if (this._config.auth_token) return this._config.auth_token;
    if (this._hass && this._hass.auth && this._hass.auth.data) {
      return this._hass.auth.data.access_token || '';
    }
    return '';
  }

  _esc(s) {
    if (typeof window.styxEsc === 'function') return window.styxEsc(s);
    const el = document.createElement('span');
    el.textContent = s;
    return el.innerHTML;
  }

  /* ── Neural Data ── */

  async _fetchNeuralData() {
    const url = this._getCoreUrl();
    const ctrl = new AbortController();
    const timer = setTimeout(() => ctrl.abort(), 12000);
    try {
      const resp = await fetch(`${url}/api/v1/neurons/layers/visualization`, {
        headers: { 'X-Auth-Token': this._getToken() },
        signal: ctrl.signal,
      });
      clearTimeout(timer);
      if (resp.ok) {
        const data = await resp.json();
        this._layers = data.layers || [];
        this._connections = data.connections || [];
        this._pipelineStatus = data.pipeline_status || null;
        this._neuralLoaded = true;
        this._renderNeuralViz();
      }
    } catch (e) {
      clearTimeout(timer);
    }
  }

  _snapshotNeurons() {
    const snap = new Map();
    for (const layer of this._layers) {
      for (const n of layer.neurons || []) {
        snap.set(n.id, { value: n.value, active: n.active });
      }
    }
    return snap;
  }

  async _fetchAndAnimateNeurons() {
    const s0 = this._snapshotNeurons();
    await this._fetchNeuralData();
    const s1 = this._snapshotNeurons();

    const changed = [];
    for (const [id, after] of s1) {
      const before = s0.get(id);
      if (!before || Math.abs(after.value - before.value) > 0.05) {
        changed.push(id);
      }
    }

    if (changed.length > 0) {
      this._animateNeuronChanges(changed);
    }
    return changed;
  }

  _animateNeuronChanges(neuronIds) {
    const svg = this.shadowRoot.querySelector('#neural-svg');
    if (!svg) return;

    const idSet = new Set(neuronIds);

    // Fire neurons
    svg.querySelectorAll('.neuron-g').forEach(g => {
      if (idSet.has(g.dataset.nid)) {
        g.classList.add('neuron-firing');
        setTimeout(() => g.classList.remove('neuron-firing'), 2500);
      }
    });

    // Activate connected synapses
    svg.querySelectorAll('.synapse-line').forEach(line => {
      if (idSet.has(line.dataset.from) || idSet.has(line.dataset.to)) {
        line.classList.add('synapse-active');
        setTimeout(() => line.classList.remove('synapse-active'), 2500);
      }
    });
  }

  /* ── Neural SVG Rendering ── */

  _renderNeuralViz() {
    const container = this.shadowRoot.querySelector('.neural-viz');
    if (!container || !this._layers.length) return;

    const w = 520, h = 240;
    const layerCount = this._layers.length || 3;
    const bandW = w / layerCount;

    let svgContent = `
      <svg id="neural-svg" viewBox="0 0 ${w} ${h}" role="img"
           aria-label="Neuronales Netzwerk Visualisierung">
        <title>Neural Interface: Neuronen und Synapsen</title>
        <defs>
          <radialGradient id="nbg" cx="50%" cy="50%" r="55%">
            <stop offset="0%" stop-color="#101820"/>
            <stop offset="100%" stop-color="#080c12"/>
          </radialGradient>
          <filter id="nglow">
            <feGaussianBlur stdDeviation="4" result="b"/>
            <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
          </filter>
        </defs>
        <rect x="0" y="0" width="${w}" height="${h}" fill="url(#nbg)"/>`;

    // Layer bands (subtle background zones)
    this._layers.forEach((layer, li) => {
      const x = li * bandW;
      const color = LAYER_COLORS[layer.name] || '#4fc3f7';
      const label = LAYER_LABELS_DE[layer.name] || layer.name;
      svgContent += `
        <rect x="${x}" y="0" width="${bandW}" height="${h}"
              fill="${color}" fill-opacity="0.04"/>
        <text x="${x + bandW / 2}" y="18" text-anchor="middle"
              fill="${color}" fill-opacity="0.6" font-size="11"
              font-family="system-ui,sans-serif" font-weight="600">${label}</text>`;
    });

    // Position neurons within their bands
    const neuronPositions = new Map();
    this._layers.forEach((layer, li) => {
      const neurons = layer.neurons || [];
      const bx = li * bandW + bandW / 2;
      const count = neurons.length;
      neurons.forEach((n, ni) => {
        const ny = 36 + ((h - 52) * (ni + 0.5)) / Math.max(1, count);
        const nx = bx + (Math.sin(ni * 2.7) * bandW * 0.25);
        neuronPositions.set(n.id, { x: nx, y: ny, neuron: n, layerName: layer.name });
      });
    });

    // Draw synapses
    svgContent += '<g class="synapses-layer">';
    for (const conn of this._connections) {
      const src = neuronPositions.get(conn.from);
      const tgt = neuronPositions.get(conn.to);
      if (!src || !tgt) continue;

      const strength = Math.abs(conn.signal_strength || 0);
      const excitatory = conn.excitatory !== false;
      const strokeColor = excitatory ? 'rgba(79,195,247,0.5)' : 'rgba(239,83,80,0.4)';
      const strokeW = 0.6 + strength * 2.5;
      const opacity = 0.15 + strength * 0.5;

      svgContent += `
        <line class="synapse-line" data-from="${conn.from}" data-to="${conn.to}"
              x1="${src.x.toFixed(1)}" y1="${src.y.toFixed(1)}"
              x2="${tgt.x.toFixed(1)}" y2="${tgt.y.toFixed(1)}"
              stroke="${strokeColor}" stroke-width="${strokeW.toFixed(1)}"
              stroke-opacity="${opacity.toFixed(2)}"/>`;
    }
    svgContent += '</g>';

    // Draw neurons
    svgContent += '<g class="neurons-layer">';
    for (const [nid, pos] of neuronPositions) {
      const n = pos.neuron;
      const val = Math.max(0, Math.min(1, n.value || 0));
      const r = 5 + 12 * val;
      const color = LAYER_COLORS[pos.layerName] || '#4fc3f7';
      const fillOpacity = 0.3 + 0.7 * val;
      const label = NEURON_LABELS_DE[n.name] || n.name;

      svgContent += `
        <g class="neuron-g" data-nid="${nid}">
          <circle class="neuron-glow" cx="${pos.x.toFixed(1)}" cy="${pos.y.toFixed(1)}"
                  r="${(r + 6).toFixed(1)}" fill="none"
                  stroke="${color}" stroke-width="1.5" stroke-opacity="0"/>
          <circle class="neuron-circle" cx="${pos.x.toFixed(1)}" cy="${pos.y.toFixed(1)}"
                  r="${r.toFixed(1)}" fill="${color}"
                  fill-opacity="${fillOpacity.toFixed(2)}"
                  stroke="${color}" stroke-opacity="0.5" stroke-width="0.8"/>
          <text x="${pos.x.toFixed(1)}" y="${(pos.y + r + 12).toFixed(1)}"
                text-anchor="middle" fill="${color}" fill-opacity="0.7"
                font-size="8" font-family="system-ui,sans-serif">${this._esc(label)}</text>
        </g>`;
    }
    svgContent += '</g>';

    svgContent += '</svg>';

    // Pipeline status badge
    let statusHtml = '';
    if (this._pipelineStatus) {
      const mood = this._pipelineStatus.dominant_mood;
      const conf = this._pipelineStatus.mood_confidence;
      if (mood) {
        const moodLabel = NEURON_LABELS_DE[mood] || mood;
        statusHtml = `<div class="pipeline-status">
          <span class="status-dot"></span>
          ${this._esc(moodLabel)} (${Math.round((conf || 0) * 100)}%)
        </div>`;
      }
    }

    container.innerHTML = svgContent + statusHtml;
  }

  /* ── Chat History ── */

  async _loadHistory() {
    const url = this._getCoreUrl();
    const ctrl = new AbortController();
    const timer = setTimeout(() => ctrl.abort(), 10000);
    try {
      const resp = await fetch(`${url}/api/v1/conversation/history?limit=${this._config.max_messages}`, {
        headers: { 'X-Auth-Token': this._getToken() },
        signal: ctrl.signal,
      });
      clearTimeout(timer);
      if (resp.ok) {
        const data = await resp.json();
        if (data.ok && data.messages) {
          this._messages = data.messages.reverse().map(m => ({
            role: m.role,
            content: m.content,
            timestamp: m.timestamp
              ? new Date(m.timestamp).toLocaleTimeString('de-DE', { hour: '2-digit', minute: '2-digit' })
              : '',
            topics: m.topics,
          }));
          this._renderMessages();
        }
      }
    } catch (e) {
      clearTimeout(timer);
    }
  }

  /* ── Chat Send ── */

  async _sendMessage(text) {
    if (!text.trim() || this._loading) return;

    this._messages.push({
      role: 'user',
      content: text,
      timestamp: new Date().toLocaleTimeString('de-DE', { hour: '2-digit', minute: '2-digit' }),
    });
    this._renderMessages();
    this._loading = true;
    this._renderTypingIndicator(true);

    // Snapshot neurons before chat
    const preSnapshot = this._snapshotNeurons();

    const url = this._getCoreUrl();
    const ctrl = new AbortController();
    const timer = setTimeout(() => ctrl.abort(), 30000);
    let changedNeurons = [];

    try {
      const resp = await fetch(`${url}/api/styx/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Auth-Token': this._getToken(),
        },
        body: JSON.stringify({ query: text }),
        signal: ctrl.signal,
      });
      clearTimeout(timer);

      if (resp.ok) {
        const data = await resp.json();

        // Fetch updated neurons and animate changes
        changedNeurons = await this._fetchAndAnimateNeurons();

        this._messages.push({
          role: 'assistant',
          content: data.response || data.message || 'Keine Antwort.',
          timestamp: new Date().toLocaleTimeString('de-DE', { hour: '2-digit', minute: '2-digit' }),
          sources: data.sources,
          query_type: data.query_type,
          neurons: changedNeurons,
        });
      } else {
        this._messages.push({
          role: 'system',
          content: `Fehler: ${resp.status} ${resp.statusText}`,
          timestamp: new Date().toLocaleTimeString('de-DE', { hour: '2-digit', minute: '2-digit' }),
        });
      }
    } catch (e) {
      clearTimeout(timer);
      this._messages.push({
        role: 'system',
        content: e.name === 'AbortError' ? 'Zeitüberschreitung (30s).' : `Verbindungsfehler: ${e.message}`,
        timestamp: new Date().toLocaleTimeString('de-DE', { hour: '2-digit', minute: '2-digit' }),
      });
    }

    this._loading = false;
    this._renderTypingIndicator(false);
    this._renderMessages();
  }

  /* ── Message Rendering ── */

  _renderTypingIndicator(show) {
    const indicator = this.shadowRoot.querySelector('.typing-indicator');
    if (indicator) indicator.style.display = show ? 'flex' : 'none';
  }

  _renderMessages() {
    const container = this.shadowRoot.querySelector('.messages');
    if (!container) return;

    const msgs = this._messages.slice(-this._config.max_messages);
    container.innerHTML = msgs.map(m => {
      const cls = m.role === 'user' ? 'msg-user' : m.role === 'assistant' ? 'msg-assistant' : 'msg-system';
      const label = m.role === 'user' ? 'Du' : m.role === 'assistant' ? 'Styx' : 'System';
      const neuronBadge = m.neurons && m.neurons.length
        ? `<div class="neuron-badge">${m.neurons.map(nid => {
            const name = nid.split('.').pop();
            return this._esc(NEURON_LABELS_DE[name] || name);
          }).join(', ')}</div>`
        : '';
      return `
        <div class="msg ${cls}">
          <div class="msg-header">
            <span class="msg-role">${label}</span>
            <span class="msg-time">${this._esc(m.timestamp || '')}</span>
          </div>
          <div class="msg-content">${this._esc(m.content)}</div>
          ${neuronBadge}
          ${m.sources ? `<div class="msg-meta">${m.sources.length} Quelle(n) | ${m.query_type || ''}</div>` : ''}
        </div>`;
    }).join('');

    container.scrollTop = container.scrollHeight;
  }

  /* ── Main Render ── */

  _render() {
    const designTokens = typeof this._designTokens === 'function' ? this._designTokens() : '';
    this.shadowRoot.innerHTML = `
      <style>
        ${designTokens}
        :host {
          display: block;
          --ps-accent: var(--accent-color, #4fc3f7);
          --ps-bg: var(--card-background-color, var(--ha-card-background, #1a1a2e));
          --ps-surface: var(--secondary-background-color, #222240);
          --ps-text: var(--primary-text-color, #e0e0f0);
          --ps-text-secondary: var(--secondary-text-color, #9e9eb8);
          --ps-radius: var(--ha-card-border-radius, 12px);
          --ps-transition: 0.2s ease;
        }
        .card {
          background: var(--ps-bg);
          border-radius: var(--ps-radius);
          padding: 16px;
          color: var(--ps-text);
          font-family: var(--paper-font-body1_-_font-family, system-ui, sans-serif);
          display: flex;
          flex-direction: column;
          height: min(640px, 80vh);
        }

        /* ── Header ── */
        .header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 8px;
          flex-shrink: 0;
        }
        .title { font-size: 0.9375rem; font-weight: 600; }
        .pulse-dot {
          display: inline-block; width: 8px; height: 8px; border-radius: 50%;
          background: #81c784; margin-right: 6px; vertical-align: middle;
          animation: pulseDot 2s ease-in-out infinite;
        }
        @keyframes pulseDot {
          0%, 100% { opacity: 1; box-shadow: 0 0 4px #81c784; }
          50% { opacity: 0.4; box-shadow: 0 0 12px #81c784; }
        }
        .header-meta {
          font-size: 0.75rem;
          color: var(--ps-text-secondary);
        }

        /* ── Neural Visualization ── */
        .neural-viz {
          flex-shrink: 0;
          margin-bottom: 8px;
        }
        .neural-viz svg {
          width: 100%;
          height: auto;
          border-radius: 8px;
          border: 1px solid rgba(255,255,255,0.06);
        }
        .pipeline-status {
          display: flex;
          align-items: center;
          gap: 6px;
          padding: 4px 0;
          font-size: 0.75rem;
          color: var(--ps-text-secondary);
        }
        .status-dot {
          width: 6px; height: 6px; border-radius: 50%;
          background: #FF9800;
          box-shadow: 0 0 6px rgba(255,152,0,0.4);
        }

        /* ── Neuron Animations ── */
        .neuron-g { transition: opacity 0.3s; }
        .neuron-glow { transition: stroke-opacity 0.4s; }
        .neuron-circle { transition: fill-opacity 0.3s, r 0.3s; }
        .synapse-line { transition: stroke-opacity 0.4s, stroke-width 0.3s; }

        .neuron-firing .neuron-circle {
          animation: neuronPulse 0.8s ease-in-out 3;
        }
        .neuron-firing .neuron-glow {
          stroke-opacity: 0.6 !important;
          animation: glowPulse 0.8s ease-in-out 3;
        }
        @keyframes neuronPulse {
          0%, 100% { filter: none; }
          50% { filter: brightness(1.8) drop-shadow(0 0 8px currentColor); }
        }
        @keyframes glowPulse {
          0%, 100% { stroke-opacity: 0.2; }
          50% { stroke-opacity: 0.8; }
        }

        .synapse-active {
          stroke-opacity: 0.9 !important;
          stroke-width: 2.5 !important;
          stroke-dasharray: 4 8;
          animation: synapseFlow 0.6s linear infinite;
        }
        @keyframes synapseFlow {
          0% { stroke-dashoffset: 12; }
          100% { stroke-dashoffset: 0; }
        }

        /* Subtle idle breathing on layer groups */
        .neurons-layer, .synapses-layer {
          animation: layerBreathe 6s ease-in-out infinite;
          transform-origin: center center;
        }
        @keyframes layerBreathe {
          0%, 100% { transform: scale(1); }
          50% { transform: scale(1.006); }
        }

        /* ── Chat Section ── */
        .chat-divider {
          height: 1px;
          background: linear-gradient(90deg, transparent, rgba(79,195,247,0.2), transparent);
          margin: 4px 0 8px;
          flex-shrink: 0;
        }
        .messages {
          flex: 1;
          overflow-y: auto;
          padding: 4px 0;
          scroll-behavior: smooth;
          min-height: 80px;
        }
        .messages::-webkit-scrollbar { width: 4px; }
        .messages::-webkit-scrollbar-thumb {
          background: rgba(255,255,255,0.15);
          border-radius: 2px;
        }
        .msg {
          margin-bottom: 8px;
          padding: 8px 12px;
          border-radius: 12px;
          max-width: 85%;
          word-wrap: break-word;
          transition: opacity var(--ps-transition);
        }
        .msg-user {
          background: linear-gradient(135deg, rgba(79,195,247,0.18), rgba(79,195,247,0.08));
          border: 1px solid rgba(79,195,247,0.3);
          margin-left: auto;
          border-bottom-right-radius: 4px;
        }
        .msg-assistant {
          background: rgba(255,255,255,0.06);
          border: 1px solid rgba(255,255,255,0.1);
          margin-right: auto;
          border-bottom-left-radius: 4px;
        }
        .msg-system {
          background: rgba(255,183,77,0.1);
          border: 1px solid rgba(255,183,77,0.2);
          margin: 0 auto;
          font-size: 0.8125rem;
          text-align: center;
        }
        .msg-header {
          display: flex;
          justify-content: space-between;
          margin-bottom: 4px;
        }
        .msg-role {
          font-size: 0.75rem;
          font-weight: 600;
          color: var(--ps-text-secondary);
        }
        .msg-time {
          font-size: 0.75rem;
          color: var(--ps-text-secondary);
          opacity: 0.7;
        }
        .msg-content {
          font-size: 0.875rem;
          line-height: 1.5;
          white-space: pre-wrap;
        }
        .msg-meta {
          font-size: 0.75rem;
          color: var(--ps-text-secondary);
          margin-top: 4px;
          opacity: 0.6;
        }
        .neuron-badge {
          display: inline-flex;
          align-items: center;
          gap: 4px;
          margin-top: 4px;
          padding: 2px 8px;
          border-radius: 10px;
          font-size: 0.6875rem;
          background: rgba(156,39,176,0.12);
          border: 1px solid rgba(156,39,176,0.25);
          color: #ce93d8;
        }

        /* ── Typing Indicator ── */
        .typing-indicator {
          display: none;
          align-items: center;
          gap: 4px;
          padding: 6px 12px;
          margin-bottom: 4px;
        }
        .typing-indicator span {
          display: inline-block;
          width: 6px; height: 6px; border-radius: 50%;
          background: var(--ps-accent);
          animation: bounce 1.4s infinite;
        }
        .typing-indicator span:nth-child(2) { animation-delay: 0.2s; }
        .typing-indicator span:nth-child(3) { animation-delay: 0.4s; }
        @keyframes bounce {
          0%, 80%, 100% { transform: scale(1); opacity: 0.4; }
          40% { transform: scale(1.3); opacity: 1; }
        }
        .typing-label {
          font-size: 0.8125rem;
          color: var(--ps-text-secondary);
          margin-left: 4px;
        }

        /* ── Input Area ── */
        .input-area {
          display: flex;
          gap: 8px;
          margin-top: 8px;
          flex-shrink: 0;
        }
        .input-area input {
          flex: 1;
          padding: 10px 14px;
          border-radius: 20px;
          border: 1px solid rgba(255,255,255,0.15);
          background: rgba(255,255,255,0.06);
          color: var(--ps-text);
          font-size: 0.875rem;
          outline: none;
          transition: border-color var(--ps-transition), box-shadow var(--ps-transition);
        }
        .input-area input:focus {
          border-color: var(--ps-accent);
          box-shadow: 0 0 0 2px rgba(79,195,247,0.15);
        }
        .input-area input::placeholder {
          color: var(--ps-text-secondary);
          opacity: 0.5;
        }
        .send-btn {
          padding: 8px 16px;
          border-radius: 20px;
          border: none;
          background: rgba(79,195,247,0.2);
          color: var(--ps-accent);
          cursor: pointer;
          font-size: 0.875rem;
          font-weight: 600;
          transition: background var(--ps-transition);
          flex-shrink: 0;
        }
        .send-btn:hover { background: rgba(79,195,247,0.35); }
        .send-btn:disabled { opacity: 0.4; cursor: not-allowed; }

        .empty {
          text-align: center;
          color: var(--ps-text-secondary);
          padding: 24px 0;
          font-size: 0.875rem;
        }

        /* ── Refresh Button ── */
        .refresh-btn {
          background: none;
          border: none;
          color: var(--ps-text-secondary);
          cursor: pointer;
          font-size: 0.8125rem;
          padding: 2px 6px;
          border-radius: 4px;
          transition: color var(--ps-transition);
        }
        .refresh-btn:hover { color: var(--ps-accent); }
      </style>
      <div class="card">
        <div class="header">
          <span class="title">
            <span class="pulse-dot"></span>
            ${this._esc(this._config.title)}
          </span>
          <span class="header-meta">
            <button class="refresh-btn" aria-label="Neuronennetz aktualisieren" title="Aktualisieren">&#x21bb;</button>
          </span>
        </div>
        <div class="neural-viz" role="region" aria-label="Neuronennetz-Visualisierung">
          <div class="empty">Neuronennetz wird geladen...</div>
        </div>
        <div class="chat-divider"></div>
        <div class="messages" role="log" aria-label="Chat-Verlauf">
          <div class="empty">Starte eine Unterhaltung mit Styx...</div>
        </div>
        <div class="typing-indicator">
          <span></span><span></span><span></span>
          <span class="typing-label">Styx denkt nach...</span>
        </div>
        <div class="input-area">
          <input type="text" placeholder="Nachricht eingeben..." aria-label="Chat-Nachricht" />
          <button class="send-btn" aria-label="Nachricht senden">Senden</button>
        </div>
      </div>`;

    // Event listeners
    const input = this.shadowRoot.querySelector('.input-area input');
    const btn = this.shadowRoot.querySelector('.send-btn');
    const refreshBtn = this.shadowRoot.querySelector('.refresh-btn');

    const send = () => {
      const text = input.value.trim();
      if (text) {
        this._sendMessage(text);
        input.value = '';
      }
    };

    btn.addEventListener('click', send);
    input.addEventListener('keydown', e => {
      if (e.key === 'Enter') send();
    });

    refreshBtn.addEventListener('click', () => {
      this._fetchNeuralData();
    });

    if (this._messages.length > 0) {
      this._renderMessages();
    }
  }
}

if (typeof registerStyxCard === 'function') {
  registerStyxCard('styx-neural-card', StyxNeuralCard, {
    name: 'PilotSuite Neural Interface',
    description: 'Kombiniertes Neuronennetz + Chat-Interface mit Aktivitaets-Visualisierung',
  });
} else {
  customElements.define('styx-neural-card', StyxNeuralCard);
  window.customCards = window.customCards || [];
  window.customCards.push({
    type: 'styx-neural-card',
    name: 'PilotSuite Neural Interface',
    description: 'Kombiniertes Neuronennetz + Chat-Interface mit Aktivitaets-Visualisierung',
  });
}
