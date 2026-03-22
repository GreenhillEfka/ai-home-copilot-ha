/**
 * PilotSuite Styx Suggestions Card v1.1.0
 *
 * Lovelace custom card displaying AI-generated suggestions
 * with accept/snooze/reject governance actions.
 *
 * PS-UX-015 scope:
 * - Suggestions list/detail states: loading/empty/error/offline-read-only
 * - Filter empty-case with CTA "Filter zurücksetzen"
 * - Actions disabled when offline (stale) or auth missing
 * - Telemetry hooks via ui_state_* + ui_global_degraded_on/off events
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
  low: 'var(--ps-green, #81c784)',
  medium: 'var(--ps-orange, #ffb74d)',
  high: 'var(--ps-red, #ef5350)',
};

// Use shared STYX_UI_EVENTS from styx-card-base.js if available.
const UI_TELEMETRY_EVENTS_SUG = window.STYX_UI_EVENTS || Object.freeze({
  LOADING_SHOWN: 'ui_state_loading_shown',
  EMPTY_SHOWN: 'ui_state_empty_shown',
  ERROR_SHOWN: 'ui_state_error_shown',
  GLOBAL_DEGRADED_ON: 'ui_global_degraded_on',
  GLOBAL_DEGRADED_OFF: 'ui_global_degraded_off',
  RETRY_CLICKED: 'ui_state_retry_clicked',
  RETRY_SUCCEEDED: 'ui_state_retry_succeeded',
  RETRY_FAILED: 'ui_state_retry_failed',
});

const _SugBase = window.StyxCardBase || HTMLElement;

class StyxSuggestionsCard extends _SugBase {
  constructor() {
    super();
    if (!this.shadowRoot) this.attachShadow({ mode: 'open' });
    this._config = {};
    this._hass = null;
    this._suggestions = [];
    this._lastFetch = 0;
    this._loadError = null;
    this._stale = false;
    this._actionError = null;
    this._loading = false;
    this._selectedId = null;
    this._detailMissingNotifiedForId = null;
    this._focusTriggerEl = null;

    // PS-UX-015 additions
    this._filterText = '';
    this._uiState = null;           // loading|empty|error|loaded
    this._degraded = false;         // global degraded banner state
    this._lastRetryTs = 0;
    this._timers = [];

    // Esc key handler to close detail modal
    this._onKeyDown = (e) => {
      if (e.key === 'Escape') this._closeDetail();
    };
  }

  disconnectedCallback() {
    super.disconnectedCallback?.();
    this._timers.forEach(t => clearTimeout(t));
    this._timers = [];
  }

  static getConfigElement() {
    return document.createElement('hui-generic-entity-row');
  }

  static getStubConfig() {
    return {
      title: 'Vorschläge',
      max_suggestions: 10,
      show_actions: true,
    };
  }

  setConfig(config) {
    this._config = {
      title: config.title || 'KI-Vorschläge',
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

  _emitUi(eventKeyOrName, detail = {}) {
    const payload = {
      ...detail,
      emittedAt: new Date().toISOString(),
    };

    try {
      // Prefer shared UiState.emit() if present (handles enum keys + validation).
      if (window.UiState && typeof window.UiState.emit === 'function') {
        window.UiState.emit(eventKeyOrName, payload);
        return;
      }

      const resolvedName = UI_TELEMETRY_EVENTS_SUG[eventKeyOrName] || eventKeyOrName;
      window.dispatchEvent(new CustomEvent(resolvedName, { detail: payload }));
    } catch (_e) {
      // ignore
    }
  }

  _setUiState(state, meta = {}) {
    if (this._uiState === state) return;
    this._uiState = state;

    if (state === 'loading') this._emitUi('LOADING_SHOWN', { scope: 'suggestions', ...meta });
    if (state === 'empty') this._emitUi('EMPTY_SHOWN', { scope: 'suggestions', ...meta });
    if (state === 'error') this._emitUi('ERROR_SHOWN', { scope: 'suggestions', ...meta });
  }

  _setDegraded(enabled, meta = {}) {
    if (this._degraded === enabled) return;
    this._degraded = enabled;
    this._emitUi(enabled ? 'GLOBAL_DEGRADED_ON' : 'GLOBAL_DEGRADED_OFF', { scope: 'suggestions', ...meta });
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
    this._loading = true;
    this._setUiState('loading');

    // Keep current suggestions visible; but if we have none yet, show a loading state.
    if (!this._suggestions || this._suggestions.length === 0) this._render();

    const url = this._getCoreUrl();
    const ctrl = new AbortController();
    const timer = setTimeout(() => ctrl.abort(), 10000);
    this._timers.push(timer);

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
          this._loading = false;
          this._setDegraded(false, { reason: 'online' });

          // Retry telemetry: if we got here from a retry click recently, mark success.
          if (Date.now() - this._lastRetryTs < 20000) {
            this._emitUi('RETRY_SUCCEEDED', { scope: 'suggestions' });
          }

          this._render();
          return;
        }
      }

      // Non-OK or unexpected payload -> try sensor fallback
      this._loadError = `HTTP ${resp.status || 'Fehler'}`;
      this._stale = this._loadFromSensor();
      this._loading = false;
      this._setDegraded(true, { reason: 'core_unreachable' });

      if (Date.now() - this._lastRetryTs < 20000) {
        this._emitUi('RETRY_FAILED', { scope: 'suggestions', error: this._loadError });
      }

      this._render();
    } catch (e) {
      clearTimeout(timer);
      this._loadError = e && e.name === 'AbortError' ? 'Zeitüberschreitung' : 'Verbindungsfehler';
      this._stale = this._loadFromSensor();
      this._loading = false;
      this._setDegraded(true, { reason: this._loadError });

      if (Date.now() - this._lastRetryTs < 20000) {
        this._emitUi('RETRY_FAILED', { scope: 'suggestions', error: this._loadError });
      }

      this._render();
    }
  }

  async _action(id, action) {
    if (action === 'retry') {
      this._lastRetryTs = Date.now();
      this._emitUi('RETRY_CLICKED', { scope: 'suggestions' });
      this._loadSuggestions();
      return;
    }

    if (action === 'detail-close') {
      this._closeDetail();
      return;
    }

    // Non-mutating actions: detail, reset_filter
    if (action === 'detail') {
      this._openDetail(id);
      return;
    }
    if (action === 'reset_filter') {
      this._filterText = '';
      this._render();
      return;
    }

    // Offline read-only: do not allow mutating actions.
    if (this._stale) {
      this._actionError = 'Offline — Aktion ist deaktiviert.';
      this._render();
      return;
    }

    // Auth missing: disable actions.
    if (!this._getToken()) {
      this._actionError = 'Authentifizierung fehlt — Aktion ist deaktiviert.';
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
    } catch (_e) {
      this._actionError = 'Aktion fehlgeschlagen';
      this._render();
    }
  }

  _esc(s) {
    if (typeof window.styxEsc === 'function') return window.styxEsc(s);
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

  _openDetail(id) {
    if (!id) return;
    // Save the currently focused/active element for focus restore on close
    this._focusTriggerEl = this.shadowRoot.activeElement || document.activeElement;
    this._selectedId = id;
    this._detailMissingNotifiedForId = null;
    document.addEventListener('keydown', this._onKeyDown);
    this._render();
    // Focus the close button inside the modal for focus trap
    requestAnimationFrame(() => {
      const closeBtn = this.shadowRoot.querySelector('button.detail-close');
      if (closeBtn) closeBtn.focus();
    });
  }

  _closeDetail() {
    document.removeEventListener('keydown', this._onKeyDown);
    const triggerEl = this._focusTriggerEl;
    this._selectedId = null;
    this._detailMissingNotifiedForId = null;
    this._focusTriggerEl = null;
    this._render();
    // Restore focus to the element that opened the modal
    if (triggerEl && typeof triggerEl.focus === 'function') {
      requestAnimationFrame(() => triggerEl.focus());
    }
  }

  _getSelectedSuggestion() {
    if (!this._selectedId) return null;
    return (this._suggestions || []).find(s => this._getSuggestionId(s) === this._selectedId) || null;
  }

  _render() {
    const suggestions = this._suggestions || [];
    const hasSuggestions = suggestions.length > 0;

    const filterText = String(this._filterText || '').trim().toLowerCase();
    const filtered = filterText
      ? suggestions.filter(s => {
          const t = String(s.title || s.name || '').toLowerCase();
          const d = String(s.description || '').toLowerCase();
          const c = String(s.category || '').toLowerCase();
          const z = String(s.zone || '').toLowerCase();
          return (t + ' ' + d + ' ' + c + ' ' + z).includes(filterText);
        })
      : suggestions;

    const selected = this._getSelectedSuggestion();
    const selectedMissing = Boolean(this._selectedId && !selected);
    if (selectedMissing) {
      // Avoid blank views: keep a dedicated detail empty/error state.
      this._actionError = this._actionError || 'Detailansicht nicht verfügbar (Vorschlag fehlt oder wurde aktualisiert).';
    }

    const showStaleBanner = this._stale || (this._loadError && hasSuggestions);

    const countLabelBase = this._stale ? `${suggestions.length} letzte` : `${suggestions.length} aktiv`;
    const countLabel = filterText ? `${filtered.length}/${countLabelBase}` : countLabelBase;

    const actionsDisabledGlobal = this._stale || !this._getToken();

    const banners = `
      ${this._actionError ? `<div class="banner err">${this._esc(this._actionError)}</div>` : ''}
      ${showStaleBanner ? `<div class="banner warn">${this._esc(this._loadError || 'Offline')} — letzte bekannte Daten.</div>` : ''}
      ${(!this._stale && !this._getToken()) ? `<div class="banner warn">Kein Token — Aktionen sind deaktiviert.</div>` : ''}
    `;

    let html = '';

    if (this._loading && !hasSuggestions && !this._loadError) {
      this._setUiState('loading');
      html = `
        <div class="state-loading" aria-label="Lade Vorschläge">
          <div class="sk sk-1"></div>
          <div class="sk sk-2"></div>
          <div class="sk sk-3"></div>
        </div>`;
    } else if (this._loadError && !hasSuggestions) {
      const errClass = String(this._loadError || '').includes('401') || String(this._loadError || '').includes('403') ? 'AUTH' : 'NETWORK';
      this._setUiState('error', { error_class: errClass, error: this._loadError });
      html = `
        <div class="state-error">
          <div class="state-title">Vorschläge konnten nicht geladen werden</div>
          <div class="state-msg">${this._esc(this._loadError)}</div>
          <button class="retry" data-action="retry">Erneut versuchen</button>
        </div>`;
    } else if (!hasSuggestions) {
      this._setUiState('empty', { reason: 'no_suggestions' });
      html = '<div class="empty">Keine aktiven Vorschläge.</div>';
    } else if (filtered.length === 0) {
      this._setUiState('empty', { reason: 'filter_empty' });
      html = `
        <div class="empty">Keine Treffer für den Filter.</div>
        <div style="text-align:center;margin-top:8px;">
          <button class="retry" data-action="reset_filter">Filter zurücksetzen</button>
        </div>`;
    } else {
      this._setUiState('loaded', { total: suggestions.length, filtered: filtered.length });
      html = `${banners}` + filtered.map(s => {
        const id = this._getSuggestionId(s);
        const cat = (s.category || 'default').toLowerCase();
        const catColor = CATEGORY_COLORS[cat] || CATEGORY_COLORS.default;
        const risk = (s.risk || 'low').toLowerCase();
        const riskColor = RISK_COLORS[risk] || RISK_COLORS.low;

        const actions = this._config.show_actions ? `
          <div class="actions ${actionsDisabledGlobal ? 'disabled' : ''}">
            <button class="act-accept" data-id="${this._esc(id)}" data-action="accept" ${actionsDisabledGlobal ? 'disabled' : ''}>Annehmen</button>
            <button class="act-snooze" data-id="${this._esc(id)}" data-action="snooze" ${actionsDisabledGlobal ? 'disabled' : ''}>Später</button>
            <button class="act-reject" data-id="${this._esc(id)}" data-action="reject" ${actionsDisabledGlobal ? 'disabled' : ''}>Ablehnen</button>
          </div>` : '';

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
              ${s.estimated_savings ? `<span class="tag" style="background:rgba(129,199,132,0.12);color:var(--ps-green, #81c784);border:1px solid rgba(129,199,132,0.25)">${this._esc(s.estimated_savings)}</span>` : ''}
            </div>
            <div class="sg-footer">
              <button class="details" data-id="${this._esc(id)}" data-action="detail">Details</button>
              ${actionsDisabledGlobal ? `<span class="ro">Nur Lesen</span>` : ''}
            </div>
            ${actions}
          </div>`;
      }).join('');
    }

    let detailHtml = '';

    if (selectedMissing) {
      const missingId = this._selectedId;
      const eventKey = hasSuggestions ? 'ERROR_SHOWN' : 'EMPTY_SHOWN';
      const reason = hasSuggestions ? 'missing_item' : 'no_data';

      if (this._detailMissingNotifiedForId !== missingId) {
        this._detailMissingNotifiedForId = missingId;
        this._emitUi(eventKey, {
          scope: 'suggestion_detail',
          reason,
          selected_id: missingId,
          stale: Boolean(this._stale),
          load_error: this._loadError || null,
          list_count: suggestions.length,
        });
      }

      detailHtml = `
        <div class="detail-backdrop">
          <div class="detail" role="dialog" aria-modal="true">
            <div class="detail-header">
              <div class="detail-title">Vorschlag nicht verfügbar</div>
              <button class="detail-close" data-action="detail-close" aria-label="Schliessen">×</button>
            </div>
            <div class="detail-body">
              <div class="state-error">
                <div class="state-title">Detailansicht nicht verfügbar</div>
                <div class="state-msg">Der Vorschlag ist nicht mehr in der Liste (z. B. nach Refresh oder Aktion).</div>
                <button class="retry" data-action="detail-close">Zurück zur Liste</button>
              </div>
            </div>
          </div>
        </div>`;
    } else if (selected) {
      const id = this._getSuggestionId(selected);

      const descRaw = selected.description || selected.summary || '';
      const descText = (descRaw && typeof descRaw === 'object') ? JSON.stringify(descRaw) : String(descRaw || '');
      const descValue = descText.trim()
        ? `<div class="detail-value">${this._esc(descText)}</div>`
        : `<div class="detail-value placeholder">Keine Beschreibung verfügbar.</div>`;

      const rationaleRaw = selected.rationale || selected.reason || selected.why || '';
      const rationaleText = (rationaleRaw && typeof rationaleRaw === 'object') ? JSON.stringify(rationaleRaw) : String(rationaleRaw || '');
      const rationaleValue = rationaleText.trim()
        ? `<div class="detail-value">${this._esc(rationaleText)}</div>`
        : `<div class="detail-value placeholder">Keine Begründung verfügbar.</div>`;

      const stepsRaw = selected.steps || selected.actions || selected.plan_steps || null;
      const stepsArr = Array.isArray(stepsRaw) ? stepsRaw : null;
      const stepsValue = (stepsArr && stepsArr.length)
        ? `<ul class="steps">${stepsArr.map(st => {
            if (st && typeof st === 'object') return `<li>${this._esc(st.title || st.name || JSON.stringify(st))}</li>`;
            return `<li>${this._esc(String(st))}</li>`;
          }).join('')}</ul>`
        : `<div class="detail-value placeholder">Keine Schritte angegeben.</div>`;

      const detailsObj = selected.details || selected.payload || null;
      const details = (detailsObj && typeof detailsObj === 'object')
        ? `<pre class="code">${this._esc(JSON.stringify(detailsObj, null, 2))}</pre>`
        : (detailsObj ? `<div class="detail-value">${this._esc(String(detailsObj))}</div>` : '');

      let readOnlyBanner = '';
      if (actionsDisabledGlobal) {
        const roReason = this._stale
          ? `${this._loadError ? `${this._loadError} — ` : ''}letzte bekannte Daten.`
          : (!this._getToken() ? 'Kein Token.' : '');
        readOnlyBanner = `<div class="banner warn">Nur Lesen — ${this._esc(roReason)} Aktionen sind deaktiviert.</div>`;
      }

      const detailActions = this._config.show_actions ? `
        <div class="detail-actions ${actionsDisabledGlobal ? 'disabled' : ''}">
          <button class="act-accept" data-id="${this._esc(id)}" data-action="accept" ${actionsDisabledGlobal ? 'disabled' : ''}>Annehmen</button>
          <button class="act-snooze" data-id="${this._esc(id)}" data-action="snooze" ${actionsDisabledGlobal ? 'disabled' : ''}>Später</button>
          <button class="act-reject" data-id="${this._esc(id)}" data-action="reject" ${actionsDisabledGlobal ? 'disabled' : ''}>Ablehnen</button>
        </div>` : '';

      detailHtml = `
        <div class="detail-backdrop">
          <div class="detail" role="dialog" aria-modal="true">
            <div class="detail-header">
              <div class="detail-title">${this._esc(selected.title || selected.name || 'Vorschlag')}</div>
              <button class="detail-close" data-action="detail-close" aria-label="Schliessen">×</button>
            </div>

            ${readOnlyBanner}

            <div class="detail-body">
              <div class="detail-section">
                <div class="detail-label">Beschreibung</div>
                ${descValue}
              </div>

              <div class="detail-section">
                <div class="detail-label">Warum</div>
                ${rationaleValue}
              </div>

              <div class="detail-section">
                <div class="detail-label">Schritte</div>
                ${stepsValue}
              </div>

              ${(selected.pattern || selected.lift || selected.confidence) ? `
              <details class="reasoning-expander">
                <summary>Begründung</summary>
                <div class="reasoning-grid">
                  ${selected.confidence != null ? `
                  <div class="reasoning-item">
                    <span class="reasoning-label">Confidence</span>
                    <span class="reasoning-value">${this._confidenceBadge(selected.confidence)}</span>
                  </div>` : ''}
                  ${selected.pattern ? `
                  <div class="reasoning-item">
                    <span class="reasoning-label">Pattern</span>
                    <code class="reasoning-code">${this._esc(String(selected.pattern))}</code>
                  </div>` : ''}
                  ${selected.lift != null ? `
                  <div class="reasoning-item">
                    <span class="reasoning-label">Lift</span>
                    <span class="reasoning-value">${Number(selected.lift).toFixed(2)}×</span>
                  </div>` : ''}
                </div>
              </details>` : ''}

              ${details ? `
                <div class="detail-section">
                  <div class="detail-label">Details</div>
                  ${details}
                </div>` : ''}

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

    this.shadowRoot.innerHTML = `
      <style>
        ${typeof this._designTokens === 'function' ? this._designTokens() : ''}
        :host { display: block; }
        .card {
          background: var(--ps-bg, var(--card-background-color, #1a1a2e));
          border-radius: var(--ps-radius, var(--ha-card-border-radius, 12px));
          padding: 16px;
          color: var(--ps-text, var(--primary-text-color, #e6eef6));
          font-family: var(--paper-font-body1_-_font-family, system-ui, sans-serif);
        }
        .header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 10px;
        }
        .title { font-size: 16px; font-weight: 600; }
        .count {
          font-size: 12px;
          padding: 2px 8px;
          border-radius: 10px;
          background: rgba(79, 195, 247, 0.15);
          color: var(--ps-accent, #4fc3f7);
        }
        .toolbar {
          display: flex;
          gap: 8px;
          align-items: center;
          margin-bottom: 12px;
        }
        .filter {
          flex: 1;
          padding: 8px 10px;
          border-radius: var(--ps-radius-sm, 10px);
          border: 1px solid var(--ps-border, rgba(255,255,255,0.12));
          background: var(--ps-surface, rgba(255,255,255,0.04));
          color: var(--ps-text, var(--primary-text-color, #e6eef6));
          font-size: 12px;
        }
        .reset {
          padding: 8px 10px;
          border-radius: var(--ps-radius-sm, 10px);
          border: 1px solid var(--ps-border, rgba(255,255,255,0.14));
          background: rgba(79,195,247,0.10);
          color: var(--ps-accent, #4fc3f7);
          cursor: pointer;
          font-weight: 700;
          font-size: 12px;
          white-space: nowrap;
        }
        .reset:hover { background: rgba(79,195,247,0.18); }
        .reset:disabled { opacity: 0.55; cursor: default; }

        .suggestion {
          padding: 12px;
          margin-bottom: 8px;
          background: var(--ps-surface, rgba(255,255,255,0.04));
          border-radius: var(--ps-radius-sm, 10px);
          border: 1px solid var(--ps-border, rgba(255,255,255,0.06));
        }
        .sg-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 6px;
        }
        .sg-title { font-size: 14px; font-weight: 600; }
        .badge {
          font-size: 0.75rem;
          padding: 2px 8px;
          border-radius: var(--ps-radius-sm, 8px);
          font-weight: 600;
        }
        .conf-high { background: rgba(129,199,132,0.2); color: var(--ps-green, #81c784); }
        .conf-mid { background: rgba(255,183,77,0.2); color: var(--ps-orange, #ffb74d); }
        .conf-low { background: rgba(158,158,158,0.2); color: var(--ps-text-secondary, #9e9e9e); }
        .sg-desc {
          font-size: 12px;
          color: var(--ps-text-secondary, var(--secondary-text-color, #9fb1c3));
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
          font-size: 0.75rem;
          padding: 2px 8px;
          border-radius: 6px;
          background: rgba(255,255,255,0.06);
          color: var(--ps-text-secondary, var(--secondary-text-color, #9fb1c3));
          border: 1px solid var(--ps-border, rgba(255,255,255,0.08));
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
          font-size: 0.75rem;
          cursor: pointer;
          font-weight: 600;
          transition: background var(--ps-transition, 0.2s ease);
        }
        .act-accept {
          background: rgba(129,199,132,0.2);
          color: var(--ps-green, #81c784);
        }
        .act-accept:hover { background: rgba(129,199,132,0.35); }
        .act-snooze {
          background: rgba(255,183,77,0.2);
          color: var(--ps-orange, #ffb74d);
        }
        .act-snooze:hover { background: rgba(255,183,77,0.35); }
        .act-reject {
          background: rgba(239,83,80,0.15);
          color: var(--ps-red, #ef5350);
        }
        .act-reject:hover { background: rgba(239,83,80,0.3); }
        .actions.disabled button,
        .detail-actions.disabled button {
          opacity: 0.55;
        }

        .banner {
          padding: 8px 10px;
          margin: 10px 0 10px 0;
          border-radius: var(--ps-radius-sm, 10px);
          font-size: 12px;
          border: 1px solid var(--ps-border, rgba(255,255,255,0.08));
        }
        .banner.warn { background: rgba(255,183,77,0.12); color: var(--ps-orange, #ffb74d); border-color: rgba(255,183,77,0.25); }
        .banner.err { background: rgba(239,83,80,0.12); color: var(--ps-red, #ef5350); border-color: rgba(239,83,80,0.25); }

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
          color: var(--ps-text-secondary, var(--secondary-text-color, #9fb1c3));
          margin-bottom: 10px;
        }
        button.retry {
          padding: 6px 12px;
          border-radius: var(--ps-radius-sm, 8px);
          border: 1px solid var(--ps-border, rgba(255,255,255,0.14));
          background: rgba(79,195,247,0.12);
          color: var(--ps-accent, #4fc3f7);
          cursor: pointer;
          font-weight: 700;
          font-size: 12px;
        }
        button.retry:hover { background: rgba(79,195,247,0.2); }
        .empty {
          text-align: center;
          color: var(--ps-text-secondary, var(--secondary-text-color, #9fb1c3));
          padding: 24px 0;
          font-size: 13px;
        }

        .state-loading {
          display: flex;
          flex-direction: column;
          gap: 8px;
          padding: 8px 0 2px 0;
        }
        .sk {
          height: 14px;
          border-radius: var(--ps-radius-sm, 10px);
          background: rgba(255,255,255,0.06);
          position: relative;
          overflow: hidden;
        }
        .sk::after {
          content: '';
          position: absolute;
          top: 0;
          left: -40%;
          width: 40%;
          height: 100%;
          background: linear-gradient(90deg, transparent, rgba(255,255,255,0.12), transparent);
          animation: shimmer 1.2s infinite;
        }
        .sk-1 { width: 92%; }
        .sk-2 { width: 78%; }
        .sk-3 { width: 86%; }
        @keyframes shimmer {
          0% { left: -40%; }
          100% { left: 100%; }
        }

        .sg-footer {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-top: 6px;
        }
        button.details {
          padding: 4px 10px;
          border-radius: var(--ps-radius-sm, 8px);
          border: 1px solid var(--ps-border, rgba(255,255,255,0.14));
          background: rgba(79,195,247,0.10);
          color: var(--ps-accent, #4fc3f7);
          cursor: pointer;
          font-weight: 700;
          font-size: 0.75rem;
        }
        button.details:hover { background: rgba(79,195,247,0.18); }
        .ro {
          font-size: 0.75rem;
          color: var(--ps-orange, #ffb74d);
          opacity: 0.9;
        }

        .detail-backdrop {
          position: fixed;
          inset: 0;
          background: rgba(0,0,0,0.55);
          display: flex;
          align-items: flex-end;
          justify-content: center;
          padding: 18px;
          z-index: 9999;
        }
        .detail {
          width: min(680px, 100%);
          max-height: 82vh;
          overflow: auto;
          background: var(--ps-bg, var(--card-background-color, #1a1a2e));
          border-radius: var(--ps-radius, 14px);
          border: 1px solid var(--ps-border, rgba(255,255,255,0.10));
          padding: 14px;
          box-shadow: 0 10px 30px rgba(0,0,0,0.35);
        }
        .detail-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 10px;
        }
        .detail-title {
          font-size: 15px;
          font-weight: 800;
        }
        button.detail-close {
          width: 34px;
          height: 34px;
          border-radius: var(--ps-radius-sm, 10px);
          border: 1px solid var(--ps-border, rgba(255,255,255,0.14));
          background: var(--ps-surface, rgba(255,255,255,0.06));
          color: var(--ps-text, var(--primary-text-color, #e6eef6));
          cursor: pointer;
          font-size: 18px;
          font-weight: 900;
          line-height: 1;
        }
        button.detail-close:hover { background: rgba(255,255,255,0.10); }
        .detail-body { padding-top: 4px; }
        .detail-section { margin-bottom: 12px; }
        .detail-label {
          font-size: 0.75rem;
          text-transform: uppercase;
          letter-spacing: 0.06em;
          color: var(--ps-text-secondary, var(--secondary-text-color, #9fb1c3));
          margin-bottom: 4px;
        }
        .detail-value {
          font-size: 12px;
          line-height: 1.45;
          color: var(--ps-text, var(--primary-text-color, #e6eef6));
        }
        .detail-value.placeholder {
          color: var(--ps-text-secondary, var(--secondary-text-color, #9fb1c3));
          font-style: italic;
        }
        .detail-meta {
          display: flex;
          flex-wrap: wrap;
          gap: 6px;
          margin-top: 8px;
        }
        .detail-actions {
          display: flex;
          gap: 6px;
          margin-top: 10px;
          justify-content: flex-end;
        }
        .steps {
          margin: 0;
          padding-left: 18px;
          color: var(--ps-text, var(--primary-text-color, #e6eef6));
          font-size: 12px;
        }
        .steps li { margin: 3px 0; }
        pre.code {
          margin: 0;
          background: rgba(0,0,0,0.25);
          padding: 10px;
          border-radius: var(--ps-radius-sm, 10px);
          overflow: auto;
          font-size: 0.75rem;
          border: 1px solid var(--ps-border, rgba(255,255,255,0.08));
        }
        .reasoning-expander {
          margin-top: 8px;
          border: 1px solid var(--ps-border, rgba(255,255,255,0.12));
          border-radius: var(--ps-radius-sm, 10px);
          overflow: hidden;
        }
        .reasoning-expander summary {
          padding: 8px 12px;
          cursor: pointer;
          font-size: 0.8rem;
          font-weight: 600;
          color: var(--ps-accent, #4fc3f7);
          user-select: none;
          background: rgba(79,195,247,0.08);
        }
        .reasoning-expander summary:hover {
          background: rgba(79,195,247,0.14);
        }
        .reasoning-grid {
          display: flex;
          flex-direction: column;
          gap: 6px;
          padding: 10px 12px;
        }
        .reasoning-item {
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: 8px;
        }
        .reasoning-label {
          font-size: 0.75rem;
          color: var(--ps-text-secondary, var(--secondary-text-color, #9fb1c3));
        }
        .reasoning-code {
          font-size: 0.7rem;
          background: rgba(0,0,0,0.25);
          padding: 2px 6px;
          border-radius: 4px;
          color: var(--ps-accent, #4fc3f7);
          word-break: break-all;
        }
      </style>
      <div class="card">
        <div class="header">
          <span class="title">${this._esc(this._config.title)}</span>
          <span class="count">${this._esc(countLabel)}</span>
        </div>
        <div class="toolbar">
          <input class="filter" type="search" placeholder="Filtern…" value="${this._esc(this._filterText)}" data-action="filter" aria-label="Vorschläge filtern" />
          <button class="reset" data-action="reset_filter" ${filterText ? '' : 'disabled'}>Filter zurücksetzen</button>
        </div>
        ${html}
        ${detailHtml}
      </div>`;

    const card = this.shadowRoot.querySelector('.card');
    if (card) {
      card.addEventListener('click', (e) => {
        // Close modal when clicking on backdrop.
        if (e.target && e.target.classList && e.target.classList.contains('detail-backdrop')) {
          this._closeDetail();
          return;
        }

        const closeBtn = e.target.closest('button.detail-close');
        if (closeBtn) {
          this._closeDetail();
          return;
        }

        const btn = e.target.closest('.actions button, .detail-actions button, button.retry, button.details, button.reset');
        if (btn) {
          const action = btn.dataset.action || 'retry';
          const id = btn.dataset.id || '';
          if (btn.disabled || btn.closest('.actions.disabled') || btn.closest('.detail-actions.disabled')) {
            this._actionError = 'Aktion derzeit deaktiviert.';
            this._render();
            return;
          }
          this._action(id, action);
          return;
        }

        const sg = e.target.closest('.suggestion');
        if (sg && sg.dataset && sg.dataset.id) {
          this._openDetail(sg.dataset.id);
        }
      });

      card.addEventListener('input', (e) => {
        const el = e.target;
        if (!el || !el.dataset || el.dataset.action !== 'filter') return;
        this._filterText = String(el.value || '');
        this._render();
      });
    }
  }
}

if (typeof registerStyxCard === 'function') {
  registerStyxCard('styx-suggestions-card', StyxSuggestionsCard, {
    name: 'PilotSuite KI-Vorschlaege',
    description: 'KI-gesteuerte Vorschlaege mit Governance-Aktionen',
  });
} else {
  customElements.define('styx-suggestions-card', StyxSuggestionsCard);
  window.customCards = window.customCards || [];
  window.customCards.push({
    type: 'styx-suggestions-card',
    name: 'PilotSuite KI-Vorschlaege',
    description: 'KI-gesteuerte Vorschlaege mit Governance-Aktionen',
  });
}
