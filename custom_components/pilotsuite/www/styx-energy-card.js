/**
 * PilotSuite Energy Card v1.0.0
 * 
 * Lovelace card for Energy module (Slice 82)
 * Shows consumption, forecast, optimization recommendations
 */

const _EnergyBase = window.StyxCardBase || HTMLElement;

class StyxEnergyCard extends _EnergyBase {
  constructor() {
    super();
    if (!this.shadowRoot) this.attachShadow({ mode: 'open' });
    this._config = {};
    this._hass = null;
  }

  setConfig(config) {
    this._config = {
      type: 'custom:styx-energy-card',
      title: 'Energy Management',
      show_forecast: true,
      show_recommendations: true,
      ...config,
    };
  }

  set hass(hass) {
    this._hass = hass;
    this._render();
  }

  _render() {
    if (!this._hass) return;

    // Get energy forecast sensor
    const energyEntity = this._hass.states['sensor.pilot_suite_energy_forecast'];
    const forecast = energyEntity?.attributes?.forecast_24h || 0;
    const current = energyEntity?.state || 0;
    const recommendations = energyEntity?.attributes?.recommendations || [];

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
        .stats { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 16px; }
        .stat {
          background: var(--secondary-background-color);
          border-radius: 8px;
          padding: 16px;
          text-align: center;
        }
        .value { font-size: 28px; font-weight: bold; color: var(--primary-color); }
        .label { font-size: 14px; color: var(--secondary-text-color); margin-top: 4px; }
        .recommendations { margin-top: 16px; }
        .rec {
          background: var(--secondary-background-color);
          border-radius: 8px;
          padding: 12px;
          margin-bottom: 8px;
          border-left: 4px solid #ff9800;
        }
        .rec-title { font-weight: 500; margin-bottom: 4px; }
        .rec-savings { font-size: 12px; color: #4caf50; }
      </style>
      <div class="card">
        <div class="header">
          <div class="title">${this._config.title}</div>
        </div>
        <div class="stats">
          <div class="stat">
            <div class="value">${current} kWh</div>
            <div class="label">Current Consumption</div>
          </div>
          <div class="stat">
            <div class="value">${forecast} kWh</div>
            <div class="label">24h Forecast</div>
          </div>
        </div>
        ${recommendations.length > 0 ? `
          <div class="recommendations">
            <div class="title" style="font-size: 16px; margin-bottom: 8px;">Optimization Recommendations</div>
            ${recommendations.map(rec => `
              <div class="rec">
                <div class="rec-title">${rec.title || rec}</div>
                <div class="rec-savings">${rec.savings ? 'Save ' + rec.savings : ''}</div>
              </div>
            `).join('')}
          </div>
        ` : ''}
      </div>
    `;
  }
}

customElements.define('styx-energy-card', StyxEnergyCard);
window.customCards.push({
  type: 'styx-energy-card',
  name: 'PilotSuite Energy Card',
  description: 'Energy Management dashboard card',
  preview: true,
});
