/**
 * PilotSuite Styx Error Log Card v1.0.0
 *
 * Lovelace custom card displaying error digest with categorization,
 * severity badges, and automated repair suggestions.
 *
 * Reads from sensor.copilot_home_alerts_* and calls
 * /api/v1/errors/digest for aggregated errors with repair hints.
 */

const SEVERITY_CONFIG = {
  critical: { color: '#f44336', icon: 'mdi:alert-circle', label: 'Kritisch' },
  high:     { color: '#ff5722', icon: 'mdi:alert', label: 'Hoch' },
  medium:   { color: '#ff9800', icon: 'mdi:alert-outline', label: 'Mittel' },
  low:      { color: '#4caf50', icon: 'mdi:information', label: 'Niedrig' },
};

const CATEGORY_LABELS = {
  connectivity:  'Netzwerk',
  security:      'Sicherheit',
  configuration: 'Konfiguration',
  system:        'System',
  database:      'Datenbank',
  automation:    'Automatisierung',
  device:        'Geraet',
  other:         'Sonstige',
};

class StyxErrorCard extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: 'open' });
    this._config = {};
    this._hass = null;
    this._errors = [];
    this._summary = {};
    this._lastFetch = 0;
    this._expanded = {};
    this._loadError = null;
    this._stale = false;
  }

  static getConfigElement() {
    return document.createElement('hui-generic-entity-row');
  }

  static getStubConfig() {
    return {
      title: 'Fehler & Reparatur',
      hours: 24,
      max_errors: 20,
    };
  }

  setConfig(config) {
    this._config = {
      title: config.title || 'Fehler & Reparaturvorschlaege',
      hours: config.hours || 24,
      max_errors: config.max_errors || 20,
      core_url: config.core_url || '',
      ...config,
    };
  }

  set hass(hass) {
    this._hass = hass;
    const now = Date.now();
    if (now - this._lastFetch > 60000) {
      this._lastFetch = now;
      this._loadErrors();
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

  async _loadErrors() {
    const url = this._getCoreUrl();
    const ctrl = new AbortController();
    const timer = setTimeout(() => ctrl.abort(), 10000);

    this._loadError = null;
    this._stale = false;

    try {
      const resp = await fetch(
        `${url}/api/v1/errors/digest?hours=${this._config.hours}`,
        { headers: { 'X-Auth-Token': this._getToken() }, signal: ctrl.signal }
      );
      clearTimeout(timer);

      if (!resp.ok) {
        this._loadError = `HTTP ${resp.status}`;
        this._stale = this._loadFromSensors();
        this._render();
        return;
      }

      const data = await resp.json();
      if (data && data.ok) {
        this._errors = (data.errors || []).slice(0, this._config.max_errors);
        this._summary = data.summary || {};
        this._loadError = null;
        this._stale = false;
        this._render();
        return;
      }

      this._loadError = 'Unerwartete Antwort';
      this._stale = this._loadFromSensors();
      this._render();
    } catch (e) {
      clearTimeout(timer);
      this._loadError = e.name === 'AbortError' ? 'Zeitueberschreitung' : 'Verbindungsfehler';
      this._stale = this._loadFromSensors();
      this._render();
    }
  }

  _loadFromSensors() {
    if (!this._hass) return false;
    const alertSensor = this._hass.states['sensor.copilot_ha_home_alerts_count'] ||
                        this._hass.states['sensor.copilot_home_alerts_count'];
    if (!alertSensor) return false;

    const attrs = alertSensor.attributes || {};
    const total = parseInt(alertSensor.state, 10) || 0;
    this._summary = {
      total_errors: total,
      by_category: {
        system: attrs.system_count || 0,
        device: attrs.device_count || 0,
        connectivity: attrs.network_count || 0,
      },
    };

    // No detailed list in sensor fallback; keep whatever list we had.
    return true;
  }

  _esc(s) {
    const el = document.createElement('span');
    el.textContent = s || '';
    return el.innerHTML;
  }

  _formatTime(ts) {
    if (!ts) return '';
    const d = new Date(ts * 1000);
    return d.toLocaleString('de-DE', { hour: '2-digit', minute: '2-digit', day: '2-digit', month: '2-digit' });
  }

  _toggleExpand(idx) {
    this._expanded[idx] = !this._expanded[idx];
    this._render();
  }

  _render() {
    const { _errors: errors, _summary: summary } = this;
    const totalErrors = summary.total_errors || errors.length;
    const byCat = summary.by_category || {};
    const bySev = summary.by_severity || {};

    const showStaleBanner = !!this._loadError;
    const bannerHtml = showStaleBanner ? `
      <div class="banner ${this._stale ? 'warn' : 'err'}">
        ${this._esc(this._loadError)}${this._stale ? ' — letzte bekannte Daten.' : ''}
        <button class="retry" data-action="retry">Erneut versuchen</button>
      </div>` : '';

    const showHardError = !!this._loadError && !this._stale && errors.length === 0 && totalErrors === 0;

    // Summary chips
    let summaryHtml = '';
    if (totalErrors > 0) {
      const chips = Object.entries(byCat).filter(([, v]) => v > 0).map(([cat, count]) => {
        const label = CATEGORY_LABELS[cat] || cat;
        return `<span class="chip">${this._esc(label)}: ${count}</span>`;
      }).join('');
      const sevChips = Object.entries(bySev).filter(([, v]) => v > 0).map(([sev, count]) => {
        const cfg = SEVERITY_CONFIG[sev] || SEVERITY_CONFIG.low;
        return `<span class="chip" style="background:${cfg.color}20;color:${cfg.color};border-color:${cfg.color}40">${cfg.label}: ${count}</span>`;
      }).join('');
      summaryHtml = `<div class="summary">${sevChips}${chips}</div>`;
    }

    // Error list
    let errorsHtml = '';
    if (showHardError) {
      errorsHtml = `
        <div class="state-error">
          <div class="state-title">Fehlerliste konnte nicht geladen werden</div>
          <div class="state-msg">${this._esc(this._loadError)}</div>
          <button class="retry" data-action="retry">Erneut versuchen</button>
        </div>`;
    } else if (errors.length === 0) {
      errorsHtml = `<div class="empty">${this._loadError && this._stale ? 'Details derzeit nicht verfuegbar.' : `Keine Fehler in den letzten ${this._config.hours}h.`}</div>`;
    } else {
      errorsHtml = errors.map((e, idx) => {
        const sev = SEVERITY_CONFIG[e.severity] || SEVERITY_CONFIG.low;
        const cat = CATEGORY_LABELS[e.category] || e.category;
        const expanded = this._expanded[idx];
        const repairs = e.repairs || [];

        let repairHtml = '';
        if (expanded && repairs.length > 0) {
          repairHtml = `
            <div class="repairs">
              <div class="repair-title">Reparaturvorschlaege:</div>
              ${repairs.map(r => `
                <div class="repair">
                  <div class="repair-text">${this._esc(r.suggestion)}</div>
                  ${r.actions && r.actions.length ? `<div class="repair-actions">${r.actions.map(a => `<span class="action-tag">${this._esc(a)}</span>`).join('')}</div>` : ''}
                </div>`).join('')}
            </div>`;
        }

        return `
          <div class="error-item" data-idx="${idx}">
            <div class="err-header">
              <span class="err-sev" style="color:${sev.color}">${sev.label}</span>
              <span class="err-cat">${this._esc(cat)}</span>
              <span class="err-time">${this._formatTime(e.timestamp)}</span>
              ${repairs.length > 0 ? `<span class="err-repair-badge">${repairs.length} Fix</span>` : ''}
            </div>
            <div class="err-msg">${this._esc(e.message)}</div>
            ${e.source ? `<div class="err-source">${this._esc(e.source)}</div>` : ''}
            ${repairHtml}
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
          max-height: 500px;
          overflow-y: auto;
        }
        .header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 12px;
        }
        .title { font-size: 16px; font-weight: 600; }
        .total {
          font-size: 12px;
          padding: 2px 8px;
          border-radius: 10px;
          font-weight: 600;
        }
        .total-ok { background: rgba(76,175,80,0.15); color: #4caf50; }
        .total-warn { background: rgba(255,152,0,0.15); color: #ff9800; }
        .total-err { background: rgba(244,67,54,0.15); color: #f44336; }
        .summary {
          display: flex;
          flex-wrap: wrap;
          gap: 4px;
          margin-bottom: 12px;
        }
        .chip {
          font-size: 10px;
          padding: 2px 8px;
          border-radius: 6px;
          background: rgba(255,255,255,0.06);
          border: 1px solid rgba(255,255,255,0.08);
          color: var(--secondary-text-color, #9fb1c3);
        }
        .error-item {
          padding: 10px 12px;
          margin-bottom: 6px;
          background: rgba(255,255,255,0.03);
          border-radius: 8px;
          border-left: 3px solid rgba(255,255,255,0.1);
          cursor: pointer;
          transition: background 0.15s;
        }
        .error-item:hover { background: rgba(255,255,255,0.06); }
        .err-header {
          display: flex;
          align-items: center;
          gap: 8px;
          margin-bottom: 4px;
          flex-wrap: wrap;
        }
        .err-sev { font-size: 11px; font-weight: 700; }
        .err-cat {
          font-size: 10px;
          padding: 1px 6px;
          border-radius: 4px;
          background: rgba(255,255,255,0.06);
          color: var(--secondary-text-color, #9fb1c3);
        }
        .err-time {
          font-size: 10px;
          color: var(--secondary-text-color, #9fb1c3);
          opacity: 0.6;
          margin-left: auto;
        }
        .err-repair-badge {
          font-size: 10px;
          padding: 1px 6px;
          border-radius: 4px;
          background: rgba(76,175,80,0.15);
          color: #4caf50;
          font-weight: 600;
        }
        .err-msg {
          font-size: 12px;
          line-height: 1.4;
          word-break: break-word;
          color: var(--primary-text-color, #e6eef6);
        }
        .err-source {
          font-size: 10px;
          color: var(--secondary-text-color, #9fb1c3);
          opacity: 0.5;
          margin-top: 2px;
        }
        .repairs {
          margin-top: 8px;
          padding: 8px;
          background: rgba(76,175,80,0.05);
          border-radius: 6px;
          border: 1px solid rgba(76,175,80,0.15);
        }
        .repair-title {
          font-size: 11px;
          font-weight: 600;
          color: #4caf50;
          margin-bottom: 6px;
        }
        .repair {
          margin-bottom: 6px;
        }
        .repair-text {
          font-size: 12px;
          line-height: 1.4;
          color: var(--primary-text-color, #e6eef6);
        }
        .repair-actions {
          display: flex;
          flex-wrap: wrap;
          gap: 4px;
          margin-top: 4px;
        }
        .action-tag {
          font-size: 9px;
          padding: 1px 6px;
          border-radius: 4px;
          background: rgba(79,195,247,0.1);
          color: #4fc3f7;
          border: 1px solid rgba(79,195,247,0.2);
        }
        .banner {
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: 10px;
          padding: 8px 10px;
          margin: 10px 0 10px 0;
          border-radius: 10px;
          font-size: 12px;
          border: 1px solid rgba(255,255,255,0.08);
        }
        .banner.warn { background: rgba(255,152,0,0.12); color: #ffb74d; border-color: rgba(255,152,0,0.25); }
        .banner.err { background: rgba(244,67,54,0.12); color: #ff8a80; border-color: rgba(244,67,54,0.25); }
        button.retry {
          padding: 6px 10px;
          border-radius: 8px;
          border: 1px solid rgba(255,255,255,0.14);
          background: rgba(79,195,247,0.12);
          color: #4fc3f7;
          cursor: pointer;
          font-weight: 700;
          font-size: 12px;
          white-space: nowrap;
        }
        button.retry:hover { background: rgba(79,195,247,0.2); }
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
          <span class="total ${totalErrors === 0 ? 'total-ok' : totalErrors <= 5 ? 'total-warn' : 'total-err'}">
            ${totalErrors === 0 ? 'Alles OK' : `${totalErrors} Fehler`}
          </span>
        </div>
        ${bannerHtml}
        ${summaryHtml}
        ${errorsHtml}
      </div>`;

    // Wire events via delegation
    const card = this.shadowRoot.querySelector('.card');
    if (card) {
      card.addEventListener('click', (e) => {
        const retry = e.target.closest('button.retry');
        if (retry) {
          this._loadErrors();
          return;
        }
        const item = e.target.closest('.error-item');
        if (item) this._toggleExpand(parseInt(item.dataset.idx, 10));
      });
    }
  }
}

customElements.define('styx-error-card', StyxErrorCard);

window.customCards = window.customCards || [];
window.customCards.push({
  type: 'styx-error-card',
  name: 'PilotSuite Styx Fehler',
  description: 'Error digest with categorization and repair suggestions',
});
