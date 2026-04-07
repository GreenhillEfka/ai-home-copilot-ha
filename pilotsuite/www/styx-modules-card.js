/**
 * PilotSuite Modules Dashboard Card v1.0.0
 * 
 * Lovelace custom card showing all intelligence modules status:
 * - Presence (Slices 67, 70, 75)
 * - Light (Slices 68, 71, 76)
 * - TimeOfDay (Slices 69, 72, 77)
 * - Rules (Slices 73, 78)
 * - Climate (Slice 80)
 * - Humidity (Slice 81)
 * - Energy (Slice 82)
 *
 * Features:
 * - Module status overview
 * - Quick actions per module
 * - Real-time updates via HA entity polling
 * - Responsive grid layout
 */

const MODULE_ICONS = {
  presence: 'mdi:motion-sensor',
  light: 'mdi:lightbulb',
  climate: 'mdi:thermostat',
  humidity: 'mdi:water-percent',
  energy: 'mdi:lightning-bolt',
  timeofday: 'mdi:clock-outline',
  rules: 'mdi:script-text',
};

const MODULE_NAMES = {
  presence: 'Presence Intelligence',
  light: 'Light Intelligence',
  climate: 'Climate/HVAC',
  humidity: 'Humidity Control',
  energy: 'Energy Management',
  timeofday: 'Time of Day',
  rules: 'Rules Engine',
};

const MODULE_COLORS = {
  presence: '#4caf50',
  light: '#ff9800',
  climate: '#f44336',
  humidity: '#2196f3',
  energy: '#ffeb3b',
  timeofday: '#9c27b0',
  rules: '#00bcd4',
};

const _ModuleBase = window.StyxCardBase || HTMLElement;

class StyxModulesCard extends _ModuleBase {
  constructor() {
    super();
    if (!this.shadowRoot) this.attachShadow({ mode: 'open' });
    this._config = {};
    this._hass = null;
    this._pollTimer = null;
    this._modules = {};
  }

  disconnectedCallback() {
    super.disconnectedCallback?.();
    if (this._pollTimer) {
      clearInterval(this._pollTimer);
      this._pollTimer = null;
    }
  }

  static getConfigElement() {
    return super.getConfigElement?.() || document.createElement('hui-generic-entity-row');
  }

  static getStubConfig() {
    return {
      type: 'custom:styx-modules-card',
      title: 'PilotSuite Modules',
      refresh_interval: 30,
      show_actions: true,
      show_status: true,
    };
  }

  setConfig(config) {
    this._config = {
      type: 'custom:styx-modules-card',
      title: 'PilotSuite Modules',
      refresh_interval: 30,
      show_actions: true,
      show_status: true,
      ...config,
    };
  }

  set hass(hass) {
    this._hass = hass;
    this._updateFromHass();
    this._render();
  }

  _updateFromHass() {
    // Fetch module states from HA entities
    const modules = {};
    
    // Presence
    const presenceEntity = this._hass.states['sensor.pilot_suite_presence_count'];
    if (presenceEntity) {
      modules.presence = {
        status: 'active',
        value: presenceEntity.state,
        unit: 'zones occupied',
      };
    }

    // Light
    const lightEntity = this._hass.states['sensor.pilot_suite_light_zones'];
    if (lightEntity) {
      modules.light = {
        status: 'active',
        value: lightEntity.state,
      };
    }

    // Climate
    const climateEntity = this._hass.states['sensor.pilot_suite_climate_zones'];
    if (climateEntity) {
      modules.climate = {
        status: 'active',
        value: climateEntity.state + '°C',
      };
    }

    // Humidity
    const humidityEntity = this._hass.states['sensor.pilot_suite_humidity_zones'];
    if (humidityEntity) {
      modules.humidity = {
        status: 'active',
        value: humidityEntity.state + '%',
      };
    }

    // Energy
    const energyEntity = this._hass.states['sensor.pilot_suite_energy_forecast'];
    if (energyEntity) {
      modules.energy = {
        status: 'active',
        value: energyEntity.state + ' kWh',
      };
    }

    // TimeOfDay
    const timeofdayEntity = this._hass.states['sensor.pilot_suite_time_of_day'];
    if (timeofdayEntity) {
      modules.timeofday = {
        status: 'active',
        value: timeofdayEntity.state,
      };
    }

    // Rules
    const rulesEntity = this._hass.states['sensor.pilot_suite_active_rules'];
    if (rulesEntity) {
      modules.rules = {
        status: 'active',
        value: rulesEntity.state + ' rules',
      };
    }

    this._modules = modules;
  }

  _render() {
    if (!this._hass || !this._config) return;

    this.shadowRoot.innerHTML = `
      <style>
        :host {
          display: block;
        }
        .card {
          background: var(--ha-card-background, var(--card-background-color, white));
          border-radius: var(--ha-card-border-radius, 12px);
          box-shadow: var(--ha-card-box-shadow, 0 2px 4px rgba(0,0,0,0.1));
          padding: 16px;
        }
        .header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 16px;
        }
        .title {
          font-size: 20px;
          font-weight: bold;
          color: var(--primary-text-color);
        }
        .grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
          gap: 12px;
        }
        .module {
          background: var(--secondary-background-color, #f5f5f5);
          border-radius: 8px;
          padding: 16px;
          display: flex;
          align-items: center;
          gap: 12px;
          transition: transform 0.2s;
        }
        .module:hover {
          transform: translateY(-2px);
        }
        .icon {
          width: 48px;
          height: 48px;
          border-radius: 50%;
          display: flex;
          align-items: center;
          justify-content: center;
          color: white;
          font-size: 24px;
        }
        .info {
          flex: 1;
        }
        .name {
          font-size: 14px;
          font-weight: 500;
          color: var(--primary-text-color);
          margin-bottom: 4px;
        }
        .value {
          font-size: 18px;
          font-weight: bold;
          color: var(--secondary-text-color);
        }
        .status {
          font-size: 12px;
          color: var(--secondary-text-color);
          margin-top: 4px;
        }
        .actions {
          display: flex;
          gap: 8px;
          margin-top: 8px;
        }
        .action-btn {
          background: var(--primary-color);
          color: white;
          border: none;
          border-radius: 4px;
          padding: 4px 8px;
          font-size: 12px;
          cursor: pointer;
          transition: opacity 0.2s;
        }
        .action-btn:hover {
          opacity: 0.8;
        }
      </style>
      <div class="card">
        <div class="header">
          <div class="title">${this._config.title}</div>
        </div>
        <div class="grid">
          ${this._renderModules()}
        </div>
      </div>
    `;
  }

  _renderModules() {
    const modules = Object.keys(MODULE_ICONS);
    
    return modules.map(moduleId => {
      const moduleData = this._modules[moduleId] || { status: 'inactive', value: '-' };
      const icon = MODULE_ICONS[moduleId];
      const name = MODULE_NAMES[moduleId];
      const color = MODULE_COLORS[moduleId];
      
      return `
        <div class="module">
          <div class="icon" style="background: ${color}">
            <ha-icon icon="${icon}"></ha-icon>
          </div>
          <div class="info">
            <div class="name">${name}</div>
            <div class="value">${moduleData.value}</div>
            <div class="status">Status: ${moduleData.status}</div>
            ${this._config.show_actions ? this._renderActions(moduleId) : ''}
          </div>
        </div>
      `;
    }).join('');
  }

  _renderActions(moduleId) {
    const actions = {
      presence: [
        { label: 'Refresh', action: 'refresh' },
        { label: 'Override', action: 'override' },
      ],
      light: [
        { label: 'Scenes', action: 'scenes' },
        { label: 'Refresh', action: 'refresh' },
      ],
      climate: [
        { label: 'Setpoint', action: 'setpoint' },
        { label: 'Mode', action: 'mode' },
      ],
      humidity: [
        { label: 'Refresh', action: 'refresh' },
      ],
      energy: [
        { label: 'Forecast', action: 'forecast' },
        { label: 'Optimize', action: 'optimize' },
      ],
      timeofday: [
        { label: 'Mode', action: 'mode' },
      ],
      rules: [
        { label: 'List', action: 'list' },
        { label: 'Activate', action: 'activate' },
      ],
    };

    const moduleActions = actions[moduleId] || [];
    
    return `
      <div class="actions">
        ${moduleActions.map(action => `
          <button class="action-btn" data-module="${moduleId}" data-action="${action.action}">
            ${action.label}
          </button>
        `).join('')}
      </div>
    `;
  }

  connectedCallback() {
    super.connectedCallback?.();
    // Start polling for updates
    if (this._config.refresh_interval) {
      this._pollTimer = setInterval(() => {
        if (this._hass) {
          this._updateFromHass();
          this._render();
        }
      }, this._config.refresh_interval * 1000);
    }
  }

  // Handle action button clicks
  static async actionHandler(hass, moduleId, action) {
    console.log(`Module action: ${moduleId}.${action}`);
    
    // Dispatch action to HA service
    await hass.callService('button', 'press', {
      entity_id: `button.pilot_suite_${moduleId}_${action}`,
    });
  }
}

// Register the card
customElements.define('styx-modules-card', StyxModulesCard);

// Add to window for Lovelace
window.customCards = window.customCards || [];
window.customCards.push({
  type: 'styx-modules-card',
  name: 'PilotSuite Modules Card',
  description: 'Dashboard card showing all PilotSuite intelligence modules status',
  preview: true,
});
