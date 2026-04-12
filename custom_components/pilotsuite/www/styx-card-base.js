/**
 * PilotSuite Styx Card Base v1.0.0
 *
 * Shared base class and utilities for all PilotSuite Lovelace cards.
 * Import via: <script src="/api/v1/cards/styx-card-base.js"></script>
 * (must be loaded before individual cards)
 *
 * Provides:
 * - StyxCardBase — HTMLElement base with Shadow DOM, config, hass integration
 * - StyxCoreApi  — Mixin for Core API communication (_getCoreUrl, _getToken, _coreFetch)
 * - Utility functions: _esc, _sensorVal, registerStyxCard
 */

/* -----------------------------------------------------------------------
 * Utility functions
 * ----------------------------------------------------------------------- */

/**
 * Escape HTML text to prevent XSS.
 * @param {string} s — raw string
 * @returns {string} — HTML-safe string
 */
function styxEsc(s) {
  const el = document.createElement('span');
  el.textContent = s || '';
  return el.innerHTML;
}

/**
 * Register a custom element as a Lovelace card.
 * @param {string} tagName — e.g. 'styx-mood-card'
 * @param {typeof HTMLElement} cls — the card class
 * @param {object} meta — { name, description, preview }
 */
function registerStyxCard(tagName, cls, meta = {}) {
  if (!customElements.get(tagName)) {
    customElements.define(tagName, cls);
  }
  window.customCards = window.customCards || [];
  window.customCards.push({
    type: tagName,
    name: meta.name || tagName,
    description: meta.description || '',
    preview: meta.preview !== false,
  });
}

/* -----------------------------------------------------------------------
 * StyxCardBase — shared HTMLElement base for all cards
 * ----------------------------------------------------------------------- */

class StyxCardBase extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: 'open' });
    this._config = {};
    this._hass = null;
  }

  /** Default config element (override in subclass if needed). */
  static getConfigElement() {
    return document.createElement('hui-generic-entity-row');
  }

  /**
   * Called by Lovelace when config changes.
   * Override in subclass; call super.setConfig(config) to store config.
   */
  setConfig(config) {
    this._config = config;
  }

  /**
   * Called by Lovelace whenever hass state changes.
   * Default: store hass + call _render().
   * Override for debounce/fetch patterns.
   */
  set hass(hass) {
    this._hass = hass;
    this._render();
  }

  /** Grid height for Lovelace layout. Override per card. */
  getCardSize() {
    return 3;
  }

  /** HTML-escape helper. */
  _esc(s) {
    return styxEsc(s);
  }

  /**
   * Read a HA sensor value with multiple naming fallbacks.
   * @param {string} entityId — full entity_id or short suffix
   * @param {*} fallback — returned when sensor not found
   * @returns {{ state: string, attrs: object } | *}
   */
  _sensorVal(entityId, fallback) {
    if (!this._hass) return fallback;
    const prefixes = ['sensor.pilotsuite_', 'sensor.copilot_ha_', 'sensor.copilot_'];
    const candidates = entityId.startsWith('sensor.')
      ? [entityId]
      : prefixes.map(p => p + entityId);
    for (const eid of candidates) {
      const s = this._hass.states[eid];
      if (s) return { state: s.state, attrs: s.attributes || {} };
    }
    return fallback;
  }

  /**
   * Build a circular SVG gauge.
   * @param {number} value — 0–100
   * @param {string} startColor — gradient start
   * @param {string} endColor — gradient end
   * @param {string} label — display label
   * @returns {string} — SVG HTML
   */
  _buildGaugeSvg(value, startColor, endColor, label) {
    const size = 100, cx = 50, cy = 50, r = 38;
    const circ = 2 * Math.PI * r;
    const pct = Math.max(0, Math.min(100, value));
    const offset = circ - (circ * pct) / 100;
    const gid = `g_${label.toLowerCase().replace(/\W/g, '_')}`;
    return `
      <svg viewBox="0 0 ${size} ${size}" class="gauge">
        <defs>
          <linearGradient id="${gid}" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stop-color="${startColor}"/>
            <stop offset="100%" stop-color="${endColor}"/>
          </linearGradient>
        </defs>
        <circle cx="${cx}" cy="${cy}" r="${r}"
          fill="none" stroke="#1e2a36" stroke-width="7"/>
        <circle cx="${cx}" cy="${cy}" r="${r}"
          fill="none" stroke="url(#${gid})" stroke-width="7"
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

  /**
   * Shared PilotSuite design tokens as CSS string.
   * Use in subclass _render(): `<style>${this._designTokens()} ...</style>`
   */
  _designTokens() {
    return `
      :host {
        /* ── PilotSuite Design System ─────────────── */
        --ps-accent: var(--accent-color, #4fc3f7);
        --ps-green: #81c784; --ps-orange: #ffb74d;
        --ps-red: #ef5350; --ps-purple: #ce93d8;
        /* Surfaces */
        --ps-bg: var(--card-background-color, var(--ha-card-background, #1a1a2e));
        --ps-surface: var(--secondary-background-color, #222240);
        --ps-border: var(--divider-color, rgba(255,255,255,0.08));
        /* Text */
        --ps-text: var(--primary-text-color, #e0e0f0);
        --ps-text-secondary: var(--secondary-text-color, #9e9eb8);
        --ps-text-disabled: var(--disabled-text-color, #666);
        /* Typography */
        --ps-fs-xs: 0.75rem; --ps-fs-sm: 0.8125rem;
        --ps-fs-base: 0.875rem; --ps-fs-md: 0.9375rem;
        --ps-fs-lg: 1.0625rem; --ps-fs-xl: 1.25rem;
        /* Spacing */
        --ps-sp-xs: 4px; --ps-sp-sm: 8px;
        --ps-sp-md: 12px; --ps-sp-lg: 16px;
        /* Radius */
        --ps-radius: var(--ha-card-border-radius, 12px);
        --ps-radius-sm: 8px;
        /* Transition */
        --ps-transition: 0.2s ease;
      }
      ha-card {
        padding: var(--ps-sp-lg);
        color: var(--ps-text);
        font-family: var(--paper-font-body1_-_font-family, system-ui, sans-serif);
      }
      .ps-card-header {
        display: flex; align-items: center; gap: var(--ps-sp-sm);
        margin-bottom: var(--ps-sp-md); font-weight: 600;
        font-size: var(--ps-fs-md);
      }
      .ps-card-header ha-icon, .ps-card-header .icon {
        color: var(--ps-accent); --mdc-icon-size: 20px;
      }
      .ps-badge {
        display: inline-flex; align-items: center; gap: 4px;
        padding: 3px 10px; border-radius: 12px;
        font-size: var(--ps-fs-xs); font-weight: 600;
      }
      .ps-badge--ok { background: rgba(129,199,132,0.15); color: var(--ps-green); }
      .ps-badge--warn { background: rgba(255,183,77,0.15); color: var(--ps-orange); }
      .ps-badge--error { background: rgba(239,83,80,0.15); color: var(--ps-red); }
      .ps-badge--info { background: rgba(79,195,247,0.15); color: var(--ps-accent); }
      .ps-empty-state {
        text-align: center; padding: var(--ps-sp-xl, 24px);
        color: var(--ps-text-secondary); font-size: var(--ps-fs-sm);
      }
      .ps-loading {
        display: flex; align-items: center; justify-content: center;
        gap: var(--ps-sp-sm); padding: var(--ps-sp-lg);
        color: var(--ps-text-secondary); font-size: var(--ps-fs-sm);
      }
      .ps-loading::before {
        content: ""; width: 16px; height: 16px;
        border: 2px solid var(--ps-surface); border-top-color: var(--ps-accent);
        border-radius: 50%; animation: ps-spin 0.8s linear infinite;
      }
      @keyframes ps-spin { to { transform: rotate(360deg); } }
      .ps-error-banner {
        background: rgba(239,83,80,0.1); border: 1px solid rgba(239,83,80,0.3);
        border-radius: var(--ps-radius-sm); padding: var(--ps-sp-sm) var(--ps-sp-md);
        color: var(--ps-red); font-size: var(--ps-fs-sm);
        display: flex; align-items: center; gap: var(--ps-sp-sm);
        margin-bottom: var(--ps-sp-md);
      }
    `;
  }

  /**
   * Render a loading state placeholder.
   * @param {string} message — optional loading message
   */
  _renderLoading(message = 'Laden...') {
    return `<div class="ps-loading">${this._esc(message)}</div>`;
  }

  /**
   * Render an error banner.
   * @param {string} message — error description
   */
  _renderError(message) {
    return `<div class="ps-error-banner">⚠ ${this._esc(message)}</div>`;
  }

  /**
   * Render an empty state with optional icon.
   * @param {string} message — empty state message
   */
  _renderEmpty(message = 'Keine Daten verfügbar') {
    return `<div class="ps-empty-state">${this._esc(message)}</div>`;
  }

  /** Override in subclass to render card content into shadowRoot. */
  _render() {}
}

/* -----------------------------------------------------------------------
 * StyxCoreApiCard — extended base for cards that talk to Core API
 * ----------------------------------------------------------------------- */

class StyxCoreApiCard extends StyxCardBase {
  constructor() {
    super();
    this._loading = false;
    this._loadError = null;
    this._stale = false;
    this._lastFetch = 0;
  }

  /**
   * Resolve Core Add-on base URL.
   * Priority: config > sensor attribute > default.
   */
  _getCoreUrl() {
    if (this._config.core_url) return this._config.core_url;
    if (this._hass) {
      const apiSensor = this._hass.states['sensor.pilotsuite_core_api_v1']
        || this._hass.states['sensor.copilot_ha_core_api_v1'];
      if (apiSensor && apiSensor.attributes && apiSensor.attributes.base_url) {
        return apiSensor.attributes.base_url;
      }
    }
    return 'http://homeassistant.local:8909';
  }

  /** Resolve auth token for Core API requests. */
  _getToken() {
    if (this._config.auth_token) return this._config.auth_token;
    if (this._hass && this._hass.auth && this._hass.auth.data) {
      return this._hass.auth.data.access_token || '';
    }
    return '';
  }

  /**
   * Fetch JSON from Core API with timeout and error handling.
   * @param {string} path — API path (e.g. '/api/v1/mood')
   * @param {object} opts — { method, body, timeoutMs }
   * @returns {Promise<object|null>}
   */
  async _coreFetch(path, { method = 'GET', body = null, timeoutMs = 15000 } = {}) {
    const url = this._getCoreUrl();
    const ctrl = new AbortController();
    const timer = setTimeout(() => ctrl.abort(), timeoutMs);
    const headers = { 'X-Auth-Token': this._getToken() };
    if (body) headers['Content-Type'] = 'application/json';

    try {
      const resp = await fetch(`${url}${path}`, {
        method,
        headers,
        body: body ? JSON.stringify(body) : undefined,
        signal: ctrl.signal,
      });
      clearTimeout(timer);
      if (!resp.ok) {
        this._loadError = `HTTP ${resp.status}`;
        return null;
      }
      this._loadError = null;
      this._stale = false;
      return await resp.json();
    } catch (err) {
      clearTimeout(timer);
      if (err.name === 'AbortError') {
        this._loadError = 'Timeout';
      } else {
        this._loadError = String(err.message || err);
      }
      this._stale = true;
      return null;
    }
  }
}

/* -----------------------------------------------------------------------
 * Telemetry event constants (shared across cards)
 * ----------------------------------------------------------------------- */

const STYX_UI_EVENTS = (window.UiState && window.UiState.EventKeys)
  ? window.UiState.EventKeys
  : Object.freeze({
      LOADING_SHOWN: 'ui_state_loading_shown',
      EMPTY_SHOWN: 'ui_state_empty_shown',
      ERROR_SHOWN: 'ui_state_error_shown',
      GLOBAL_DEGRADED_ON: 'ui_global_degraded_on',
      GLOBAL_DEGRADED_OFF: 'ui_global_degraded_off',
      RETRY_CLICKED: 'ui_state_retry_clicked',
      RETRY_SUCCEEDED: 'ui_state_retry_succeeded',
      RETRY_FAILED: 'ui_state_retry_failed',
    });

/* -----------------------------------------------------------------------
 * Exports (global scope — no module system in Lovelace resources)
 * ----------------------------------------------------------------------- */

window.StyxCardBase = StyxCardBase;
window.StyxCoreApiCard = StyxCoreApiCard;
window.styxEsc = styxEsc;
window.registerStyxCard = registerStyxCard;
window.STYX_UI_EVENTS = STYX_UI_EVENTS;
