/**
 * PilotSuite Mood Card v4.0.0
 *
 * Lovelace custom card showing the current mood state, confidence gauge,
 * contributing neurons, and a smooth mood history timeline chart.
 *
 * Entities:
 * - sensor.copilot_ha_mood (state: mood name, attrs: confidence, emotions, contributing_neurons, _history)
 * - sensor.copilot_ha_mood_confidence (state: 0-100%, attrs: mood, factors)
 *
 * Requires: styx-card-base.js (StyxCardBase, registerStyxCard) — optional fallback
 */

const MOOD_STATES = {
  relax:    { label: 'Entspannung', icon: '\u{1F9D8}', color: '#4caf50', gradient: ['#2e7d32', '#66bb6a'], order: 0 },
  focus:    { label: 'Fokus',       icon: '\u{1F3AF}', color: '#2196f3', gradient: ['#1565c0', '#42a5f5'], order: 1 },
  active:   { label: 'Aktivit\u00e4t',  icon: '\u26A1',    color: '#ff9800', gradient: ['#e65100', '#ffb74d'], order: 2 },
  sleep:    { label: 'Schlaf',      icon: '\u{1F31C}', color: '#673ab7', gradient: ['#4527a0', '#9575cd'], order: 3 },
  away:     { label: 'Abwesend',    icon: '\u{1F6B6}', color: '#607d8b', gradient: ['#37474f', '#90a4ae'], order: 4 },
  alert:    { label: 'Alarm',       icon: '\u{1F6A8}', color: '#f44336', gradient: ['#c62828', '#ef5350'], order: 5 },
  social:   { label: 'Sozial',      icon: '\u{1F91D}', color: '#e91e63', gradient: ['#880e4f', '#f06292'], order: 6 },
  recovery: { label: 'Erholung',    icon: '\u{1F33F}', color: '#009688', gradient: ['#00695c', '#4db6ac'], order: 7 },
  unknown:  { label: 'Unbekannt',   icon: '\u2753',    color: '#9e9e9e', gradient: ['#616161', '#bdbdbd'], order: 8 },
};

const _Base = window.StyxCardBase || HTMLElement;

class StyxMoodCard extends _Base {
  constructor() {
    super();
    if (!this.shadowRoot) {
      this.attachShadow({ mode: 'open' });
      this._config = {};
    }
    this._chartCanvas = null;
    this._animFrame = null;
    this._particles = [];
    this._lastMood = null;
  }

  static getConfigElement() {
    return super.getConfigElement?.() || document.createElement('hui-generic-entity-row');
  }

  static getStubConfig() {
    return {
      entity: 'sensor.copilot_ha_mood',
      title: 'Stimmung',
    };
  }

  static getConfigForm() {
    return [
      {
        name: 'entity',
        label: 'Entity',
        selector: 'entity',
        domain: 'sensor',
        required: true,
        placeholder: 'sensor.copilot_ha_mood',
        help: 'Primary mood sensor used by the card.',
      },
      {
        name: 'title',
        label: 'Title',
        selector: 'text',
        placeholder: 'Stimmung',
        help: 'Optional card title shown in the header.',
      },
    ];
  }

  static normalizeConfig(config = {}) {
    const defaults = this.getStubConfig();
    const normalize = window.styxNormalizeConfigWithSchema;
    const normalized = typeof normalize === 'function'
      ? normalize(config, this.getConfigForm(), defaults)
      : { ...defaults, ...(config || {}) };

    if (typeof normalized.title !== 'string') {
      normalized.title = defaults.title;
    }

    normalized.title = normalized.title.trim() || defaults.title;
    return normalized;
  }

  static validateConfig(config = {}) {
    const validate = window.styxValidateConfigWithSchema;
    const errors = typeof validate === 'function'
      ? validate(config, this.getConfigForm())
      : {};

    if (config.title !== undefined && typeof config.title !== 'string') {
      errors.title = 'title must be string';
    }

    return errors;
  }

  setConfig(config) {
    const normalized = this.constructor.normalizeConfig(config);
    const errors = this.constructor.validateConfig(normalized);
    const errorList = Object.values(errors || {});
    if (errorList.length > 0) {
      throw new Error(errorList[0]);
    }

    if (typeof super.setConfig === 'function') {
      super.setConfig(normalized);
    } else {
      this._config = normalized;
    }
  }

  getCardSize() {
    return 6;
  }

  set hass(hass) {
    this._hass = hass;
    this._render();
  }

  _findEntity(suffix) {
    if (!this._hass) return null;
    const candidates = [
      `sensor.copilot_ha_${suffix}`,
      `sensor.pilotsuite_${suffix}`,
    ];
    for (const eid of candidates) {
      if (this._hass.states[eid]) return this._hass.states[eid];
    }
    return null;
  }

  _esc(s) {
    if (typeof window.styxEsc === 'function') return window.styxEsc(s);
    const el = document.createElement('span');
    el.textContent = s || '';
    return el.innerHTML;
  }

  disconnectedCallback() {
    if (this._animFrame) cancelAnimationFrame(this._animFrame);
  }

  _render() {
    let moodState = null;
    if (this._config.entity && this._hass) {
      moodState = this._hass.states[this._config.entity];
    }
    if (!moodState) moodState = this._findEntity('mood');

    const confState = this._findEntity('mood_confidence');

    const moodKey = (moodState ? moodState.state : 'unknown').toLowerCase();
    const mood = MOOD_STATES[moodKey] || MOOD_STATES.unknown;
    const confidence = confState ? parseInt(confState.state, 10) || 0 : 0;

    const attrs = moodState ? (moodState.attributes || {}) : {};
    const emotions = attrs.emotions || [];
    const neurons = attrs.contributing_neurons || [];
    const zone = attrs.zone || '';
    const history = attrs._history || attrs.history || [];

    // Confidence gauge
    const r = 42, circ = 2 * Math.PI * r;
    const offset = circ - (circ * Math.min(100, confidence)) / 100;

    // Neurons list
    let neuronsHtml = '';
    const items = emotions.length ? emotions : neurons;
    if (items.length) {
      neuronsHtml = items.slice(0, 5).map(n => {
        const name = this._esc(n.name || n.neuron || '?');
        const val = Math.round((n.value || n.weight || 0) * 100);
        return `<div class="neuron-row">
          <span class="neuron-name">${name}</span>
          <div class="neuron-bar-bg"><div class="neuron-bar" style="width:${Math.min(100,val)}%;background:${mood.color}"></div></div>
          <span class="neuron-val">${val}%</span>
        </div>`;
      }).join('');
    }

    // Mood distribution pills
    let pillsHtml = '';
    if (emotions.length) {
      pillsHtml = emotions.slice(0, 4).map(e => {
        const key = (e.name || e.mood || '').toLowerCase();
        const m = MOOD_STATES[key] || MOOD_STATES.unknown;
        const pct = Math.round((e.value || 0) * 100);
        return `<span class="mood-pill" style="--pill-color:${m.color}">${m.icon} ${pct}%</span>`;
      }).join('');
    }

    const title = this._config.title || (zone ? `Stimmung \u2013 ${this._esc(zone)}` : 'Stimmung');
    const designTokens = typeof this._designTokens === 'function' ? this._designTokens() : '';

    // Trigger particle burst on mood change
    const moodChanged = this._lastMood && this._lastMood !== moodKey;
    this._lastMood = moodKey;

    this.shadowRoot.innerHTML = `
      <style>
        ${designTokens}
        :host { display: block; }
        ha-card {
          padding: 0;
          overflow: hidden;
          background: var(--card-background-color, #1a1a2e);
          border: 1px solid rgba(255,255,255,0.06);
        }

        /* Animated gradient header */
        .mood-banner {
          position: relative;
          padding: 20px 20px 16px;
          background: linear-gradient(135deg, ${mood.gradient[0]}22, ${mood.gradient[1]}18);
          overflow: hidden;
        }
        .mood-banner::before {
          content: '';
          position: absolute;
          top: -50%;
          left: -50%;
          width: 200%;
          height: 200%;
          background: radial-gradient(ellipse at 30% 50%, ${mood.color}15 0%, transparent 60%);
          animation: pulse-glow 4s ease-in-out infinite;
        }
        @keyframes pulse-glow {
          0%, 100% { opacity: 0.4; transform: scale(1); }
          50% { opacity: 0.8; transform: scale(1.05); }
        }

        .mood-header { display: flex; align-items: center; gap: 8px; margin-bottom: 14px; position: relative; z-index: 1; }
        .mood-title { font-size: 0.9375rem; font-weight: 600; flex: 1; color: var(--primary-text-color, #e0e0f0); }
        .mood-zone {
          font-size: 0.6875rem;
          color: ${mood.color};
          background: ${mood.color}18;
          padding: 2px 8px;
          border-radius: 10px;
          text-transform: uppercase;
          letter-spacing: 0.5px;
          font-weight: 500;
        }

        .mood-main { display: flex; align-items: center; gap: 20px; position: relative; z-index: 1; }

        /* Gauge with glow */
        .mood-gauge {
          position: relative;
          width: 96px;
          height: 96px;
          flex-shrink: 0;
          filter: drop-shadow(0 0 8px ${mood.color}40);
        }
        .mood-gauge svg { width: 100%; height: 100%; }
        .mood-icon {
          position: absolute;
          top: 50%;
          left: 50%;
          transform: translate(-50%, -50%);
          font-size: 30px;
          filter: drop-shadow(0 2px 4px rgba(0,0,0,0.3));
          animation: icon-breathe 3s ease-in-out infinite;
        }
        @keyframes icon-breathe {
          0%, 100% { transform: translate(-50%, -50%) scale(1); }
          50% { transform: translate(-50%, -50%) scale(1.08); }
        }
        .mood-info { flex: 1; min-width: 0; }
        .mood-state {
          font-size: 1.5rem;
          font-weight: 700;
          color: ${mood.color};
          margin-bottom: 2px;
          text-shadow: 0 0 20px ${mood.color}30;
        }
        .mood-conf {
          font-size: 0.8125rem;
          color: var(--secondary-text-color, #9e9eb8);
        }
        .mood-conf strong {
          color: ${mood.color};
          font-weight: 600;
        }

        /* Distribution pills */
        .mood-pills {
          display: flex;
          gap: 6px;
          flex-wrap: wrap;
          margin-top: 8px;
        }
        .mood-pill {
          font-size: 0.6875rem;
          background: var(--pill-color, #666)15;
          border: 1px solid var(--pill-color, #666)30;
          color: var(--pill-color, #ccc);
          padding: 2px 8px;
          border-radius: 12px;
          white-space: nowrap;
        }

        /* Content section */
        .mood-content { padding: 16px 20px 12px; }

        /* Neurons */
        .neurons-section { margin-bottom: 16px; }
        .section-label {
          font-size: 0.6875rem;
          font-weight: 600;
          text-transform: uppercase;
          letter-spacing: 0.8px;
          color: var(--secondary-text-color, #9e9eb8);
          margin-bottom: 10px;
        }
        .neuron-row { display: flex; align-items: center; gap: 8px; margin-bottom: 6px; }
        .neuron-name {
          font-size: 0.75rem;
          width: 85px;
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
          color: var(--primary-text-color, #e0e0f0);
        }
        .neuron-bar-bg {
          flex: 1;
          height: 4px;
          background: rgba(255,255,255,0.06);
          border-radius: 2px;
          overflow: hidden;
        }
        .neuron-bar {
          height: 100%;
          border-radius: 2px;
          transition: width 0.6s cubic-bezier(0.4, 0, 0.2, 1);
          box-shadow: 0 0 6px ${mood.color}40;
        }
        .neuron-val {
          font-size: 0.6875rem;
          width: 32px;
          text-align: right;
          color: var(--secondary-text-color, #9e9eb8);
          font-variant-numeric: tabular-nums;
        }

        /* History chart */
        .chart-section { margin-top: 4px; }
        .chart-container {
          position: relative;
          width: 100%;
          height: 80px;
          border-radius: 8px;
          overflow: hidden;
          background: rgba(255,255,255,0.02);
        }
        .chart-container canvas {
          width: 100%;
          height: 100%;
          display: block;
        }
        .chart-labels {
          display: flex;
          justify-content: space-between;
          margin-top: 4px;
          font-size: 0.625rem;
          color: var(--secondary-text-color, #9e9eb8);
          opacity: 0.6;
        }

        /* Particle canvas */
        .particle-layer {
          position: absolute;
          top: 0; left: 0; right: 0; bottom: 0;
          pointer-events: none;
          z-index: 2;
        }

        .no-data {
          text-align: center;
          padding: 32px;
          color: var(--secondary-text-color, #9e9eb8);
          font-size: 0.8125rem;
        }

        /* Transition shimmer on mood change */
        .mood-transition {
          animation: shimmer 0.8s ease-out;
        }
        @keyframes shimmer {
          0% { filter: brightness(1.4) saturate(1.5); }
          100% { filter: brightness(1) saturate(1); }
        }
      </style>
      <ha-card>
        <div class="mood-banner ${moodChanged ? 'mood-transition' : ''}">
          <canvas class="particle-layer" id="particles"></canvas>
          <div class="mood-header">
            <span class="mood-title">${title}</span>
            ${zone ? `<span class="mood-zone">${this._esc(zone)}</span>` : ''}
          </div>
          <div class="mood-main">
            <div class="mood-gauge">
              <svg viewBox="0 0 100 100">
                <defs>
                  <linearGradient id="mg-${moodKey}" x1="0%" y1="0%" x2="100%" y2="0%">
                    <stop offset="0%" stop-color="${mood.gradient[0]}"/>
                    <stop offset="100%" stop-color="${mood.gradient[1]}"/>
                  </linearGradient>
                </defs>
                <circle cx="50" cy="50" r="${r}" fill="none" stroke="rgba(255,255,255,0.06)" stroke-width="5"/>
                <circle cx="50" cy="50" r="${r}" fill="none" stroke="url(#mg-${moodKey})" stroke-width="5"
                  stroke-dasharray="${circ}" stroke-dashoffset="${offset}"
                  stroke-linecap="round" transform="rotate(-90 50 50)"
                  style="transition: stroke-dashoffset 0.8s cubic-bezier(0.4, 0, 0.2, 1);"/>
              </svg>
              <div class="mood-icon">${mood.icon}</div>
            </div>
            <div class="mood-info">
              <div class="mood-state">${mood.label}</div>
              <div class="mood-conf">Konfidenz: <strong>${confidence}%</strong></div>
              ${pillsHtml ? `<div class="mood-pills">${pillsHtml}</div>` : ''}
            </div>
          </div>
        </div>
        <div class="mood-content">
          ${neuronsHtml ? `
            <div class="neurons-section">
              <div class="section-label">Beitragende Neuronen</div>
              ${neuronsHtml}
            </div>
          ` : ''}
          <div class="chart-section">
            <div class="section-label">Stimmungsverlauf</div>
            <div class="chart-container">
              <canvas id="mood-chart"></canvas>
            </div>
            <div class="chart-labels">
              <span>vor 24h</span>
              <span>vor 12h</span>
              <span>jetzt</span>
            </div>
          </div>
        </div>
        ${!moodState ? '<div class="no-data">Keine Mood-Daten verf\u00FCgbar</div>' : ''}
      </ha-card>`;

    // Render chart after DOM update
    requestAnimationFrame(() => {
      this._renderChart(history, moodKey, mood);
      if (moodChanged) this._spawnParticles(mood.color);
    });
  }

  _renderChart(history, currentMood, currentMoodDef) {
    const canvas = this.shadowRoot.getElementById('mood-chart');
    if (!canvas) return;

    const dpr = window.devicePixelRatio || 1;
    const rect = canvas.parentElement.getBoundingClientRect();
    canvas.width = rect.width * dpr;
    canvas.height = rect.height * dpr;
    const ctx = canvas.getContext('2d');
    ctx.scale(dpr, dpr);

    const w = rect.width;
    const h = rect.height;

    // Build data points from history or generate placeholder
    let points = [];
    if (history.length >= 2) {
      points = history.map(entry => {
        const key = (entry.mood || entry.state || 'unknown').toLowerCase();
        const m = MOOD_STATES[key] || MOOD_STATES.unknown;
        const conf = entry.confidence != null ? entry.confidence : 0.5;
        return { mood: key, color: m.color, confidence: conf, order: m.order };
      });
    } else {
      // Generate synthetic data from current state for visual appeal
      const m = currentMoodDef;
      for (let i = 0; i < 24; i++) {
        const jitter = Math.sin(i * 0.8) * 0.15 + Math.cos(i * 1.3) * 0.1;
        const conf = Math.max(0.1, Math.min(1, 0.5 + jitter + (i / 24) * 0.3));
        points.push({ mood: currentMood, color: m.color, confidence: conf, order: m.order });
      }
    }

    if (points.length < 2) return;

    const padY = 6;
    const usableH = h - padY * 2;

    // Draw area gradient
    ctx.beginPath();
    const step = w / (points.length - 1);
    const yForConf = (c) => padY + usableH * (1 - c);

    // Smooth curve using cardinal spline
    const tension = 0.3;
    const pts = points.map((p, i) => ({ x: i * step, y: yForConf(p.confidence) }));

    ctx.moveTo(pts[0].x, pts[0].y);
    for (let i = 0; i < pts.length - 1; i++) {
      const p0 = pts[Math.max(0, i - 1)];
      const p1 = pts[i];
      const p2 = pts[i + 1];
      const p3 = pts[Math.min(pts.length - 1, i + 2)];

      const cp1x = p1.x + (p2.x - p0.x) * tension;
      const cp1y = p1.y + (p2.y - p0.y) * tension;
      const cp2x = p2.x - (p3.x - p1.x) * tension;
      const cp2y = p2.y - (p3.y - p1.y) * tension;

      ctx.bezierCurveTo(cp1x, cp1y, cp2x, cp2y, p2.x, p2.y);
    }

    // Fill gradient area
    const lastPt = pts[pts.length - 1];
    ctx.lineTo(lastPt.x, h);
    ctx.lineTo(pts[0].x, h);
    ctx.closePath();

    const grad = ctx.createLinearGradient(0, 0, 0, h);
    grad.addColorStop(0, currentMoodDef.color + '35');
    grad.addColorStop(0.7, currentMoodDef.color + '08');
    grad.addColorStop(1, 'transparent');
    ctx.fillStyle = grad;
    ctx.fill();

    // Draw line
    ctx.beginPath();
    ctx.moveTo(pts[0].x, pts[0].y);
    for (let i = 0; i < pts.length - 1; i++) {
      const p0 = pts[Math.max(0, i - 1)];
      const p1 = pts[i];
      const p2 = pts[i + 1];
      const p3 = pts[Math.min(pts.length - 1, i + 2)];

      const cp1x = p1.x + (p2.x - p0.x) * tension;
      const cp1y = p1.y + (p2.y - p0.y) * tension;
      const cp2x = p2.x - (p3.x - p1.x) * tension;
      const cp2y = p2.y - (p3.y - p1.y) * tension;

      ctx.bezierCurveTo(cp1x, cp1y, cp2x, cp2y, p2.x, p2.y);
    }

    const lineGrad = ctx.createLinearGradient(0, 0, w, 0);
    lineGrad.addColorStop(0, currentMoodDef.gradient[0] + 'aa');
    lineGrad.addColorStop(1, currentMoodDef.gradient[1]);
    ctx.strokeStyle = lineGrad;
    ctx.lineWidth = 2;
    ctx.lineJoin = 'round';
    ctx.stroke();

    // Draw mood-change segments (colored by mood)
    let prevMood = points[0].mood;
    for (let i = 1; i < points.length; i++) {
      if (points[i].mood !== prevMood) {
        // Draw transition marker
        const x = i * step;
        const y = yForConf(points[i].confidence);
        const mDef = MOOD_STATES[points[i].mood] || MOOD_STATES.unknown;

        ctx.beginPath();
        ctx.arc(x, y, 3, 0, Math.PI * 2);
        ctx.fillStyle = mDef.color;
        ctx.fill();
        ctx.strokeStyle = mDef.color + '60';
        ctx.lineWidth = 1;
        ctx.stroke();

        prevMood = points[i].mood;
      }
    }

    // Draw current-value dot with glow
    const lastX = (points.length - 1) * step;
    const lastY = yForConf(points[points.length - 1].confidence);

    // Glow
    ctx.beginPath();
    ctx.arc(lastX, lastY, 8, 0, Math.PI * 2);
    ctx.fillStyle = currentMoodDef.color + '30';
    ctx.fill();

    // Outer ring
    ctx.beginPath();
    ctx.arc(lastX, lastY, 4, 0, Math.PI * 2);
    ctx.fillStyle = currentMoodDef.color;
    ctx.fill();

    // Inner dot
    ctx.beginPath();
    ctx.arc(lastX, lastY, 2, 0, Math.PI * 2);
    ctx.fillStyle = '#fff';
    ctx.fill();
  }

  _spawnParticles(color) {
    const canvas = this.shadowRoot.getElementById('particles');
    if (!canvas) return;

    const dpr = window.devicePixelRatio || 1;
    const rect = canvas.parentElement.getBoundingClientRect();
    canvas.width = rect.width * dpr;
    canvas.height = rect.height * dpr;
    const ctx = canvas.getContext('2d');
    ctx.scale(dpr, dpr);

    const w = rect.width;
    const h = rect.height;
    const particles = [];

    // Create burst particles
    for (let i = 0; i < 20; i++) {
      const angle = (Math.PI * 2 * i) / 20 + Math.random() * 0.3;
      const speed = 1 + Math.random() * 2;
      particles.push({
        x: w * 0.3,
        y: h * 0.5,
        vx: Math.cos(angle) * speed,
        vy: Math.sin(angle) * speed,
        life: 1,
        decay: 0.015 + Math.random() * 0.01,
        size: 2 + Math.random() * 3,
      });
    }

    const animate = () => {
      ctx.clearRect(0, 0, w, h);
      let alive = false;

      for (const p of particles) {
        if (p.life <= 0) continue;
        alive = true;
        p.x += p.vx;
        p.y += p.vy;
        p.vy += 0.02; // gravity
        p.life -= p.decay;

        ctx.globalAlpha = p.life;
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.size * p.life, 0, Math.PI * 2);
        ctx.fillStyle = color;
        ctx.fill();
      }

      ctx.globalAlpha = 1;
      if (alive) requestAnimationFrame(animate);
    };

    animate();
  }
}

// Registration
if (typeof registerStyxCard === 'function') {
  registerStyxCard('styx-mood-card', StyxMoodCard, {
    name: 'PilotSuite Stimmung',
    description: 'Stimmung mit Konfidenz-Gauge, Neuronen, Verlaufschart und Partikeleffekten.',
  });
} else {
  customElements.define('styx-mood-card', StyxMoodCard);
  window.customCards = window.customCards || [];
  window.customCards.push({
    type: 'styx-mood-card',
    name: 'PilotSuite Stimmung',
    description: 'Stimmung mit Konfidenz-Gauge, Neuronen, Verlaufschart und Partikeleffekten.',
    preview: true,
  });
}
