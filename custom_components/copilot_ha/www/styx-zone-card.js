/**
 * PilotSuite Zone Dashboard Card v1.0.0
 *
 * Lovelace custom card showing zone status, mood, neuron activity,
 * and quick actions. Reads from sensor.pilotsuite_habitus_zones and
 * sensor.pilotsuite_zone_modes entities.
 *
 * Features:
 * - Zone Status (active/inactive indicator)
 * - Mood gauges (Comfort, Joy, Frugality per zone)
 * - Neuron Activity visualization
 * - Quick Actions (toggle, scene selection)
 */

const ZONE_ICON_MAP = {
  living_room: 'mdi:sofa',
  bedroom: 'mdi:bed',
  kitchen: 'mdi:chef-hat',
  bathroom: 'mdi:shower',
  office: 'mdi:desk',
  outdoor: 'mdi:tree',
  default: 'mdi:floor-plan'
};

const MOOD_GAUGE_DEFS = [
  { key: 'comfort', label: 'Comfort', start: '#2196f3', end: '#4caf50' },
  { key: 'joy', label: 'Joy', start: '#ff9800', end: '#f9d71c' },
  { key: 'frugality', label: 'Frugality', start: '#9c27b0', end: '#00bcd4' },
];

const MODE_ICONS = {
  party: 'mdi:party-popper',
  kids_sleep: 'mdi:baby-face-outline',
  movie: 'mdi:movie-open',
  guest: 'mdi:account-group',
  focus: 'mdi:head-lightbulb',
  away: 'mdi:home-export-outline',
  night: 'mdi:weather-night',
  romantic: 'mdi:heart',
  relaxing: 'mdi:meditation',
  focus_work: 'mdi:briefcase',
};

class StyxZoneCard extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: 'open' });
    this._config = {};
    this._hass = null;
    this._selectedZone = null;
  }

  static getConfigElement() {
    return document.createElement('hui-generic-entity-row');
  }

  static getStubConfig() {
    return {
      entity: 'sensor.pilotsuite_habitus_zones',
      show_mood: true,
      show_neuron_activity: true,
      show_quick_actions: true,
    };
  }

  setConfig(config) {
    if (!config.entity) {
      throw new Error('Please define an entity');
    }
    this._config = {
      ...config,
      show_mood: config.show_mood !== false,
      show_neuron_activity: config.show_neuron_activity !== false,
      show_quick_actions: config.show_quick_actions !== false,
    };
  }

  set hass(hass) {
    this._hass = hass;
    this._render();
  }

  getCardSize() {
    return 4;
  }

  _getZoneIcon(zoneId) {
    const key = zoneId.toLowerCase().replace(/[^a-z_]/g, '_');
    return ZONE_ICON_MAP[key] || ZONE_ICON_MAP.default;
  }

  _getModeIcon(modeId) {
    return MODE_ICONS[modeId] || 'mdi:toggle-switch';
  }

  _getZonesData() {
    if (!this._hass || !this._config.entity) return { zones: [], active_zones: 0 };

    const state = this._hass.states[this._config.entity];
    if (!state) return { zones: [], active_zones: 0 };

    const attrs = state.attributes || {};
    const zones = attrs.zones || [];

    return {
      zones: zones,
      total_zones: attrs.total_zones || zones.length,
      active_zones: attrs.active_zones || 0,
      modes: attrs.modes || {},
    };
  }

  _getMoodData(zoneId) {
    const prefix = `sensor.pilotsuite_mood_${zoneId}`;
    return MOOD_GAUGE_DEFS.map(def => {
      const entityId = `${prefix}_${def.key}`;
      const state = this._hass?.states[entityId];
      const parsed = state ? parseFloat(state.state) : null;
      const hasNumeric = Number.isFinite(parsed);

      return {
        ...def,
        entityId,
        value: hasNumeric ? Math.max(0, Math.min(100, parsed)) : null,
        available: Boolean(state) && hasNumeric,
      };
    });
  }

  _getNeuronActivity(zoneId) {
    const nodeEntity = this._hass?.states['sensor.pilotsuite_brain_graph_nodes'];
    if (!nodeEntity) {
      return {
        available: false,
        active: null,
        total: null,
        score: null,
      };
    }

    const nodes = Array.isArray(nodeEntity.attributes?.nodes) ? nodeEntity.attributes.nodes : [];
    const zoneNodes = nodes.filter(n => n.zone === zoneId || n.rooms?.includes(zoneId));

    return {
      available: true,
      active: zoneNodes.filter(n => n.state === 'on').length,
      total: zoneNodes.length,
      score: zoneNodes.length > 0
        ? zoneNodes.reduce((acc, n) => acc + (n.score || 0), 0) / zoneNodes.length
        : 0,
    };
  }

  _buildMissingTileValue(label, subtitle = '') {
    const subtitleHtml = subtitle ? `<div class="value-subtitle">${subtitle}</div>` : '';
    return `
      <div class="missing-value">
        <div class="value-na">n/a</div>
        <div class="value-title">${label}</div>
        ${subtitleHtml}
      </div>`;
  }

  _buildMoodGauge(mood) {
    if (!mood?.available) {
      return `<div class="mood-gauge mood-gauge-missing">${this._buildMissingTileValue(mood?.label || 'n/a')}</div>`;
    }

    return this._buildGaugeSvg(mood.value, mood.start, mood.end, mood.label);
  }

  _buildGaugeSvg(value, startColor, endColor, label, size = 70) {
    const cx = size / 2;
    const cy = size / 2;
    const r = size * 0.35;
    const circumference = 2 * Math.PI * r;
    const pct = Math.max(0, Math.min(100, value));
    const offset = circumference - (circumference * pct) / 100;
    const gradId = `zg_${label.toLowerCase()}_${Math.random().toString(36).substr(2, 9)}`;

    return `
      <svg viewBox="0 0 ${size} ${size}" class="mood-gauge">
        <defs>
          <linearGradient id="${gradId}" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stop-color="${startColor}"/>
            <stop offset="100%" stop-color="${endColor}"/>
          </linearGradient>
        </defs>
        <circle cx="${cx}" cy="${cy}" r="${r}" fill="none" stroke="#1e2a36" stroke-width="5"/>
        <circle cx="${cx}" cy="${cy}" r="${r}" fill="none" stroke="url(#${gradId})" stroke-width="5"
          stroke-dasharray="${circumference}" stroke-dashoffset="${offset}"
          stroke-linecap="round" transform="rotate(-90 ${cx} ${cy})"
          style="transition: stroke-dashoffset 0.5s ease;"/>
        <text x="${cx}" y="${cy - 2}" text-anchor="middle"
          fill="var(--primary-text-color, #e6eef6)" font-size="12" font-weight="600"
          font-family="system-ui,sans-serif">${Math.round(pct)}</text>
        <text x="${cx}" y="${cy + 10}" text-anchor="middle"
          fill="var(--secondary-text-color, #9fb1c3)" font-size="7"
          font-family="system-ui,sans-serif">${label}</text>
      </svg>`;
  }

  _buildNeuronBar(activity) {
    if (!activity || activity.available === false) {
      return `<div class="neuron-bar-container neuron-missing">${this._buildMissingTileValue('Neuronen', 'Sensordaten fehlen')}</div>`;
    }

    const { active, total, score } = activity;
    const pct = total > 0 ? (active / total) * 100 : 0;
    const scorePct = Math.max(0, Math.min(100, score * 100));

    return `
      <div class="neuron-bar-container">
        <div class="neuron-bar-label">
          <span class="mdi-icon">🧠</span>
          <span>Neuronen</span>
        </div>
        <div class="neuron-bar-track">
          <div class="neuron-bar-fill" style="width: ${pct}%"></div>
          <div class="neuron-score-marker" style="left: ${scorePct}%"></div>
        </div>
        <div class="neuron-bar-stats">
          <span>${active}/${total} aktiv</span>
          <span>Score: ${Math.round(scorePct)}%</span>
        </div>
      </div>
    `;
  }

  _buildZoneCard(zone) {
    const zoneId = zone.name?.toLowerCase().replace(/\s+/g, '_') || zone.zone_id || 'unknown';
    const isActive = zone.mode && zone.mode !== 'inactive';
    const hasMode = Boolean(zone.mode);
    const moodData = this._config.show_mood ? this._getMoodData(zoneId) : [];
    const neuronActivity = this._config.show_neuron_activity ? this._getNeuronActivity(zoneId) : null;
    const hasPartialData = moodData.some(m => m.available === false) ||
      (this._config.show_neuron_activity && (!neuronActivity || neuronActivity.available === false));

    const moodGauges = this._config.show_mood
      ? moodData.map(m => this._buildMoodGauge(m)).join('')
      : '';

    const neuronBar = this._config.show_neuron_activity && neuronActivity
      ? this._buildNeuronBar(neuronActivity)
      : '';

    const modeIcon = hasMode ? this._getModeIcon(zone.mode) : 'mdi:home';
    const modeLabel = zone.mode || 'inaktiv';

    return `
      <div class="zone-card ${isActive ? 'active' : 'inactive'} ${hasPartialData ? 'partial' : ''}" data-zone="${zoneId}">
        <div class="zone-header">
          <div class="zone-info">
            <span class="zone-icon mdi-icon">${this._getZoneIcon(zoneId)}</span>
            <span class="zone-name">${zone.name || zoneId}</span>
          </div>
          <div class="zone-status ${isActive ? 'active' : ''} ${hasPartialData ? 'partial' : ''}">
            <span class="status-dot"></span>
            <span class="status-text">${hasPartialData ? 'Teildaten' : (isActive ? 'Aktiv' : 'Inaktiv')}</span>
          </div>
        </div>

        ${hasPartialData ? '<div class="partial-badge">Teildaten</div>' : ''}

        ${isActive ? `
          <div class="zone-mode">
            <span class="mdi-icon">${modeIcon}</span>
            <span class="mode-label">${modeLabel}</span>
          </div>
        ` : ''}

        ${moodGauges ? `
          <div class="mood-gauges">
            ${moodGauges}
          </div>
        ` : ''}

        ${neuronBar}

        ${this._config.show_quick_actions ? `
          <div class="quick-actions">
            <button class="action-btn light-toggle" data-action="light" title="Licht">
              <span class="mdi-icon">💡</span>
            </button>
            <button class="action-btn scene-btn" data-action="scene" title="Szene">
              <span class="mdi-icon">🎬</span>
            </button>
            <button class="action-btn thermostat-btn" data-action="thermostat" title="Thermostat">
              <span class="mdi-icon">🌡️</span>
            </button>
          </div>
        ` : ''}
      </div>
    `;
  }

  _render() {
    const { zones, total_zones, active_zones } = this._getZonesData();
    const title = this._config.title || 'Zonen';

    const zoneCards = zones.length > 0
      ? zones.map(z => this._buildZoneCard(z)).join('')
      : '<div class="no-zones">Keine Zonen konfiguriert</div>';

    this.shadowRoot.innerHTML = `
      <style>
        :host { display: block; }
        .card {
          background: var(--card-background-color, #0a0e14);
          border-radius: var(--ha-card-border-radius, 12px);
          padding: 16px;
          color: var(--primary-text-color, #e6eef6);
          font-family: var(--paper-font-body1_-_font-family, system-ui, sans-serif);
        }
        .header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 16px;
          padding-bottom: 12px;
          border-bottom: 1px solid #263343;
        }
        .title {
          font-size: 18px;
          font-weight: 600;
        }
        .zone-count {
          font-size: 12px;
          color: var(--secondary-text-color, #9fb1c3);
        }
        .zone-count .active {
          color: #22c55e;
          font-weight: 600;
        }
        .zones-grid {
          display: grid;
          grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
          gap: 12px;
        }
        .zone-card {
          background: #0f1419;
          border-radius: 10px;
          padding: 14px;
          border: 1px solid #1e2a36;
          transition: all 0.2s ease;
        }
        .zone-card:hover {
          transform: translateY(-2px);
          box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
        }
        .zone-card.active {
          border-left: 3px solid #22c55e;
        }
        .zone-card.inactive {
          border-left: 3px solid #4b5563;
          opacity: 0.7;
        }
        .zone-card.partial {
          border-left: 3px solid #f59e0b;
        }
        .zone-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 10px;
        }
        .zone-info {
          display: flex;
          align-items: center;
          gap: 8px;
        }
        .zone-icon {
          font-size: 20px;
        }
        .zone-name {
          font-size: 14px;
          font-weight: 500;
        }
        .zone-status {
          display: flex;
          align-items: center;
          gap: 6px;
          font-size: 11px;
          color: #6b7280;
        }
        .zone-status.active {
          color: #22c55e;
        }
        .zone-status.partial {
          color: #f59e0b;
        }
        .status-dot {
          width: 8px;
          height: 8px;
          border-radius: 50%;
          background: #4b5563;
        }
        .zone-status.active .status-dot {
          background: #22c55e;
          box-shadow: 0 0 6px #22c55e;
        }
        .zone-status.partial .status-dot {
          background: #f59e0b;
          box-shadow: 0 0 6px #f59e0b;
        }
        .partial-badge {
          margin-bottom: 10px;
          font-size: 11px;
          color: #f59e0b;
          background: rgba(245, 158, 11, 0.12);
          border: 1px solid rgba(245, 158, 11, 0.4);
          border-radius: 999px;
          width: fit-content;
          padding: 4px 8px;
          text-transform: uppercase;
          letter-spacing: 0.2px;
        }
        .zone-mode {
          display: flex;
          align-items: center;
          gap: 6px;
          font-size: 12px;
          color: #fbbf24;
          margin-bottom: 10px;
          padding: 6px 10px;
          background: rgba(251, 191, 36, 0.1);
          border-radius: 6px;
          width: fit-content;
        }
        .mood-gauges {
          display: flex;
          justify-content: space-around;
          margin: 12px 0;
          padding: 10px;
          background: rgba(30, 42, 54, 0.5);
          border-radius: 8px;
        }
        .mood-gauge {
          width: 70px;
          height: 70px;
        }
        .mood-gauge.mood-gauge-missing {
          display: flex;
          align-items: center;
          justify-content: center;
          border: 1px dashed rgba(245, 158, 11, 0.35);
          border-radius: 50%;
          background: rgba(30, 42, 54, 0.35);
          color: #f59e0b;
        }
        .missing-value {
          text-align: center;
          line-height: 1.1;
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 2px;
        }
        .value-na {
          font-size: 18px;
          font-weight: 700;
        }
        .value-title {
          font-size: 10px;
          color: var(--secondary-text-color, #9fb1c3);
          font-weight: 500;
        }
        .value-subtitle {
          font-size: 10px;
          color: #fbbf24;
        }
        .neuron-bar-container.neuron-missing {
          min-height: 42px;
          display: flex;
          align-items: center;
          justify-content: center;
          background: rgba(30, 42, 54, 0.5);
          border-radius: 6px;
          padding: 6px 4px;
        }
        .neuron-bar-container {
          margin: 10px 0;
        }
        .neuron-bar-label {
          display: flex;
          align-items: center;
          gap: 6px;
          font-size: 11px;
          color: var(--secondary-text-color, #9fb1c3);
          margin-bottom: 4px;
        }
        .neuron-bar-track {
          height: 6px;
          background: #1e2a36;
          border-radius: 3px;
          position: relative;
          overflow: hidden;
        }
        .neuron-bar-fill {
          height: 100%;
          background: linear-gradient(90deg, #2196f3, #22c55e);
          border-radius: 3px;
          transition: width 0.5s ease;
        }
        .neuron-score-marker {
          position: absolute;
          top: -2px;
          width: 2px;
          height: 10px;
          background: #f59e0b;
          transform: translateX(-50%);
        }
        .neuron-bar-stats {
          display: flex;
          justify-content: space-between;
          font-size: 10px;
          color: #6b7280;
          margin-top: 4px;
        }
        .quick-actions {
          display: flex;
          gap: 8px;
          margin-top: 12px;
          padding-top: 10px;
          border-top: 1px solid #1e2a36;
        }
        .action-btn {
          flex: 1;
          padding: 8px;
          border: none;
          border-radius: 6px;
          background: #1e2a36;
          color: #e6eef6;
          cursor: pointer;
          font-size: 16px;
          transition: all 0.2s ease;
          display: flex;
          align-items: center;
          justify-content: center;
        }
        .action-btn:hover {
          background: #2d3a4a;
          transform: scale(1.05);
        }
        .action-btn:active {
          transform: scale(0.95);
        }
        .no-zones {
          text-align: center;
          padding: 40px;
          color: var(--secondary-text-color, #9fb1c3);
        }
        .mdi-icon {
          font-family: 'Material Design Icons', sans-serif;
          font-style: normal;
        }
      </style>
      <ha-card>
        <div class="card">
          <div class="header">
            <span class="title">${title}</span>
            <span class="zone-count">
              <span class="active">${active_zones}</span> / ${total_zones} aktiv
            </span>
          </div>
          <div class="zones-grid">
            ${zoneCards}
          </div>
        </div>
      </ha-card>
    `;

    // Add event listeners for quick actions
    this._setupEventListeners();
  }

  _setupEventListeners() {
    const buttons = this.shadowRoot.querySelectorAll('.action-btn');
    buttons.forEach(btn => {
      btn.addEventListener('click', (e) => {
        const action = e.currentTarget.dataset.action;
        const zoneCard = e.currentTarget.closest('.zone-card');
        const zoneId = zoneCard?.dataset.zone;

        if (action === 'light') {
          this._toggleLight(zoneId);
        } else if (action === 'scene') {
          this._showSceneSelector(zoneId);
        } else if (action === 'thermostat') {
          this._adjustThermostat(zoneId);
        }
      });
    });
  }

  _toggleLight(zoneId) {
    if (!this._hass || !zoneId) return;

    const lightEntity = `light.${zoneId}_main`;
    const state = this._hass.states[lightEntity];
    const newState = state?.state === 'on' ? 'off' : 'on';

    this._hass.callService('light', 'toggle', {
      entity_id: lightEntity
    });
  }

  _showSceneSelector(zoneId) {
    // Dispatch event to show scene selector (can be handled by companion popup)
    this.dispatchEvent(new CustomEvent('scene-select', {
      detail: { zoneId },
      bubbles: true,
      composed: true
    }));
  }

  _adjustThermostat(zoneId) {
    if (!this._hass || !zoneId) return;

    const thermostatEntity = `climate.${zoneId}`;
    this._hass.callService('climate', 'set_temperature', {
      entity_id: thermostatEntity,
      temperature: 21
    });
  }
}

customElements.define('styx-zone-card', StyxZoneCard);

window.customCards = window.customCards || [];
window.customCards.push({
  type: 'styx-zone-card',
  name: 'PilotSuite Zone Dashboard',
  description: 'Zone status card with mood gauges, neuron activity, and quick actions.',
  preview: true,
  required_features: ['x'],
});
