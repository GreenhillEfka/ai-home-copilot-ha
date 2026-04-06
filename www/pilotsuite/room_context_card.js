/**
 * PilotSuite Room Context Card — Lovelace Custom Card
 * Displays and manages Room Contexts with activation controls
 */

class RoomContextCard extends HTMLElement {
  constructor() {
    super();
    this._hass = null;
    this._config = null;
    this._contexts = [];
    this._coreUrl = null;
  }

  setConfig(config) {
    this._config = config;
    this._coreUrl = config.core_url || 'http://localhost:8909';
    this._fetchContexts();
    this._refreshInterval = setInterval(() => this._fetchContexts(), 30000);
  }

  set hass(hass) {
    this._hass = hass;
  }

  async _fetchContexts() {
    try {
      const response = await fetch(`${this._coreUrl}/api/v1/contexts/rooms`);
      const data = await response.json();
      this._contexts = data.contexts || [];
      this._render();
    } catch (err) {
      console.error('Failed to fetch Room Contexts:', err);
    }
  }

  async _handleActivate(contextId) {
    await fetch(`${this._coreUrl}/api/v1/contexts/rooms/${contextId}/activate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' }
    });
    this._fetchContexts();
  }

  async _handleDeactivate(contextId) {
    await fetch(`${this._coreUrl}/api/v1/contexts/rooms/${contextId}/deactivate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' }
    });
    this._fetchContexts();
  }

  _render() {
    const activeCount = this._contexts.filter(c => c.active).length;
    
    this.innerHTML = `
      <ha-card header="🎭 Room Contexts">
        <div class="card-content">
          <div class="summary">
            <span class="stat">
              <span class="value">${this._contexts.length}</span>
              <span class="label">Kontexte</span>
            </span>
            <span class="stat">
              <span class="value">${activeCount}</span>
              <span class="label">Aktiv</span>
            </span>
            <span class="stat">
              <span class="value">${this._contexts.filter(c => c.ha_scene_id).length}</span>
              <span class="label">Mit Szene</span>
            </span>
          </div>
          
          <div class="contexts-list">
            ${this._contexts.map(ctx => `
              <div class="context-item ${ctx.active ? 'active' : ''}">
                <div class="context-header">
                  <span class="context-name">${ctx.name}</span>
                  <span class="context-zone">${ctx.zone_ref || 'Keine Zone'}</span>
                </div>
                <div class="context-details">
                  ${ctx.trigger_time ? `<span class="badge">⏰ ${ctx.trigger_time}</span>` : ''}
                  ${ctx.trigger_presence ? `<span class="badge">👤 ${ctx.trigger_presence}</span>` : ''}
                  ${ctx.ha_scene_id ? `<span class="badge">🎬 Szene</span>` : ''}
                  ${ctx.learned ? `<span class="badge learned">🧠 Gelernt</span>` : ''}
                </div>
                <div class="context-actions">
                  ${ctx.active ? 
                    `<button class="btn deactivate" onclick="this.dispatchEvent(new CustomEvent('deactivate', {detail: '${ctx.context_id}'}))">Deaktivieren</button>` : 
                    `<button class="btn activate" onclick="this.dispatchEvent(new CustomEvent('activate', {detail: '${ctx.context_id}'}))">Aktivieren</button>`}
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
        .contexts-list { display: grid; gap: 8px; }
        .context-item {
          padding: 12px;
          border: 1px solid var(--divider-color);
          border-radius: 8px;
          transition: all 0.2s;
        }
        .context-item.active {
          border-color: var(--accent-color);
          background: rgba(var(--rgb-accent-color), 0.1);
        }
        .context-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 8px;
        }
        .context-name { font-weight: bold; font-size: 16px; }
        .context-zone {
          font-size: 12px;
          padding: 2px 8px;
          background: var(--secondary-background-color);
          border-radius: 4px;
        }
        .context-details {
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
        .badge.learned {
          background: var(--accent-color);
        }
        .context-actions { display: flex; gap: 8px; }
        .btn {
          padding: 8px 16px;
          border: none;
          border-radius: 4px;
          cursor: pointer;
          font-size: 13px;
        }
        .btn.activate {
          background: var(--primary-color);
          color: var(--text-primary-color);
        }
        .btn.deactivate {
          background: var(--secondary-background-color);
          color: var(--primary-color);
          border: 1px solid var(--primary-color);
        }
      </style>
    `;

    this.addEventListener('activate', (e) => this._handleActivate(e.detail));
    this.addEventListener('deactivate', (e) => this._handleDeactivate(e.detail));
  }

  disconnectedCallback() {
    if (this._refreshInterval) clearInterval(this._refreshInterval);
  }

  getCardSize() {
    return this._contexts.length + 2;
  }
}

customElements.define('pilotsuite-room-context-card', RoomContextCard);
