/**
 * PilotSuite Climate Card v1.0.0
 * 
 * Lovelace card for Climate/HVAC module (Slice 80)
 * Shows temperature, setpoints, HVAC modes per zone
 */

const _ClimateBase = window.StyxCardBase || HTMLElement;

class StyxClimateCard extends _ClimateBase {
  constructor() {
    super();
    if (!this.shadowRoot) this.attachShadow({ mode: 'open' });
    this._config = {};
    this._hass = null;
  }

  setConfig(config) {
    this._config = {
      type: 'custom:styx-climate-card',
      title: 'Climate Control',
      show_setpoints: true,
      show_modes: true,
      ...config,
    };
  }

  set hass(hass) {
    this._hass = hass;
    this._render();
  }

  _render() {
    if (!this._hass) return;

    // Get all climate sensors
    const climateSensors = Object.values(this._hass.states)
      .filter(e => e.entity_id.startsWith('sensor.pilot_suite_climate_'));

    this.shadowRoot.innerHTML = `
      <style>
        :host { display: block; }
        .card {
          background: var(--ha-card-background, white);
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
        .title { font-size: 20px; font-weight: bold; }
        .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 12px; }
        .zone {
          background: var(--secondary-background-color);
          border-radius: 8px;
          padding: 16px;
        }
        .zone-name { font-weight: 500; margin-bottom: 8px; }
        .temp { font-size: 32px; font-weight: bold; color: var(--primary-color); }
        .target { font-size: 14px; color: var(--secondary-text-color); margin-top: 4px; }
        .mode { 
          display: inline-block;
          padding: 4px 8px;
          border-radius: 4px;
          font-size: 12px;
          margin-top: 8px;
          background: var(--primary-color);
          color: white;
        }
      </style>
      <div class="card">
        <div class="header">
          <div class="title">${this._config.title}</div>
        </div>
        <div class="grid">
          ${climateSensors.map(zone => `
            <div class="zone">
              <div class="zone-name">${zone.attributes.friendly_name || zone.entity_id}</div>
              <div class="temp">${zone.state}°C</div>
              <div class="target">Target: ${zone.attributes.target_temp || '—'}°C</div>
              <div class="mode">${zone.attributes.hvac_mode || '—'}</div>
            </div>
          `).join('')}
        </div>
      </div>
    `;
  }
}

customElements.define('styx-climate-card', StyxClimateCard);
window.customCards.push({
  type: 'styx-climate-card',
  name: 'PilotSuite Climate Card',
  description: 'Climate/HVAC dashboard card',
  preview: true,
});
