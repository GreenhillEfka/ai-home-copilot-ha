/**
 * PilotSuite State Bridge Card — Lovelace Custom Card
 * Displays State Bridges with history visualization
 */

class StateBridgeCard extends HTMLElement {
  constructor() {
    super();
    this._hass = null;
    this._config = null;
    this._states = [];
    this._coreUrl = null;
  }

  setConfig(config) {
    this._config = config;
    this._coreUrl = config.core_url || 'http://localhost:8909';
    this._fetchStates();
    this._refreshInterval = setInterval(() => this._fetchStates(), 15000);
  }

  set hass(hass) {
    this._hass = hass;
  }

  async _fetchStates() {
    try {
      const response = await fetch(`${this._coreUrl}/api/v1/states`);
      const data = await response.json();
      this._states = data.states || [];
      this._render();
    } catch (err) {
      console.error('Failed to fetch State Bridges:', err);
    }
  }

  _render() {
    const summary = {
      total: this._states.length,
      withHistory: this._states.filter(s => s.history?.length > 0).length,
      withSubscribers: this._states.filter(s => s.subscribers?.length > 0).length,
      totalHistory: this._states.reduce((sum, s) => sum + (s.history?.length || 0), 0)
    };
    
    this.innerHTML = `
      <ha-card header="🌉 State Bridges">
        <div class="card-content">
          <div class="summary">
            <span class="stat">
              <span class="value">${summary.total}</span>
              <span class="label">States</span>
            </span>
            <span class="stat">
              <span class="value">${summary.withHistory}</span>
              <span class="label">Mit History</span>
            </span>
            <span class="stat">
              <span class="value">${summary.totalHistory}</span>
              <span class="label">History-Einträge</span>
            </span>
          </div>
          
          <div class="states-list">
            ${this._states.slice(0, 20).map(state => `
              <div class="state-item">
                <div class="state-header">
                  <span class="state-name">${state.name}</span>
                  <span class="state-value ${state.current_state?.state === 'on' ? 'on' : 'off'}">
                    ${state.current_state?.state || 'unknown'}
                  </span>
                </div>
                <div class="state-details">
                  <span class="badge">🔗 ${state.subscribers?.length || 0} Subscriber</span>
                  <span class="badge">📜 ${state.history?.length || 0} History</span>
                  ${state.last_sync ? `<span class="badge time">⏰ ${state.last_sync}</span>` : ''}
                </div>
                ${state.history?.length > 0 ? `
                  <div class="history-preview">
                    <span class="history-label">Letzte Änderungen:</span>
                    ${state.history.slice(-3).map(h => `
                      <span class="history-item">${h.state} @ ${h.at?.split('T')[1]?.split('.')[0]}</span>
                    `).join('')}
                  </div>
                ` : ''}
              </div>
            `).join('')}
          </div>
          ${this._states.length > 20 ? `<div class="more-indicator">+ ${this._states.length - 20} weitere...</div>` : ''}
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
        .states-list { display: grid; gap: 8px; }
        .state-item {
          padding: 12px;
          border: 1px solid var(--divider-color);
          border-radius: 8px;
          transition: all 0.2s;
        }
        .state-item:hover {
          border-color: var(--primary-color);
        }
        .state-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 8px;
        }
        .state-name { font-weight: bold; font-size: 14px; }
        .state-value {
          font-size: 12px;
          padding: 2px 8px;
          border-radius: 4px;
          font-weight: bold;
          text-transform: uppercase;
        }
        .state-value.on {
          background: var(--accent-color);
          color: var(--text-primary-color);
        }
        .state-value.off {
          background: var(--secondary-background-color);
          color: var(--secondary-text-color);
        }
        .state-details {
          display: flex;
          gap: 8px;
          flex-wrap: wrap;
          margin-bottom: 8px;
        }
        .badge {
          font-size: 11px;
          padding: 2px 6px;
          background: var(--primary-color);
          color: var(--text-primary-color);
          border-radius: 4px;
        }
        .badge.time {
          background: var(--secondary-background-color);
        }
        .history-preview {
          margin-top: 8px;
          padding: 8px;
          background: var(--secondary-background-color);
          border-radius: 4px;
        }
        .history-label {
          display: block;
          font-size: 11px;
          color: var(--secondary-text-color);
          margin-bottom: 4px;
        }
        .history-item {
          display: inline-block;
          font-size: 11px;
          padding: 2px 4px;
          margin-right: 4px;
          background: var(--divider-color);
          border-radius: 3px;
        }
        .more-indicator {
          margin-top: 12px;
          text-align: center;
          font-size: 12px;
          color: var(--secondary-text-color);
        }
      </style>
    `;
  }

  disconnectedCallback() {
    if (this._refreshInterval) clearInterval(this._refreshInterval);
  }

  getCardSize() {
    return Math.min(this._states.length, 20) / 2 + 3;
  }
}

customElements.define('pilotsuite-state-bridge-card', StateBridgeCard);
