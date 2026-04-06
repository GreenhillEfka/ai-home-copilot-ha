/**
 * PilotSuite Device Link Card — Lovelace Custom Card
 * Displays and manages Device Links with zone assignment
 */

class DeviceLinkCard extends HTMLElement {
  constructor() {
    super();
    this._hass = null;
    this._config = null;
    this._links = [];
    this._coreUrl = null;
  }

  setConfig(config) {
    this._config = config;
    this._coreUrl = config.core_url || 'http://localhost:8909';
    this._fetchLinks();
    this._refreshInterval = setInterval(() => this._fetchLinks(), 30000);
  }

  set hass(hass) {
    this._hass = hass;
  }

  async _fetchLinks() {
    try {
      const response = await fetch(`${this._coreUrl}/api/v1/devices/links`);
      const data = await response.json();
      this._links = data.links || [];
      this._render();
    } catch (err) {
      console.error('Failed to fetch Device Links:', err);
    }
  }

  async _handleZoneAssign(linkId) {
    const zoneRef = prompt('Zone Ref (e.g., zone.living_room):');
    if (!zoneRef) return;
    
    await fetch(`${this._coreUrl}/api/v1/devices/links/${linkId}/zone`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ zone_ref: zoneRef })
    });
    this._fetchLinks();
  }

  _render() {
    const summary = {
      total: this._links.length,
      zoned: this._links.filter(l => l.zone_ref).length,
      byDomain: this._links.reduce((acc, l) => {
        acc[l.domain] = (acc[l.domain] || 0) + 1;
        return acc;
      }, {})
    };
    
    this.innerHTML = `
      <ha-card header="🔗 Device Links">
        <div class="card-content">
          <div class="summary">
            <span class="stat">
              <span class="value">${summary.total}</span>
              <span class="label">Devices</span>
            </span>
            <span class="stat">
              <span class="value">${summary.zoned}</span>
              <span class="label">In Zonen</span>
            </span>
            <span class="stat">
              <span class="value">${Object.keys(summary.byDomain).length}</span>
              <span class="label">Domänen</span>
            </span>
          </div>
          
          <div class="domains-section">
            ${Object.entries(summary.byDomain).map(([domain, count]) => `
              <div class="domain-badge">
                <span class="domain-icon">${this._getDomainIcon(domain)}</span>
                <span class="domain-name">${domain}</span>
                <span class="domain-count">${count}</span>
              </div>
            `).join('')}
          </div>
          
          <div class="links-list">
            ${this._links.map(link => `
              <div class="link-item ${link.zone_ref ? 'zoned' : ''}">
                <div class="link-header">
                  <span class="link-name">${link.name}</span>
                  <span class="link-domain">${link.domain}</span>
                </div>
                <div class="link-details">
                  <span class="badge">🎯 ${link.capabilities?.length || 0} Capabilities</span>
                  ${link.zone_ref ? 
                    `<span class="badge zone">📍 ${link.zone_ref}</span>` : 
                    '<span class="badge no-zone">Keine Zone</span>'}
                </div>
                <div class="link-actions">
                  <button class="btn assign-zone" onclick="this.dispatchEvent(new CustomEvent('zone-assign', {detail: '${link.link_id}'}))">
                    ${link.zone_ref ? 'Zone ändern' : 'Zone zuweisen'}
                  </button>
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
        }
        .stat { text-align: center; }
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
        .domains-section {
          display: flex;
          gap: 8px;
          flex-wrap: wrap;
          margin-bottom: 16px;
        }
        .domain-badge {
          display: flex;
          align-items: center;
          gap: 6px;
          padding: 6px 12px;
          background: var(--secondary-background-color);
          border-radius: 6px;
          font-size: 13px;
        }
        .domain-icon { font-size: 16px; }
        .domain-count {
          font-weight: bold;
          color: var(--primary-color);
        }
        .links-list { display: grid; gap: 8px; }
        .link-item {
          padding: 12px;
          border: 1px solid var(--divider-color);
          border-radius: 8px;
          transition: all 0.2s;
        }
        .link-item.zoned {
          border-color: var(--accent-color);
        }
        .link-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 8px;
        }
        .link-name { font-weight: bold; font-size: 15px; }
        .link-domain {
          font-size: 11px;
          padding: 2px 6px;
          background: var(--secondary-background-color);
          border-radius: 4px;
          text-transform: uppercase;
        }
        .link-details {
          display: flex;
          gap: 8px;
          flex-wrap: wrap;
          margin-bottom: 12px;
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
        .link-actions { display: flex; gap: 8px; }
        .btn {
          padding: 8px 16px;
          border: none;
          border-radius: 4px;
          cursor: pointer;
          font-size: 13px;
          background: var(--primary-color);
          color: var(--text-primary-color);
        }
      </style>
    `;

    this.addEventListener('zone-assign', (e) => this._handleZoneAssign(e.detail));
  }

  _getDomainIcon(domain) {
    const icons = {
      light: '💡',
      media_player: '🎵',
      climate: '🌡️',
      cover: '🪟',
      switch: '🔌',
      input_boolean: '🔘'
    };
    return icons[domain] || '📱';
  }

  disconnectedCallback() {
    if (this._refreshInterval) clearInterval(this._refreshInterval);
  }

  getCardSize() {
    return this._links.length + 3;
  }
}

customElements.define('pilotsuite-device-link-card', DeviceLinkCard);
