/**
 * PilotSuite Habitus Card v2.0.0
 *
 * Lovelace custom card displaying discovered behavioral patterns
 * from sensor.pilotsuite_habitus_rules_count and its attributes.
 */

const _HabitusBase = window.StyxCardBase || HTMLElement;

class StyxHabitusCard extends _HabitusBase {
  constructor() {
    super();
    if (!this.shadowRoot) {
      this.attachShadow({ mode: "open" });
      this._config = {};
    }
  }

  static getConfigElement() {
    return super.getConfigElement?.() || document.createElement("hui-generic-entity-row");
  }

  static getStubConfig() {
    return {
      entity: "sensor.pilotsuite_habitus_rules_count",
      title: "Erkannte Muster",
      max_rules: 5,
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
        placeholder: 'sensor.pilotsuite_habitus_rules_count',
        help: 'Primary habitus rules count sensor.',
      },
      {
        name: 'title',
        label: 'Title',
        selector: 'text',
        placeholder: 'Erkannte Muster',
        help: 'Optional card title shown in the header.',
      },
      {
        name: 'max_rules',
        label: 'Max rules',
        selector: 'text',
        placeholder: '5',
        help: 'Maximum number of rules to render.',
      },
    ];
  }

  static normalizeConfig(config = {}) {
    const defaults = this.getStubConfig();
    const normalize = window.styxNormalizeConfigWithSchema;
    const normalized = typeof normalize === 'function'
      ? normalize(config, this.getConfigForm(), defaults)
      : { ...defaults, ...(config || {}) };

    if (typeof normalized.title !== 'string') normalized.title = defaults.title;
    normalized.title = normalized.title.trim() || defaults.title;

    const parsedMax = Number.parseInt(normalized.max_rules, 10);
    normalized.max_rules = Number.isFinite(parsedMax) && parsedMax > 0 ? parsedMax : defaults.max_rules;
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

    const rawMax = config.max_rules;
    if (rawMax !== undefined) {
      const parsed = Number.parseInt(rawMax, 10);
      if (!Number.isFinite(parsed) || parsed <= 0) {
        errors.max_rules = 'max_rules must be a positive integer';
      }
    }

    return errors;
  }

  setConfig(config) {
    const normalized = this.constructor.normalizeConfig(config);
    const errors = this.constructor.validateConfig(normalized);
    const errorList = Object.values(errors || {});
    if (errorList.length > 0) throw new Error(errorList[0]);

    if (typeof super.setConfig === 'function') {
      super.setConfig(normalized);
    } else {
      this._config = normalized;
    }
  }

  set hass(hass) {
    this._hass = hass;
    this._render();
  }

  _resolveEntity() {
    if (!this._hass) return null;
    // Try configured entity first, then auto-detect
    if (this._config.entity) {
      const s = this._hass.states[this._config.entity];
      if (s) return s;
    }
    // Auto-detect with common naming patterns
    const candidates = [
      "sensor.pilotsuite_habitus_rules_count",
      "sensor.styx_hub_habitus_rules_count",
    ];
    // Also search all entities for matching unique_id pattern
    for (const eid of Object.keys(this._hass.states)) {
      if (eid.includes("habitus_rules_count")) candidates.unshift(eid);
    }
    for (const eid of candidates) {
      const s = this._hass.states[eid];
      if (s) return s;
    }
    return null;
  }

  getCardSize() {
    return 3;
  }

  _getRules() {
    const state = this._resolveEntity();
    if (!state) return [];

    const attrs = state.attributes || {};
    const rules = attrs.top_rules || attrs.rules || [];
    return rules.slice(0, this._config.max_rules);
  }

  _confidenceBadge(conf) {
    const pct = Math.round((conf || 0) * 100);
    let cls = "low";
    if (pct >= 80) cls = "high";
    else if (pct >= 50) cls = "mid";
    return `<span class="badge ${cls}">${pct}%</span>`;
  }

  _render() {
    const state = this._resolveEntity();
    const total = state ? parseInt(state.state, 10) || 0 : 0;
    const rules = this._getRules();

    let rulesHtml = "";
    if (rules.length === 0) {
      rulesHtml = `<div class="empty">Noch keine Muster erkannt.</div>`;
    } else {
      rulesHtml = rules
        .map((r) => {
          const ante = r.A || r.antecedent || "?";
          const cons = r.B || r.consequent || "?";
          const conf = r.confidence || 0;
          return `
            <div class="rule">
              <div class="pair">
                <span class="ante">${this._esc(ante)}</span>
                <span class="arrow">\u2192</span>
                <span class="cons">${this._esc(cons)}</span>
              </div>
              ${this._confidenceBadge(conf)}
            </div>`;
        })
        .join("");
    }

    const designTokens = typeof this._designTokens === 'function' ? this._designTokens() : '';

    this.shadowRoot.innerHTML = `
      <style>
        ${designTokens}
        :host { display: block; }
        ha-card { padding: var(--ps-sp-lg, 16px); }
        .header {
          display: flex; justify-content: space-between; align-items: center;
          margin-bottom: var(--ps-sp-md, 12px);
        }
        .title { font-size: var(--ps-fs-md, 0.9375rem); font-weight: 600; }
        .count {
          font-size: var(--ps-fs-sm, 0.8125rem);
          color: var(--ps-text-secondary, var(--secondary-text-color, #9e9eb8));
        }
        .rule {
          display: flex; justify-content: space-between; align-items: center;
          padding: var(--ps-sp-sm, 8px) 10px; margin-bottom: 6px;
          background: rgba(255,255,255,0.04); border-radius: var(--ps-radius-sm, 8px);
          transition: background var(--ps-transition, 0.2s ease);
        }
        .rule:hover { background: rgba(255,255,255,0.07); }
        .pair { display: flex; align-items: center; gap: 6px; flex: 1; min-width: 0; }
        .ante, .cons {
          white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
          max-width: 140px; font-size: var(--ps-fs-base, 0.875rem);
        }
        .arrow { color: var(--ps-accent, #4fc3f7); font-size: 14px; flex-shrink: 0; }
        .badge {
          font-size: var(--ps-fs-xs, 0.75rem); font-weight: 600;
          padding: 2px 8px; border-radius: 10px;
          flex-shrink: 0; margin-left: 8px;
        }
        .badge.high { background: rgba(129,199,132,0.15); color: var(--ps-green, #81c784); }
        .badge.mid  { background: rgba(255,183,77,0.15); color: var(--ps-orange, #ffb74d); }
        .badge.low  { background: rgba(239,83,80,0.15); color: var(--ps-red, #ef5350); }
        .empty {
          font-size: var(--ps-fs-base, 0.875rem);
          color: var(--ps-text-secondary, var(--secondary-text-color, #9e9eb8));
          padding: var(--ps-sp-md, 12px) 0; text-align: center;
        }
      </style>
      <ha-card>
        <div class="header">
          <span class="title">${this._esc(this._config.title || 'Erkannte Muster')}</span>
          <span class="count">${total} Regeln</span>
        </div>
        ${rulesHtml}
      </ha-card>`;
  }

  _esc(str) {
    if (typeof window.styxEsc === 'function') return window.styxEsc(str);
    const el = document.createElement("span");
    el.textContent = str;
    return el.innerHTML;
  }
}

if (typeof registerStyxCard === 'function') {
  registerStyxCard("styx-habitus-card", StyxHabitusCard, {
    name: "PilotSuite Erkannte Muster",
    description: "Zeigt erkannte Verhaltensmuster mit Konfidenz-Badges.",
  });
} else {
  customElements.define("styx-habitus-card", StyxHabitusCard);
  window.customCards = window.customCards || [];
  window.customCards.push({
    type: "styx-habitus-card",
    name: "PilotSuite Erkannte Muster",
    description: "Zeigt erkannte Verhaltensmuster mit Konfidenz-Badges.",
    preview: true,
  });
}
