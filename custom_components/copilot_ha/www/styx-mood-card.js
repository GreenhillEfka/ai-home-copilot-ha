/**
 * PilotSuite Mood Card v2.1.0
 *
 * Lovelace custom card showing circular gauges for Comfort, Joy, and
 * Frugality per zone, reading from sensor.pilotsuite_mood_* entities.
 *
 * Requires: styx-card-base.js (StyxCardBase, registerStyxCard)
 */

const MOOD_GAUGE_DEFS = [
  { key: "comfort", label: "Comfort", start: "#2196f3", end: "#4caf50" },
  { key: "joy", label: "Joy", start: "#ff9800", end: "#f9d71c" },
  { key: "frugality", label: "Frugality", start: "#9c27b0", end: "#00bcd4" },
];

// Fallback: use StyxCardBase if loaded, otherwise plain HTMLElement
const _Base = window.StyxCardBase || HTMLElement;

class StyxMoodCard extends _Base {
  constructor() {
    super();
    // StyxCardBase already creates shadow DOM; only create if missing
    if (!this.shadowRoot) {
      this.attachShadow({ mode: "open" });
      this._config = {};
    }
  }

  static getStubConfig() {
    return { entity: "sensor.pilotsuite_mood_comfort" };
  }

  setConfig(config) {
    if (!config.entity) {
      throw new Error("Please define an entity");
    }
    this._config = config;
  }

  getCardSize() {
    return 3;
  }

  _gaugeValue(entityId) {
    if (!this._hass) return 0;
    const state = this._hass.states[entityId];
    if (!state) return 0;
    const val = parseFloat(state.state);
    return isNaN(val) ? 0 : Math.max(0, Math.min(100, val));
  }

  _render() {
    const baseEntity = this._config.entity || "sensor.pilotsuite_mood_comfort";
    const prefix = baseEntity.replace(/_comfort$/, "").replace(/_joy$/, "").replace(/_frugality$/, "");

    const gauges = MOOD_GAUGE_DEFS.map((def) => {
      const entityId = `${prefix}_${def.key}`;
      const value = this._gaugeValue(entityId);
      // Use inherited _buildGaugeSvg if available (from StyxCardBase), else inline
      if (typeof this._buildGaugeSvg === 'function') {
        return this._buildGaugeSvg(value, def.start, def.end, def.label);
      }
      return _buildGaugeSvgFallback(value, def.start, def.end, def.label);
    }).join("");

    const zone = this._config.zone || "";
    const title = zone ? `Mood \u2013 ${zone}` : "Mood";

    const designTokens = typeof this._designTokens === 'function' ? this._designTokens() : '';

    this.shadowRoot.innerHTML = `
      <style>
        ${designTokens}
        :host { display: block; }
        ha-card { padding: var(--ps-sp-lg, 16px); }
        .title {
          font-size: var(--ps-fs-md, 0.9375rem);
          font-weight: 600;
          margin-bottom: var(--ps-sp-md, 12px);
        }
        .gauges {
          display: flex;
          justify-content: space-around;
          gap: var(--ps-sp-sm, 8px);
        }
        .gauge { width: 110px; height: 110px; }
        .no-data {
          text-align: center;
          padding: var(--ps-sp-lg, 16px);
          color: var(--ps-text-secondary, var(--secondary-text-color, #9e9eb8));
          font-size: var(--ps-fs-sm, 0.8125rem);
        }
      </style>
      <ha-card>
        <div class="title">${title}</div>
        ${gauges ? `<div class="gauges" role="img" aria-label="Stimmungs-Anzeige: Comfort, Joy, Frugality">${gauges}</div>` : '<div class="no-data">Keine Mood-Daten verfuegbar</div>'}
      </ha-card>`;
  }
}

/** Inline fallback when styx-card-base.js is not loaded. */
function _buildGaugeSvgFallback(value, startColor, endColor, label) {
  const size = 100, cx = 50, cy = 50, r = 38;
  const circ = 2 * Math.PI * r;
  const pct = Math.max(0, Math.min(100, value));
  const offset = circ - (circ * pct) / 100;
  const gid = `g_${label.toLowerCase()}`;
  return `
    <svg viewBox="0 0 ${size} ${size}" class="gauge" role="img" aria-labelledby="title_${gid}">
      <title id="title_${gid}">Stimmungs-Anzeige</title>
      <defs>
        <linearGradient id="${gid}" x1="0%" y1="0%" x2="100%" y2="0%">
          <stop offset="0%" stop-color="${startColor}"/>
          <stop offset="100%" stop-color="${endColor}"/>
        </linearGradient>
      </defs>
      <circle cx="${cx}" cy="${cy}" r="${r}" fill="none" stroke="#1e2a36" stroke-width="7"/>
      <circle cx="${cx}" cy="${cy}" r="${r}" fill="none" stroke="url(#${gid})" stroke-width="7"
        stroke-dasharray="${circ}" stroke-dashoffset="${offset}"
        stroke-linecap="round" transform="rotate(-90 ${cx} ${cy})"
        style="transition: stroke-dashoffset 0.6s ease;"/>
      <text x="${cx}" y="${cy - 4}" text-anchor="middle"
        fill="var(--primary-text-color, #e6eef6)" font-size="16" font-weight="700"
        font-family="system-ui,sans-serif">${Math.round(pct)}%</text>
      <text x="${cx}" y="${cy + 12}" text-anchor="middle"
        fill="var(--secondary-text-color, #9fb1c3)" font-size="10"
        font-family="system-ui,sans-serif">${label}</text>
    </svg>`;
}

// Registration: use registerStyxCard if available, else manual
if (typeof registerStyxCard === 'function') {
  registerStyxCard("styx-mood-card", StyxMoodCard, {
    name: "PilotSuite Mood Gauges",
    description: "Circular gauges for Comfort, Joy, and Frugality mood dimensions.",
  });
} else {
  customElements.define("styx-mood-card", StyxMoodCard);
  window.customCards = window.customCards || [];
  window.customCards.push({
    type: "styx-mood-card",
    name: "PilotSuite Mood Gauges",
    description: "Circular gauges for Comfort, Joy, and Frugality mood dimensions.",
    preview: true,
  });
}
