/**
 * PilotSuite Styx Suggestions Card v1.1.0
 *
 * Lovelace custom card displaying AI-generated suggestions
 * with accept/snooze/reject governance actions.
 *
 * PS-UX-015:
 * - List states: loading / empty / error / offline-read-only
 * - Filter empty case with CTA "Filter zurücksetzen"
 * - Detail sub-screen (no blank view) + soft-guard for offline/auth-missing
 * - ui_state_* telemetry events (best-effort)
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

const UI_STATE_EVENTS = Object.freeze({
  LOADING_SHOWN: 'ui_state_loading_shown',
  EMPTY_SHOWN: 'ui_state_empty_shown',
  ERROR_SHOWN: 'ui_state_error_shown',
  GLOBAL_DEGRADED_ON: 'ui_global_degraded_on',
  GLOBAL_DEGRADED_OFF: 'ui_global_degraded_off',
  RETRY_CLICKED: 'ui_state_retry_clicked',
  RETRY_SUCCEEDED: 'ui_state_retry_succeeded',
  RETRY_FAILED: 'ui_state_retry_failed',
});

const UI_ERROR_CLASS = Object.freeze({
  AUTH: 'auth',
  NETWORK: 'network',
  UNKNOWN: 'unknown',
});

function _dispatchUiEvent(eventName, detail = {}) {
  if (typeof window === 'undefined') return;
  try {
    window.dispatchEvent(
      new CustomEvent(eventName, {
        detail: {
          ...detail,
          event: eventName,
          emittedAt: detail.emittedAt || new Date().toISOString(),
        },
        bubbles: true,
        cancelable: false,
      })
    );
  } catch (_e) {
    // best-effort only
  }
}

class StyxSuggestionsCard extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: 'open' });

    this._config = {};
    this._hass = null;

    // Data
    this._suggestions = [];
    this._lastFetch = 0;

    // List state
    this._loading = false;
    this._loadError = null;
    this._loadErrorClass = null;
    this._stale = false; // last-known data
    this._authMissing = false;

    // UI state
    this._actionError = null;
    this._filterCategory = 'all';
    this._selectedId = null;

    // Telemetry
    this._attempt = 0;
    this._emitted = new Set();
    this._degradedActive = false;

    this._boundClick = (e) => this._onClick(e);
    this.shadowRoot.addEventListener('click', this._boundClick);
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

    // Render immediately (so the card doesn't stay blank until first hass update)
    this._render();
  }

  set hass(hass) {
    this._hass = hass;

    // If we can already hydrate from sensor, do so immediately (helps offline-read-only).
    if ((!this._suggestions || this._suggestions.length === 0) && this._loadFromSensor()) {
      this._stale = true;
      this._render();
    }

    const now = Date.now();
    if (now - this._lastFetch > 30000) {
      this._lastFetch = now;
      this._loadSuggestions({ source: 'auto' });
    }
  }

  getCardSize() {
    return 4;
  }

  _scope(sub = 'list') {
    return `suggestions/${sub}`;
  }

  _emitOnce(key, eventName, detail) {
    const namespaced = `${this._attempt}:${key}`;
    if (this._emitted.has(namespaced)) return;
    this._emitted.add(namespaced);
    _dispatchUiEvent(eventName, detail);
  }

  _setDegraded(active, payload = {}) {
    if (active === this._degradedActive) return;
    this._degradedActive = active;

    if (active) {
      _dispatchUiEvent(UI_STATE_EVENTS.GLOBAL_DEGRADED_ON, {
        scope: this._scope('global'),
        reason: payload.reason || 'degraded',
        source: 'styx-suggestions-card',
      });
    } else {
      _dispatchUiEvent(UI_STATE_EVENTS.GLOBAL_DEGRADED_OFF, {
        scope: this._scope('global'),
        reason: payload.reason || 'recovered',
        source: 'styx-suggestions-card',
      });
    }
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

  _isReadOnly() {
    return !!(this._stale || this._authMissing);
  }

  _readOnlyReason() {
    if (this._authMissing) return 'Nicht authentifiziert';
    if (this._stale) return 'Offline';
    return '';
  }

  _classifyFetchError(resp, error) {
    if (this._authMissing) return UI_ERROR_CLASS.AUTH;
    if (resp && (resp.status === 401 || resp.status === 403)) return UI_ERROR_CLASS.AUTH;
    if (error && error.name === 'AbortError') return UI_ERROR_CLASS.NETWORK;
    if (error) return UI_ERROR_CLASS.NETWORK;
    if (resp && resp.status) return UI_ERROR_CLASS.UNKNOWN;
    return UI_ERROR_CLASS.UNKNOWN;
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

  async _loadSuggestions({ source = 'auto' } = {}) {
    this._actionError = null;

    // Attempt boundary for telemetry de-dup.
    this._attempt += 1;
    this._emitted = new Set();

    this._authMissing = !this._getToken();

    // Show loading state if we have no content yet.
    this._loading = true;
    if (!this._suggestions || this._suggestions.length === 0) {
      this._emitOnce('loading_shown', UI_STATE_EVENTS.LOADING_SHOWN, {
        scope: this._scope('list'),
        source: 'styx-suggestions-card',
        message: 'Lade Vorschlaege',
      });
      this._render();
    }

    if (this._authMissing) {
      // Soft-guard: no auth token -> read-only, last-known data if available.
      this._loadError = 'Kein Auth-Token';
      this._loadErrorClass = UI_ERROR_CLASS.AUTH;
      this._stale = this._loadFromSensor();
      this._loading = false;
      this._setDegraded(true, { reason: 'auth_missing' });

      if (!this._stale) {
        this._emitOnce('error_list_auth', UI_STATE_EVENTS.ERROR_SHOWN, {
          scope: this._scope('list'),
          source: 'styx-suggestions-card',
          message: 'Authentifizierung fehlt.',
          detail: 'Bitte Token/Berechtigungen prüfen.',
          degraded: true,
          error_class: UI_ERROR_CLASS.AUTH,
        });
      }

      if (source === 'retry') {
        _dispatchUiEvent(UI_STATE_EVENTS.RETRY_FAILED, {
          scope: this._scope('list'),
          source: 'styx-suggestions-card',
          action: 'Erneut versuchen',
          error: 'auth_missing',
        });
      }

      this._render();
      return;
    }

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
        if (data && data.ok) {
          this._suggestions = (data.suggestions || []).slice(0, this._config.max_suggestions);
          this._loadError = null;
          this._loadErrorClass = null;
          this._stale = false;
          this._loading = false;
          this._setDegraded(false, { reason: 'core_ok' });

          if (source === 'retry') {
            _dispatchUiEvent(UI_STATE_EVENTS.RETRY_SUCCEEDED, {
              scope: this._scope('list'),
              source: 'styx-suggestions-card',
              action: 'Erneut versuchen',
            });
          }

          this._render();
          return;
        }
      }

      // Non-OK or unexpected payload -> try sensor fallback (offline-read-only).
      this._loadError = `HTTP ${resp.status || 'Fehler'}`;
      this._loadErrorClass = this._classifyFetchError(resp, null);
      this._stale = this._loadFromSensor();
      this._loading = false;

      if (this._stale) {
        this._setDegraded(true, { reason: 'offline_http' });
      } else {
        this._emitOnce('error_list_http', UI_STATE_EVENTS.ERROR_SHOWN, {
          scope: this._scope('list'),
          source: 'styx-suggestions-card',
          message: 'Vorschlaege konnten nicht geladen werden',
          detail: this._loadError,
          degraded: false,
          error_class: this._loadErrorClass || UI_ERROR_CLASS.UNKNOWN,
        });
      }

      if (source === 'retry') {
        _dispatchUiEvent(UI_STATE_EVENTS.RETRY_FAILED, {
          scope: this._scope('list'),
          source: 'styx-suggestions-card',
          action: 'Erneut versuchen',
          error: this._loadError,
        });
      }

      this._render();
    } catch (e) {
      clearTimeout(timer);
      this._loadError = e && e.name === 'AbortError' ? 'Zeitueberschreitung' : 'Verbindungsfehler';
      this._loadErrorClass = this._classifyFetchError(null, e);
      this._stale = this._loadFromSensor();
      this._loading = false;

      if (this._stale) {
        this._setDegraded(true, { reason: 'offline_network' });
      } else {
        this._emitOnce('error_list_net', UI_STATE_EVENTS.ERROR_SHOWN, {
          scope: this._scope('list'),
          source: 'styx-suggestions-card',
          message: 'Vorschlaege konnten nicht geladen werden',
          detail: this._loadError,
          degraded: true,
          error_class: UI_ERROR_CLASS.NETWORK,
        });
      }

      if (source === 'retry') {
        _dispatchUiEvent(UI_STATE_EVENTS.RETRY_FAILED, {
          scope: this._scope('list'),
          source: 'styx-suggestions-card',
          action: 'Erneut versuchen',
          error: this._loadError,
        });
      }

      this._render();
    }
  }

  async _action(id, action) {
    if (action === 'retry') {
      _dispatchUiEvent(UI_STATE_EVENTS.RETRY_CLICKED, {
        scope: this._scope('list'),
        source: 'styx-suggestions-card',
        action: 'Erneut versuchen',
      });
      this._loadSuggestions({ source: 'retry' });
      return;
    }

    if (action === 'reset_filters') {
      this._filterCategory = 'all';
      this._render();
      return;
    }

    if (action === 'detail-open') {
      if (id) {
        this._selectedId = id;
        this._render();
      }
      return;
    }

    if (action === 'detail-close') {
      this._selectedId = null;
      this._render();
      return;
    }

    // Mutating actions (accept/snooze/reject)
    if (this._isReadOnly()) {
      this._actionError = `${this._readOnlyReason()} — Aktion ist deaktiviert.`;
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

      // Optimistic UI: remove from list
      this._suggestions = (this._suggestions || []).filter((s) => this._getSuggestionId(s) !== id);
      this._actionError = null;

      // If we removed the selected item, close detail.
      if (this._selectedId === id) this._selectedId = null;

      this._render();
    } catch (_e) {
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

  _getSuggestionId(s) {
    return (s && (s.id || s.suggestion_id)) || '';
  }

  _getSelectedSuggestion() {
    if (!this._selectedId) return null;
    return (this._suggestions || []).find((s) => this._getSuggestionId(s) === this._selectedId) || null;
  }

  _getFilterOptions() {
    return [
      { id: 'all', label: 'Alle' },
      { id: 'energy', label: 'Energie' },
      { id: 'comfort', label: 'Komfort' },
      { id: 'security', label: 'Sicherheit' },
      { id: 'health', label: 'Gesundheit' },
      { id: 'automation', label: 'Automation' },
    ];
  }

  _applyFilters(items) {
    const cat = (this._filterCategory || 'all').toLowerCase();
    if (cat === 'all') return items;
    return (items || []).filter((s) => String(s.category || 'default').toLowerCase() === cat);
  }

  _renderFilters(hasAnySuggestions) {
    const opts = this._getFilterOptions();
    const show = hasAnySuggestions || (this._filterCategory && this._filterCategory !== 'all');
    if (!show) return '';

    const chips = opts
      .map((o) => {
        const active = (this._filterCategory || 'all') === o.id;
        return `
          <button class="chip ${active ? 'active' : ''}" data-action="set_filter" data-filter="${this._esc(o.id)}" type="button">${this._esc(o.label)}</button>
        `;
      })
      .join('');

    return `<div class="filters" aria-label="Filter">${chips}</div>`;
  }

  _render() {
    const suggestions = this._suggestions || [];
    const hasSuggestions = suggestions.length > 0;

    const selected = this._getSelectedSuggestion();
    const selectedMissing = !!(this._selectedId && !selected);

    const readOnly = this._isReadOnly();
    const showStaleBanner = readOnly && hasSuggestions;

    const filtered = this._applyFilters(suggestions);
    const filterEmpty = hasSuggestions && filtered.length === 0;

    const countLabel = readOnly ? `${suggestions.length} letzte` : `${suggestions.length} aktiv`;

    const filterBar = this._renderFilters(hasSuggestions);

    const banners = `
      ${this._actionError ? `<div class="banner err">${this._esc(this._actionError)}</div>` : ''}
      ${showStaleBanner ? `<div class="banner warn">${this._esc(this._readOnlyReason())} — letzte bekannte Daten. Aktionen sind deaktiviert.</div>` : ''}
    `;

    let html = '';

    if (this._loading && !hasSuggestions && !this._loadError) {
      html = `
        <div class="state-loading" aria-label="Lade Vorschlaege">
          <div class="sk sk-1"></div>
          <div class="sk sk-2"></div>
          <div class="sk sk-3"></div>
        </div>`;

      this._emitOnce('loading', UI_STATE_EVENTS.LOADING_SHOWN, {
        scope: this._scope('list'),
        source: 'styx-suggestions-card',
        message: 'Ladevorgang',
      });
    } else if (this._loadError && !hasSuggestions) {
      html = `
        <div class="state-error">
          <div class="state-title">Vorschlaege konnten nicht geladen werden</div>
          <div class="state-msg">${this._esc(this._loadError)}</div>
          <button class="retry" data-action="retry">Erneut versuchen</button>
        </div>`;

      this._emitOnce('error_list', UI_STATE_EVENTS.ERROR_SHOWN, {
        scope: this._scope('list'),
        source: 'styx-suggestions-card',
        message: 'Vorschlaege konnten nicht geladen werden',
        detail: this._loadError,
        degraded: !!readOnly,
        error_class: this._loadErrorClass || UI_ERROR_CLASS.UNKNOWN,
      });
    } else if (!hasSuggestions) {
      html = `<div class="empty">Keine aktiven Vorschlaege.</div>`;

      this._emitOnce('empty_list', UI_STATE_EVENTS.EMPTY_SHOWN, {
        scope: this._scope('list'),
        source: 'styx-suggestions-card',
        message: 'Keine aktiven Vorschlaege',
      });
    } else if (filterEmpty) {
      html = `
        <div class="state-empty">
          <div class="state-title">Keine Treffer fuer den Filter</div>
          <div class="state-msg">Passe den Filter an oder setze ihn zurueck.</div>
          <button class="retry" data-action="reset_filters">Filter zuruecksetzen</button>
        </div>`;

      this._emitOnce('empty_filter', UI_STATE_EVENTS.EMPTY_SHOWN, {
        scope: this._scope('list'),
        source: 'styx-suggestions-card',
        message: 'Keine Treffer fuer den Filter',
      });
    } else {
      html = `${filterBar}${banners}` + filtered
        .map((s) => {
          const id = this._getSuggestionId(s);
          const cat = String(s.category || 'default').toLowerCase();
          const catColor = CATEGORY_COLORS[cat] || CATEGORY_COLORS.default;
          const risk = String(s.risk || 'low').toLowerCase();
          const riskColor = RISK_COLORS[risk] || RISK_COLORS.low;

          const actionsDisabled = readOnly;
          const disabledAttr = actionsDisabled ? 'disabled' : '';
          const disabledTitle = actionsDisabled ? `${this._esc(this._readOnlyReason())}: Aktionen deaktiviert.` : '';

          const actions = this._config.show_actions
            ? `
          <div class="actions ${actionsDisabled ? 'disabled' : ''}">
            <button class="act-accept" ${disabledAttr} title="${disabledTitle}" data-id="${this._esc(id)}" data-action="accept">Annehmen</button>
            <button class="act-snooze" ${disabledAttr} title="${disabledTitle}" data-id="${this._esc(id)}" data-action="snooze">Spaeter</button>
            <button class="act-reject" ${disabledAttr} title="${disabledTitle}" data-id="${this._esc(id)}" data-action="reject">Ablehnen</button>
          </div>`
            : '';

          return `
          <div class="suggestion" data-id="${this._esc(id)}">
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
            <div class="sg-footer">
              <button class="details" type="button" data-id="${this._esc(id)}" data-action="detail-open">Details</button>
              ${actionsDisabled ? `<span class="ro" title="${disabledTitle}">Read-only</span>` : ''}
            </div>
            ${actions}
          </div>`;
        })
        .join('');
    }

    // Detail sub-screen (modal)
    let detailHtml = '';
    if (this._selectedId) {
      if (selectedMissing) {
        detailHtml = `
          <div class="detail-backdrop" data-action="detail-close">
            <div class="detail" role="dialog" aria-modal="true">
              <div class="detail-header">
                <div class="detail-title">Details</div>
                <button class="detail-close" type="button" data-action="detail-close" aria-label="Schliessen">×</button>
              </div>
              <div class="state-error">
                <div class="state-title">Vorschlag nicht gefunden</div>
                <div class="state-msg">Die Daten sind nicht mehr verfuegbar.</div>
                <button class="retry" data-action="retry">Erneut versuchen</button>
              </div>
            </div>
          </div>`;

        this._emitOnce('error_detail_missing', UI_STATE_EVENTS.ERROR_SHOWN, {
          scope: this._scope('detail'),
          source: 'styx-suggestions-card',
          message: 'Vorschlag nicht gefunden',
          detail: 'selected_missing',
          degraded: !!readOnly,
          error_class: UI_ERROR_CLASS.UNKNOWN,
        });
      } else if (selected) {
        const id = this._getSuggestionId(selected);

        const stepsRaw = selected.steps || selected.actions || selected.plan_steps || null;
        const steps = Array.isArray(stepsRaw)
          ? `<ul class="steps">${stepsRaw
              .map((st) => {
                if (st && typeof st === 'object') return `<li>${this._esc(st.title || st.name || JSON.stringify(st))}</li>`;
                return `<li>${this._esc(String(st))}</li>`;
              })
              .join('')}</ul>`
          : '';

        const rationale = selected.rationale || selected.reason || selected.why || '';

        const actionsDisabled = readOnly;
        const disabledAttr = actionsDisabled ? 'disabled' : '';
        const disabledTitle = actionsDisabled ? `${this._esc(this._readOnlyReason())}: Aktionen deaktiviert.` : '';

        const detailActions = this._config.show_actions
          ? `
            <div class="detail-actions ${actionsDisabled ? 'disabled' : ''}">
              <button class="act-accept" ${disabledAttr} title="${disabledTitle}" data-id="${this._esc(id)}" data-action="accept">Annehmen</button>
              <button class="act-snooze" ${disabledAttr} title="${disabledTitle}" data-id="${this._esc(id)}" data-action="snooze">Spaeter</button>
              <button class="act-reject" ${disabledAttr} title="${disabledTitle}" data-id="${this._esc(id)}" data-action="reject">Ablehnen</button>
            </div>`
          : '';

        detailHtml = `
          <div class="detail-backdrop" data-action="detail-close">
            <div class="detail" role="dialog" aria-modal="true">
              <div class="detail-header">
                <div class="detail-title">${this._esc(selected.title || selected.name || 'Vorschlag')}</div>
                <button class="detail-close" type="button" data-action="detail-close" aria-label="Schliessen">×</button>
              </div>

              ${readOnly ? `<div class="banner warn">${this._esc(this._readOnlyReason())} — Aktionen sind deaktiviert (Read-only).</div>` : ''}

              <div class="detail-body">
                <div class="detail-section">
                  <div class="detail-label">Beschreibung</div>
                  <div class="detail-value">${this._esc(selected.description || '')}</div>
                </div>

                ${rationale
                  ? `<div class="detail-section"><div class="detail-label">Warum</div><div class="detail-value">${this._esc(
                      String(rationale)
                    )}</div></div>`
                  : ''}

                ${steps
                  ? `<div class="detail-section"><div class="detail-label">Schritte</div>${steps}</div>`
                  : ''}

                <div class="detail-meta">
                  ${selected.category ? `<span class="tag">Kategorie: ${this._esc(String(selected.category))}</span>` : ''}
                  ${selected.risk ? `<span class="tag">Risiko: ${this._esc(String(selected.risk))}</span>` : ''}
                  ${selected.zone ? `<span class="tag">Zone: ${this._esc(String(selected.zone))}</span>` : ''}
                  ${selected.estimated_savings ? `<span class="tag">${this._esc(String(selected.estimated_savings))}</span>` : ''}
                </div>
              </div>

              ${detailActions}
            </div>
          </div>`;
      }
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

        .filters {
          display: flex;
          flex-wrap: wrap;
          gap: 6px;
          margin: 0 0 10px 0;
        }
        .chip {
          font-size: 11px;
          border-radius: 999px;
          padding: 4px 10px;
          border: 1px solid rgba(255,255,255,0.12);
          background: rgba(255,255,255,0.06);
          color: var(--primary-text-color, #e6eef6);
          cursor: pointer;
        }
        .chip.active {
          background: rgba(79,195,247,0.16);
          border-color: rgba(79,195,247,0.28);
          color: #4fc3f7;
          font-weight: 700;
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
        .sg-footer {
          display: flex;
          gap: 10px;
          align-items: center;
          justify-content: space-between;
          margin-top: 4px;
        }
        .details {
          padding: 4px 10px;
          border-radius: 8px;
          border: 1px solid rgba(255,255,255,0.14);
          background: rgba(255,255,255,0.04);
          color: var(--primary-text-color, #e6eef6);
          cursor: pointer;
          font-weight: 700;
          font-size: 11px;
        }
        .details:hover { background: rgba(255,255,255,0.08); }
        .ro {
          font-size: 11px;
          color: #ffb74d;
          opacity: 0.9;
          font-weight: 700;
        }

        .actions {
          display: flex;
          gap: 6px;
          margin-top: 8px;
        }
        .actions button {
          padding: 4px 12px;
          border-radius: 6px;
          border: none;
          font-size: 11px;
          cursor: pointer;
          font-weight: 700;
          transition: background 0.2s;
        }
        .actions button:disabled {
          cursor: not-allowed;
          opacity: 0.55;
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

        .state-error, .state-empty {
          text-align: center;
          padding: 16px 0;
        }
        .state-title {
          font-size: 13px;
          font-weight: 800;
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
          font-weight: 800;
          font-size: 12px;
        }
        button.retry:hover { background: rgba(79,195,247,0.2); }

        .empty {
          text-align: center;
          color: var(--secondary-text-color, #9fb1c3);
          padding: 24px 0;
          font-size: 13px;
        }

        .state-loading {
          display: flex;
          flex-direction: column;
          gap: 8px;
          padding: 8px 0;
        }
        .sk {
          height: 12px;
          border-radius: 8px;
          background: linear-gradient(90deg, rgba(255,255,255,0.05) 25%, rgba(255,255,255,0.10) 50%, rgba(255,255,255,0.05) 75%);
          background-size: 200% 100%;
          animation: shimmer 1.1s ease-in-out infinite;
        }
        .sk-1 { width: 92%; }
        .sk-2 { width: 75%; }
        .sk-3 { width: 88%; }
        @keyframes shimmer {
          0% { background-position: 200% 0; }
          100% { background-position: -200% 0; }
        }

        .detail-backdrop {
          position: fixed;
          inset: 0;
          background: rgba(0,0,0,0.55);
          z-index: 10000;
          display: flex;
          align-items: center;
          justify-content: center;
          padding: 16px;
        }
        .detail {
          width: min(560px, 100%);
          max-height: min(80vh, 720px);
          overflow: auto;
          background: rgba(20,20,40,0.98);
          border: 1px solid rgba(255,255,255,0.10);
          border-radius: 14px;
          padding: 14px;
          box-shadow: 0 12px 44px rgba(0,0,0,0.50);
        }
        .detail-header {
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: 12px;
          margin-bottom: 10px;
        }
        .detail-title {
          font-size: 14px;
          font-weight: 900;
        }
        .detail-close {
          width: 34px;
          height: 34px;
          border-radius: 10px;
          border: 1px solid rgba(255,255,255,0.12);
          background: rgba(255,255,255,0.04);
          color: var(--primary-text-color, #e6eef6);
          font-size: 18px;
          cursor: pointer;
          font-weight: 900;
        }
        .detail-body { padding: 8px 0; }
        .detail-section { margin-bottom: 12px; }
        .detail-label {
          font-size: 11px;
          text-transform: uppercase;
          letter-spacing: 0.06em;
          opacity: 0.65;
          margin-bottom: 4px;
        }
        .detail-value {
          font-size: 13px;
          color: var(--primary-text-color, #e6eef6);
          line-height: 1.4;
        }
        .detail-meta {
          display: flex;
          flex-wrap: wrap;
          gap: 6px;
          margin-top: 10px;
        }
        .steps {
          margin: 6px 0 0 16px;
          padding: 0;
          font-size: 12px;
          color: var(--secondary-text-color, #9fb1c3);
        }
        .detail-actions {
          display: flex;
          gap: 8px;
          justify-content: flex-end;
          padding-top: 10px;
          border-top: 1px solid rgba(255,255,255,0.08);
        }
        .detail-actions button:disabled { cursor: not-allowed; opacity: 0.55; }
      </style>

      <div class="card">
        <div class="header">
          <span class="title">${this._esc(this._config.title)}</span>
          <span class="count">${this._esc(countLabel)}</span>
        </div>
        ${html}
      </div>

      ${detailHtml}
    `;
  }

  _onClick(e) {
    const btn = e.target && e.target.closest ? e.target.closest('button') : null;
    if (!btn) {
      // Backdrop click
      const backdrop = e.target && e.target.classList && e.target.classList.contains('detail-backdrop') ? e.target : null;
      if (backdrop && backdrop.dataset && backdrop.dataset.action === 'detail-close') {
        this._action('', 'detail-close');
      }
      return;
    }

    const action = btn.dataset && btn.dataset.action ? btn.dataset.action : null;
    if (!action) return;

    if (action === 'set_filter') {
      const filter = btn.dataset.filter || 'all';
      this._filterCategory = filter;
      this._render();
      return;
    }

    const id = btn.dataset && btn.dataset.id ? btn.dataset.id : '';
    this._action(id, action);
  }
}

customElements.define('styx-suggestions-card', StyxSuggestionsCard);

window.customCards = window.customCards || [];
window.customCards.push({
  type: 'styx-suggestions-card',
  name: 'PilotSuite Styx Vorschlaege',
  description: 'AI-powered suggestion cards with governance actions',
});
