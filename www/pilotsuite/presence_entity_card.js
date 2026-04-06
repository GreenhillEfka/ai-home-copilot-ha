/**
 * PilotSuite Presence Entity Card — Lovelace Custom Card
 * Displays and manages Presence Entities with real-time state
 */

class PresenceEntityCard extends HTMLElement {
  constructor() {
    super();
    this._hass = null;
    this._config = null;
    this._entities = [];
    this._coreUrl = null;
  }

  setConfig(config) {
    this._config = config;
    this._coreUrl = config.core_url || 'http://localhost:8909';
    this._fetchEntities();
    this._refreshInterval = setInterval(() => this._fetchEntities(), 10000); // Faster refresh for presence
  }

  set hass(hass) {
    this._hass = hass;
  }

  async _fetchEntities() {
    try {
      const response = await fetch(`${this._coreUrl}/api/v1/entities/presence`);
      const data = await response.json();
      this._entities = data.entities || [];
      this._render();
    } catch (err) {
      console.error('Failed to fetch Presence Entities:', err);
    }
  }

  _render() {
    const summary = {
      total: this._entities.length,
      active: this._entities.filter(e => e.current_state).length,
      byType: this._entities.reduce((acc, e) => {
        acc[e.presence_type] = (acc[e.presence_type] || 0) + 1;
        return acc;
      }, {})
    };
    
    this.innerHTML = `
      <ha-card header="👤 Presence Entities">
        <div class="card-content">
          <div class="summary ${summary.active > 0 ? 'has-active' : ''}">
            <span class="stat">
              <span class="value">${summary.total}</span>
              <span class="label">Sensoren</span>
            </span>
            <span class="stat">
              <span class="value ${summary.active > 0 ? 'active-state' : ''}">${summary.active}</span>
              <span class="label">Aktiv</span>
            </span>
            <span class="stat">
              <span class="value">${Object.keys(summary.byType).length}</span>
              <span class="label">Typen</span>
            </span>
          </div>
          
          <div class="types-section">
            ${Object.entries(summary.byType).map(([type, count]) => `
              <div class="type-badge">
                <span class="type-icon">${this._getTypeIcon(type)}</span>
                <span class="type-name">${type}</span>
                <span class="type-count">${count}</span>
              </div>
            `).join('')}
          </div>
          
          <div class="entities-list">
            ${this._entities.map(entity => `
              <div class="entity-item ${entity.current_state ? 'active' : 'inactive'}">
                <div class="entity-header">
                  <span class="entity-name">${entity.name}</span>
                  <span class="entity-state ${entity.current_state ? 'on' : 'off'}">
                    ${entity.current_state ? '● ERKANNT' : '○ NICHT ERKANNT'}
                  </span>
                </div>
                <div class="entity-details">
                  <span class="badge">${entity.presence_type}</span>
                  ${entity.zone_ref ? 
                    `<span class="badge zone">📍 ${entity.zone_ref}</span>` : 
                    '<span class="badge no-zone">Keine Zone</span>'}
                  ${entity.last_changed ? 
                    `<span class="badge time">⏰ ${entity.last_changed}</span>` : ''}
                </div>
              </div>
            `).join('')}
          </div>
        </div>
      </ha-card>
      
      <style>
        ha-card { padding: 16px; }
        .summary {
          display: flex;
          justify-content: space-around;
          margin-bottom: 16px;
          padding: 12px;
          background: var(--secondary-background-color);
          border-radius: 8px;
          transition: all 0.3s;
        }
        .summary.has-active {
          background: rgba(var(--rgb-accent-color), 0.15);
          border: 1px solid var(--accent-color);
        }
        .stat { text-align: center; }
        .stat .value {
          display: block;
          font-size: 24px;
          font-weight: bold;
          color: var(--primary-color);
        }
        .stat .value.active-state {
          color: var(--accent-color);
          animation: pulse 2s infinite;
        }
        .stat .label {
          font-size: 12px;
          color: var(--secondary-text-color);
        }
        @keyframes pulse {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.6; }
        }
        .types-section {
          display: flex;
          gap: 8px;
          flex-wrap: wrap;
          margin-bottom: 16px;
        }
        .type-badge {
          display: flex;
          align-items: center;
          gap: 6px;
          padding: 6px 12px;
          background: var(--secondary-background-color);
          border-radius: 6px;
          font-size: 13px;
        }
        .type-icon { font-size: 16px; }
        .type-count {
          font-weight: bold;
          color: var(--primary-color);
        }
        .entities-list { display: grid; gap: 8px; }
        .entity-item {
          padding: 12px;
          border: 1px solid var(--divider-color);
          border-radius: 8px;
          transition: all 0.3s;
        }
        .entity-item.active {
          border-color: var(--accent-color);
          background: rgba(var(--rgb-accent-color), 0.08);
        }
        .entity-item.inactive {
          opacity: 0.7;
        }
        .entity-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 8px;
        }
        .entity-name { font-weight: bold; font-size: 15px; }
        .entity-state {
          font-size: 12px;
          padding: 2px 8px;
          border-radius: 4px;
          font-weight: bold;
        }
        .entity-state.on {
          background: var(--accent-color);
          color: var(--text-primary-color);
        }
        .entity-state.off {
          background: var(--secondary-background-color);
          color: var(--secondary-text-color);
        }
        .entity-details {
          display: flex;
          gap: 8px;
          flex-wrap: wrap;
        }
        .badge {
          font-size: 11px;
          padding: 2px 6px;
          background: var(--primary-color);
          color: var(--text-primary-color);
          border-radius: 4px;
        }
        .badge.zone {
          background: var(--accent-color);
        }
        .badge.no-zone {
          background: var(--secondary-background-color);
          color: var(--secondary-text-color);
        }
        .badge.time {
          background: var(--secondary-background-color);
        }
      </style>
    `;
  }

  _getTypeIcon(type) {
    const icons = {
      motion: '🏃',
      occupancy: '🏠',
      user_presence: '👤',
      presence: '📡'
    };
    return icons[type] || '📍';
  }

  disconnectedCallback() {
    if (this._refreshInterval) clearInterval(this._refreshInterval);
  }

  getCardSize() {
    return this._entities.length + 3;
  }
}

customElements.define('pilotsuite-presence-entity-card', PresenceEntityCard);
