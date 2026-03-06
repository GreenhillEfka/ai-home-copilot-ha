/**
 * PilotSuite Styx Suggestions Card v1.0.0
 *
 * Lovelace custom card displaying AI-generated suggestions
 * with accept/snooze/reject governance actions.
 *
 * Reads from sensor.copilot_ha_suggestions and calls Core API
 * for suggestion management.
 */

const CATEGORY_COLORS = {
  energy: '#4caf50',
  comfort: '#2196f3',
  security: '#f44336',
  health: '#ff9800',
  automation: '#9c27b0',
  default: '#607d8b',
};

const CATEGORY_ICONS = {
  energy: 'mdi:lightning-bolt',
  comfort: 'mdi:sofa',
  security: 'mdi:shield-check',
  health: 'mdi:heart-pulse',
  automation: 'mdi:robot',
  default: 'mdi:lightbulb-on',
};

const RISK_COLORS = {
  low: '#4caf50',
  medium: '#ff9800',
  high: '#f44336',
};

class StyxSuggestionsCard extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: 'open' });
    this._config = {};
    this._hass = null;
    this._suggestions = [];
    this._lastFetch = 0;
    this._loadError = null;
    this._stale = false;
    this._actionError = null;
  }

  static getConfigElement() {
    return document.createElement('hui-generic-entity-row');
  }

  static getStubConfig() {
    return {
      title: 'Vorschlaege',
      max_suggestions: 10,
      show_actions: true,
    };
  }

  setConfig(config) {
    this._config = {
      title: config.title || 'KI-Vorschlaege',
      max_suggestions: config.max_suggestions || 10,
      show_actions: config.show_actions !== false,
      core_url: config.core_url || '',
      ...config,
    };
  }

  set hass(hass) {
    this._hass = hass;
    const now = Date.now();
    if (now - this._lastFetch > 30000) {
      this._lastFetch = now;
      this._loadSuggestions();
    }
  }

  getCardSize() {
    return 4;
  }

  _getCoreUrl() {
    if (this._config.core_url) return this._config.core_url;
    if (this._hass) {
      const s = this._hass.states['sensor.copilot_ha_core_api_v1'] ||
                this._hass.states['sensor.pilotsuite_core_api_v1'];
      if (s && s.attributes && s.attributes.base_url) return s.attributes.base_url;
    }
    return 'http://homeassistant.local:8909';
  }

  _getToken() {
    if (this._config.auth_token) return this._config.auth_token;
    if (this._hass && this._hass.auth && this._hass.auth.data) {
      return this._hass.auth.data.access_token || '';
    }
    return '';
  }

  _loadFromSensor() {
    if (!this._hass) return false;
    const s = this._hass.states['sensor.copilot_ha_suggestions'] ||
              this._hass.states['sensor.copilot_suggestions'] ||
              this._hass.states['sensor.pilotsuite_suggestions'];
    if (!s) return false;

    const attrs = s.attributes || {};
    let suggestions = [];

    if (Array.isArray(attrs.suggestions)) {
      suggestions = attrs.suggestions;
    } else if (Array.isArray(attrs.items)) {
      suggestions = attrs.items;
    } else if (typeof s.state === 'string') {
      const st = s.state.trim();
      if ((st.startsWith('[') && st.endsWith(']')) || (st.startsWith('{') && st.endsWith('}'))) {
        try {
          const parsed = JSON.parse(st);
          if (Array.isArray(parsed)) suggestions = parsed;
          else if (parsed && Array.isArray(parsed.suggestions)) suggestions = parsed.suggestions;
        } catch (_e) {
          // ignore parse errors
        }
      }
    }

    if (!Array.isArray(suggestions) || suggestions.length === 0) return false;

    this._suggestions = suggestions.slice(0, this._config.max_suggestions || 10);
    return true;
  }

  async _loadSuggestions() {
    this._actionError = null;
    const url = this._getCoreUrl();
    const ctrl = new AbortController();
    const timer = setTimeout(() => ctrl.abort(), 10000);
    try {
      const resp = await fetch(`${url}/api/v1/suggestions`, {
        headers: { 'X-Auth-Token': this._getToken() },
        signal: ctrl.signal,
      });
      clearTimeout(timer);

      if (resp.ok) {
        const data = await resp.json();
        if (data.ok) {
          this._suggestions = (data.suggestions || []).slice(0, this._config.max_suggestions);
          this._loadError = null;
          this._stale = false;
          this._render();
          return;
        }
      }

      // Non-OK or unexpected payload -> try sensor fallback
      this._loadError = `HTTP ${resp.status || 'Fehler'}`;
      this._stale = this._loadFromSensor();
      this._render();
    } catch (e) {
      clearTimeout(timer);
      this._loadError = e.name === 'AbortError' ? 'Zeitueberschreitung' : 'Verbindungsfehler';
      this._stale = this._loadFromSensor();
      this._render();
    }
  }

  async _action(id, action) {
    if (action === 'retry') {
      this._loadSuggestions();
      return;
    }

    // If we only have last-known (stale) data, do not allow mutating actions.
    if (this._stale) {
      this._actionError = 'Offline — Aktion ist deaktiviert.';
      this._render();
      return;
    }

    const url = this._getCoreUrl();
    try {
      const resp = await fetch(`${url}/api/v1/suggestions/${action}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Auth-Token': this._getToken(),
        },
        body: JSON.stringify({ id }),
      });
      if (!resp.ok) {
        this._actionError = `Aktion fehlgeschlagen (HTTP ${resp.status})`;
        this._render();
        return;
      }
      this._suggestions = this._suggestions.filter(s => (s.id || s.suggestion_id) !== id);
      this._actionError = null;
      this._render();
    } catch (e) {
      this._actionError = 'Aktion fehlgeschlagen';
      this._render();
    }
  }

  _esc(s) {
    const el = document.createElement('span');
    el.textContent = s || '';
    return el.innerHTML;
  }

  _confidenceBadge(conf) {
    const pct = Math.round((conf || 0) * 100);
    let cls = 'conf-low';
    if (pct >= 80) cls = 'conf-high';
    else if (pct >= 50) cls = 'conf-mid';
    return `<span class="badge ${cls}">${pct}%</span>`;
  }

  _render() {
    const suggestions = this._suggestions;
    const hasSuggestions = suggestions.length > 0;
    const showStaleBanner = this._stale || (this._loadError && hasSuggestions);

    const countLabel = this._stale ? `${suggestions.length} letzte` : `${suggestions.length} aktiv`;

    const banners = `
      ${this._actionError ? `<div class="banner err">${this._esc(this._actionError)}</div>` : ''}
      ${showStaleBanner ? `<div class="banner warn">${this._esc(this._loadError || 'Offline')} — letzte bekannte Daten.</div>` : ''}
    `;

    let html = '';

    if (this._loadError && !hasSuggestions) {
      html = `
        <div class="state-error">
          <div class="state-title">Vorschlaege konnten nicht geladen werden</div>
          <div class="state-msg">${this._esc(this._loadError)}</div>
          <button class="retry" data-action="retry">Erneut versuchen</button>
        </div>`;
    } else if (!hasSuggestions) {
      html = '<div class="empty">Keine aktiven Vorschlaege.</div>';
    } else {
      html = `${banners}` + suggestions.map(s => {
        const id = s.id || s.suggestion_id || '';
        const cat = (s.category || 'default').toLowerCase();
        const catColor = CATEGORY_COLORS[cat] || CATEGORY_COLORS.default;
        const risk = (s.risk || 'low').toLowerCase();
        const riskColor = RISK_COLORS[risk] || RISK_COLORS.low;

        const actionsDisabled = this._stale;
        const actions = this._config.show_actions ? `
          <div class="actions ${actionsDisabled ? 'disabled' : ''}">
            <button class="act-accept" data-id="${this._esc(id)}" data-action="accept">Annehmen</button>
            <button class="act-snooze" data-id="${this._esc(id)}" data-action="snooze">Spaeter</button>
            <button class="act-reject" data-id="${this._esc(id)}" data-action="reject">Ablehnen</button>
          </div>` : '';

        return `
          <div class="suggestion">
            <div class="sg-header">
              <span class="sg-title">${this._esc(s.title || s.name || 'Vorschlag')}</span>
              ${this._confidenceBadge(s.confidence)}
            </div>
            <div class="sg-desc">${this._esc(s.description || '')}</div>
            <div class="sg-tags">
              <span class="tag" style="background:${catColor}20;color:${catColor};border:1px solid ${catColor}40">${this._esc(cat)}</span>
              <span class="tag" style="background:${riskColor}20;color:${riskColor};border:1px solid ${riskColor}40">Risiko: ${this._esc(risk)}</span>
              ${s.zone ? `<span class="tag">Zone: ${this._esc(s.zone)}</span>` : ''}
              ${s.estimated_savings ? `<span class="tag" style="background:#4caf5020;color:#4caf50;border:1px solid #4caf5040">${this._esc(s.estimated_savings)}</span>` : ''}
            </div>
            ${actions}
          </div>`;
      }).join('');
    }

    this.shadowRoot.innerHTML = `
      <style>
        :host { display: block; }
        .card {
          background: var(--card-background-color, #1a1a2e);
          border-radius: var(--ha-card-border-radius, 12px);
          padding: 16px;
          color: var(--primary-text-color, #e6eef6);
          font-family: var(--paper-font-body1_-_font-family, system-ui, sans-serif);
        }
        .header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 12px;
        }
        .title { font-size: 16px; font-weight: 600; }
        .count {
          font-size: 12px;
          padding: 2px 8px;
          border-radius: 10px;
          background: rgba(79, 195, 247, 0.15);
          color: #4fc3f7;
        }
        .suggestion {
          padding: 12px;
          margin-bottom: 8px;
          background: rgba(255,255,255,0.04);
          border-radius: 10px;
          border: 1px solid rgba(255,255,255,0.06);
        }
        .sg-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 6px;
        }
        .sg-title { font-size: 14px; font-weight: 600; }
        .badge {
          font-size: 11px;
          padding: 2px 8px;
          border-radius: 8px;
          font-weight: 600;
        }
        .conf-high { background: rgba(76,175,80,0.2); color: #4caf50; }
        .conf-mid { background: rgba(255,152,0,0.2); color: #ff9800; }
        .conf-low { background: rgba(158,158,158,0.2); color: #9e9e9e; }
        .sg-desc {
          font-size: 12px;
          color: var(--secondary-text-color, #9fb1c3);
          margin-bottom: 8px;
          line-height: 1.4;
        }
        .sg-tags {
          display: flex;
          flex-wrap: wrap;
          gap: 4px;
          margin-bottom: 8px;
        }
        .tag {
          font-size: 10px;
          padding: 2px 8px;
          border-radius: 6px;
          background: rgba(255,255,255,0.06);
          color: var(--secondary-text-color, #9fb1c3);
          border: 1px solid rgba(255,255,255,0.08);
        }
        .actions {
          display: flex;
          gap: 6px;
          margin-top: 6px;
        }
        .actions button {
          padding: 4px 12px;
          border-radius: 6px;
          border: none;
          font-size: 11px;
          cursor: pointer;
          font-weight: 600;
          transition: background 0.2s;
        }
        .act-accept {
          background: rgba(76,175,80,0.2);
          color: #4caf50;
        }
        .act-accept:hover { background: rgba(76,175,80,0.35); }
        .act-snooze {
          background: rgba(255,152,0,0.2);
          color: #ff9800;
        }
        .act-snooze:hover { background: rgba(255,152,0,0.35); }
        .act-reject {
          background: rgba(244,67,54,0.15);
          color: #f44336;
        }
        .act-reject:hover { background: rgba(244,67,54,0.3); }
        .banner {
          padding: 8px 10px;
          margin: 10px 0 10px 0;
          border-radius: 10px;
          font-size: 12px;
          border: 1px solid rgba(255,255,255,0.08);
        }
        .banner.warn { background: rgba(255,152,0,0.12); color: #ffb74d; border-color: rgba(255,152,0,0.25); }
        .banner.err { background: rgba(244,67,54,0.12); color: #ff8a80; border-color: rgba(244,67,54,0.25); }
        .actions.disabled button {
          opacity: 0.55;
        }
        .state-error {
          text-align: center;
          padding: 16px 0;
        }
        .state-title {
          font-size: 13px;
          font-weight: 700;
          margin-bottom: 6px;
        }
        .state-msg {
          font-size: 12px;
          color: var(--secondary-text-color, #9fb1c3);
          margin-bottom: 10px;
        }
        button.retry {
          padding: 6px 12px;
          border-radius: 8px;
          border: 1px solid rgba(255,255,255,0.14);
          background: rgba(79,195,247,0.12);
          color: #4fc3f7;
          cursor: pointer;
          font-weight: 700;
          font-size: 12px;
        }
        button.retry:hover { background: rgba(79,195,247,0.2); }
        .empty {
          text-align: center;
          color: var(--secondary-text-color, #9fb1c3);
          padding: 24px 0;
          font-size: 13px;
        }
      </style>
      <div class="card">
        <div class="header">
          <span class="title">${this._esc(this._config.title)}</span>
          <span class="count">${this._esc(countLabel)}</span>
        </div>
        ${html}
      </div>`;

    // Wire buttons via event delegation on card container
    const card = this.shadowRoot.querySelector('.card');
    if (card) {
      card.addEventListener('click', (e) => {
        const btn = e.target.closest('.actions button, button.retry');
        if (btn) this._action(btn.dataset.id || '', btn.dataset.action || 'retry');
      });
    }
  }
}

customElements.define('styx-suggestions-card', StyxSuggestionsCard);

window.customCards = window.customCards || [];
window.customCards.push({
  type: 'styx-suggestions-card',
  name: 'PilotSuite Styx Vorschlaege',
  description: 'AI-powered suggestion cards with governance actions',
});
