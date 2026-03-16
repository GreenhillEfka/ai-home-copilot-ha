/**
 * PilotSuite Mood Card v3.0.0
 *
 * Lovelace custom card showing the current mood state, confidence gauge,
 * and contributing neurons from PilotSuite's neural mood engine.
 *
 * Entities:
 * - sensor.copilot_ha_mood (state: mood name, attrs: confidence, emotions, contributing_neurons)
 * - sensor.copilot_ha_mood_confidence (state: 0-100%, attrs: mood, factors)
 *
 * Requires: styx-card-base.js (StyxCardBase, registerStyxCard) — optional fallback
 */

const MOOD_STATES = {
  relax:    { label: 'Entspannung', icon: '\u{1F9D8}', color: '#4caf50', gradient: ['#2e7d32', '#66bb6a'] },
  focus:    { label: 'Fokus',       icon: '\u{1F3AF}', color: '#2196f3', gradient: ['#1565c0', '#42a5f5'] },
  active:   { label: 'Aktivit\u00e4t',  icon: '\u26A1',    color: '#ff9800', gradient: ['#e65100', '#ffb74d'] },
  sleep:    { label: 'Schlaf',      icon: '\u{1F31C}', color: '#673ab7', gradient: ['#4527a0', '#9575cd'] },
  away:     { label: 'Abwesend',    icon: '\u{1F6B6}', color: '#607d8b', gradient: ['#37474f', '#90a4ae'] },
  alert:    { label: 'Alarm',       icon: '\u{1F6A8}', color: '#f44336', gradient: ['#c62828', '#ef5350'] },
  social:   { label: 'Sozial',      icon: '\u{1F91D}', color: '#e91e63', gradient: ['#880e4f', '#f06292'] },
  recovery: { label: 'Erholung',    icon: '\u{1F33F}', color: '#009688', gradient: ['#00695c', '#4db6ac'] },
  unknown:  { label: 'Unbekannt',   icon: '\u2753',    color: '#9e9e9e', gradient: ['#616161', '#bdbdbd'] },
};

const _Base = window.StyxCardBase || HTMLElement;

class StyxMoodCard extends _Base {
  constructor() {
    super();
    if (!this.shadowRoot) {
      this.attachShadow({ mode: 'open' });
      this._config = {};
    }
  }

  static getStubConfig() {
    return { entity: 'sensor.copilot_ha_mood' };
  }

  setConfig(config) {
    this._config = config;
  }

  getCardSize() {
    return 4;
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

  _render() {
    // Find mood entity — use config entity or auto-detect
    let moodState = null;
    if (this._config.entity && this._hass) {
      moodState = this._hass.states[this._config.entity];
    }
    if (!moodState) moodState = this._findEntity('mood');

    const confState = this._findEntity('mood_confidence');

    const moodKey = (moodState ? moodState.state : 'unknown').toLowerCase();
    const mood = MOOD_STATES[moodKey] || MOOD_STATES.unknown;
    const confidence = confState ? parseInt(confState.state, 10) || 0 : 0;

    // Get contributing neurons from attributes
    const attrs = moodState ? (moodState.attributes || {}) : {};
    const emotions = attrs.emotions || [];
    const neurons = attrs.contributing_neurons || [];
    const zone = attrs.zone || '';

    // Build confidence gauge SVG
    const r = 42, circ = 2 * Math.PI * r;
    const offset = circ - (circ * Math.min(100, confidence)) / 100;

    // Build neurons list
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

    const title = this._config.title || (zone ? `Stimmung \u2013 ${this._esc(zone)}` : 'Stimmung');
    const designTokens = typeof this._designTokens === 'function' ? this._designTokens() : '';

    this.shadowRoot.innerHTML = `
      <style>
        ${designTokens}
        :host { display: block; }
        ha-card { padding: 16px; }
        .mood-header { display: flex; align-items: center; gap: 8px; margin-bottom: 12px; }
        .mood-title { font-size: 0.9375rem; font-weight: 600; flex: 1; }
        .mood-zone { font-size: 0.75rem; color: var(--secondary-text-color, #9e9eb8); }
        .mood-main { display: flex; align-items: center; gap: 20px; margin-bottom: 16px; }
        .mood-gauge { position: relative; width: 100px; height: 100px; flex-shrink: 0; }
        .mood-gauge svg { width: 100%; height: 100%; }
        .mood-icon { position: absolute; top: 50%; left: 50%; transform: translate(-50%,-50%); font-size: 28px; }
        .mood-info { flex: 1; min-width: 0; }
        .mood-state { font-size: 1.5rem; font-weight: 700; color: ${mood.color}; margin-bottom: 4px; }
        .mood-conf { font-size: 0.8125rem; color: var(--secondary-text-color, #9e9eb8); }
        .neurons-title { font-size: 0.8125rem; font-weight: 600; margin-bottom: 8px; color: var(--secondary-text-color, #9e9eb8); }
        .neuron-row { display: flex; align-items: center; gap: 8px; margin-bottom: 5px; }
        .neuron-name { font-size: 0.75rem; width: 90px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
        .neuron-bar-bg { flex: 1; height: 6px; background: rgba(255,255,255,0.06); border-radius: 3px; overflow: hidden; }
        .neuron-bar { height: 100%; border-radius: 3px; transition: width 0.4s ease; }
        .neuron-val { font-size: 0.7rem; width: 32px; text-align: right; color: var(--secondary-text-color, #9e9eb8); }
        .no-data { text-align: center; padding: 24px; color: var(--secondary-text-color, #9e9eb8); font-size: 0.8125rem; }
      </style>
      <ha-card>
        <div class="mood-header">
          <span class="mood-title">${title}</span>
          ${zone ? `<span class="mood-zone">${this._esc(zone)}</span>` : ''}
        </div>
        <div class="mood-main">
          <div class="mood-gauge">
            <svg viewBox="0 0 100 100">
              <defs>
                <linearGradient id="mg" x1="0%" y1="0%" x2="100%" y2="0%">
                  <stop offset="0%" stop-color="${mood.gradient[0]}"/>
                  <stop offset="100%" stop-color="${mood.gradient[1]}"/>
                </linearGradient>
              </defs>
              <circle cx="50" cy="50" r="${r}" fill="none" stroke="rgba(255,255,255,0.06)" stroke-width="6"/>
              <circle cx="50" cy="50" r="${r}" fill="none" stroke="url(#mg)" stroke-width="6"
                stroke-dasharray="${circ}" stroke-dashoffset="${offset}"
                stroke-linecap="round" transform="rotate(-90 50 50)"
                style="transition: stroke-dashoffset 0.6s ease;"/>
            </svg>
            <div class="mood-icon">${mood.icon}</div>
          </div>
          <div class="mood-info">
            <div class="mood-state">${mood.label}</div>
            <div class="mood-conf">Konfidenz: ${confidence}%</div>
          </div>
        </div>
        ${neuronsHtml ? `
          <div class="neurons-title">Beitragende Neuronen</div>
          ${neuronsHtml}
        ` : ''}
        ${!moodState ? '<div class="no-data">Keine Mood-Daten verf\u00FCgbar</div>' : ''}
      </ha-card>`;
  }
}

// Registration
if (typeof registerStyxCard === 'function') {
  registerStyxCard('styx-mood-card', StyxMoodCard, {
    name: 'PilotSuite Stimmung',
    description: 'Aktuelle Stimmung mit Konfidenz-Gauge und Neuronen-Details.',
  });
} else {
  customElements.define('styx-mood-card', StyxMoodCard);
  window.customCards = window.customCards || [];
  window.customCards.push({
    type: 'styx-mood-card',
    name: 'PilotSuite Stimmung',
    description: 'Aktuelle Stimmung mit Konfidenz-Gauge und Neuronen-Details.',
    preview: true,
  });
}
