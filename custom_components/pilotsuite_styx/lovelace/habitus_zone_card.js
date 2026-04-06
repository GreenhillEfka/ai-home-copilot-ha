/**
 * PilotSuite Habitus Zone Card — Lovelace Custom Card
 * Displays and manages Habitus Zones with symbiotic state
 */

class HabitusZoneCard extends HTMLElement {
  constructor() {
    super();
    this._hass = null;
    this._config = null;
    this._zones = [];
    this._coreUrl = null;
  }

  setConfig(config) {
    this._config = config;
    this._coreUrl = config.core_url || 'http://localhost:8909';
    this._fetchZones();
    // Auto-refresh every 30s
    this._refreshInterval = setInterval(() => this._fetchZones(), 30000);
  }

  set hass(hass) {
    this._hass = hass;
  }

  async _fetchZones() {
    try {
      const response = await fetch(`${this._coreUrl}/api/v1/habitus/zones`);
      const data = await response.json();
      this._zones = data.zones || [];
      this._render();
    } catch (err) {
      console.error('Failed to fetch Habitus Zones:', err);
    }
  }

  async _handleZoneClick(zone) {
    // Navigate to zone detail or open dialog
    this.dispatchEvent(new CustomEvent('hass-more-info', {
      bubbles: true,
      composed: true,
      detail: { entityId: `sensor.pilotsuite_habitus_zones` }
    }));
  }

  async _handleAddZone() {
    const name = prompt('Zone Name:');
    if (!name) return;
    
    const zoneId = `zone.${name.toLowerCase().replace(' ', '_')}`;
    await fetch(`${this._coreUrl}/api/v1/habitus/zones`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ zone_id: zoneId, name: name })
    });
    this._fetchZones();
  }

  _render() {
    this.innerHTML = `
      <ha-card header="🏠 Habitus Zones">
        <div class="card-content">
          <div class="summary">
            <span class="stat">
              <span class="value">${this._zones.length}</span>
              <span class="label">Zonen</span>
            </span>
            <span class="stat">
              <span class="value">${this._zones.filter(z => z.linked_entities?.length > 0).length}</span>
              <span class="label">Mit Devices</span>
            </span>
            <span class="stat">
              <span class="value">${this._zones.filter(z => z.habitus_rules?.length > 0).length}</span>
              <span class="label">Mit Regeln</span>
            </span>
          </div>
          
          <div class="zones-list">
            ${this._zones.map(zone => `
              <div class="zone-item ${zone.active_context === 'active' ? 'active' : ''}" 
                   onclick="this.dispatchEvent(new CustomEvent('zone-click', {detail: ${JSON.stringify(zone)}}))">
                <div class="zone-header">
                  <span class="zone-name">${zone.name}</span>
                  <span class="zone-context">${zone.active_context}</span>
                </div>
                <div class="zone-details">
                  ${zone.linked_entities?.length > 0 ? 
                    `<span class="badge">🔗 ${zone.linked_entities.length} Devices</span>` : 
                    '<span class="badge empty">Keine Devices</span>'}
                  ${zone.habitus_rules?.length > 0 ? 
                    `<span class="badge">📋 ${zone.habitus_rules.length} Regeln</span>` : 
                    '<span class="badge empty">Keine Regeln</span>'}
                </div>
              </div>
            `).join('')}
          </div>
          
          <button class="add-zone-btn" onclick="this.dispatchEvent(new CustomEvent('add-zone'))">
            + Zone hinzufügen
          </button>
        </div>
      </ha-card>
      
      <style>
        ha-card {
          padding: 16px;
        }
        .summary {
          display: flex;
          justify-content: space-around;
          margin-bottom: 16px;
          padding: 12px;
          background: var(--secondary-background-color);
          border-radius: 8px;
        }
        .stat {
          text-align: center;
        }
        .stat .value {
          display: block;
          font-size: 24px;
          font-weight: bold;
          color: var(--primary-color);
        }
        .stat .label {
          font-size: 12px;
          color: var(--secondary-text-color);
        }
        .zones-list {
          display: grid;
          gap: 8px;
        }
        .zone-item {
          padding: 12px;
          border: 1px solid var(--divider-color);
          border-radius: 8px;
          cursor: pointer;
          transition: all 0.2s;
        }
        .zone-item:hover {
          border-color: var(--primary-color);
          background: var(--secondary-background-color);
        }
        .zone-item.active {
          border-color: var(--accent-color);
          background: rgba(var(--rgb-accent-color), 0.1);
        }
        .zone-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 8px;
        }
        .zone-name {
          font-weight: bold;
          font-size: 16px;
        }
        .zone-context {
          font-size: 12px;
          padding: 2px 8px;
          background: var(--secondary-background-color);
          border-radius: 4px;
        }
        .zone-details {
          display: flex;
          gap: 8px;
        }
        .badge {
          font-size: 12px;
          padding: 2px 8px;
          background: var(--primary-color);
          color: var(--text-primary-color);
          border-radius: 4px;
        }
        .badge.empty {
          background: var(--secondary-background-color);
          color: var(--secondary-text-color);
        }
        .add-zone-btn {
          margin-top: 16px;
          width: 100%;
          padding: 12px;
          background: var(--primary-color);
          color: var(--text-primary-color);
          border: none;
          border-radius: 8px;
          cursor: pointer;
          font-size: 14px;
        }
        .add-zone-btn:hover {
          opacity: 0.9;
        }
      </style>
    `;

    // Attach event listeners
    this.addEventListener('zone-click', (e) => this._handleZoneClick(e.detail));
    this.addEventListener('add-zone', () => this._handleAddZone());
  }

  disconnectedCallback() {
    if (this._refreshInterval) {
      clearInterval(this._refreshInterval);
    }
  }

  getCardSize() {
    return this._zones.length + 2;
  }
}

customElements.define('pilotsuite-habitus-zone-card', HabitusZoneCard);
