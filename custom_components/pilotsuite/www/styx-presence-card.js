/**
 * PilotSuite Presence Card v1.0.0
 * 
 * Lovelace card for Presence Intelligence module (Slices 67,70,75)
 * Shows zone occupancy, person tracking, presence history
 */

const _PresenceBase = window.StyxCardBase || HTMLElement;

class StyxPresenceCard extends _PresenceBase {
  constructor() {
    super();
    if (!this.shadowRoot) this.attachShadow({ mode: 'open' });
    this._config = {};
    this._hass = null;
  }

  setConfig(config) {
    this._config = {
      type: 'custom:styx-presence-card',
      title: 'Presence Intelligence',
      show_history: true,
      show_sensors: true,
      ...config,
    };
  }

  set hass(hass) {
    this._hass = hass;
    this._render();
  }

  _render() {
    if (!this._hass) return;

    // Get presence count
    const presenceEntity = this._hass.states['sensor.pilot_suite_presence_count'];
    const count = presenceEntity ? parseInt(presenceEntity.state) : 0;
    
    // Get all zone sensors
    const zoneSensors = Object.values(this._hass.states)
      .filter(e => e.entity_id.startsWith('sensor.pilot_suite_presence_') && !e.entity_id.includes('count'));

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
        .count {
          font-size: 32px;
          font-weight: bold;
          color: var(--primary-color);
        }
        .label { font-size: 14px; color: var(--secondary-text-color); }
        .zones { display: grid; gap: 12px; margin-top: 16px; }
        .zone {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 12px;
          background: var(--secondary-background-color);
          border-radius: 8px;
        }
        .zone.present { border-left: 4px solid #4caf50; }
        .zone.absent { border-left: 4px solid #9e9e9e; }
        .zone-name { font-weight: 500; }
        .zone-state { font-size: 14px; }
        .present { color: #4caf50; }
        .absent { color: #9e9e9e; }
      </style>
      <div class="card">
        <div class="header">
          <div class="title">${this._config.title}</div>
          <div>
            <div class="count">${count}</div>
            <div class="label">Zones Occupied</div>
          </div>
        </div>
        <div class="zones">
          ${zoneSensors.map(zone => `
            <div class="zone ${zone.state === 'present' ? 'present' : 'absent'}">
              <div class="zone-name">${zone.attributes.friendly_name || zone.entity_id}</div>
              <div class="zone-state ${zone.state}">${zone.state}</div>
            </div>
          `).join('')}
        </div>
      </div>
    `;
  }
}

customElements.define('styx-presence-card', StyxPresenceCard);
window.customCards = window.customCards || [];
window.customCards.push({
  type: 'styx-presence-card',
  name: 'PilotSuite Presence Card',
  description: 'Presence Intelligence dashboard card',
  preview: true,
});
