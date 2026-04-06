/**
 * PilotSuite Action Executor Card — Lovelace Custom Card
 * Displays and manages Actions with execution controls
 */

class ActionExecutorCard extends HTMLElement {
  constructor() {
    super();
    this._hass = null;
    this._config = null;
    this._actions = [];
    this._coreUrl = null;
  }

  setConfig(config) {
    this._config = config;
    this._coreUrl = config.core_url || 'http://localhost:8909';
    this._fetchActions();
    this._refreshInterval = setInterval(() => this._fetchActions(), 30000);
  }

  set hass(hass) {
    this._hass = hass;
  }

  async _fetchActions() {
    try {
      const response = await fetch(`${this._coreUrl}/api/v1/actions`);
      const data = await response.json();
      this._actions = data.actions || [];
      this._render();
    } catch (err) {
      console.error('Failed to fetch Actions:', err);
    }
  }

  async _handleExecute(actionId) {
    const result = await fetch(`${this._coreUrl}/api/v1/actions/${actionId}/execute`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' }
    });
    const data = await result.json();
    if (data.ok) {
      this._fetchActions();
    }
  }

  async _handleUndo(actionId) {
    const result = await fetch(`${this._coreUrl}/api/v1/actions/${actionId}/undo`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' }
    });
    const data = await result.json();
    alert(data.ok ? `✅ Undo erfolgreich (${data.restored_states} States)` : `❌ Fehler: ${data.error}`);
    this._fetchActions();
  }

  _render() {
    const summary = {
      total: this._actions.length,
      executions: this._actions.reduce((sum, a) => sum + (a.execution_count || 0), 0),
      withScript: this._actions.filter(a => a.ha_script_id).length
    };
    
    this.innerHTML = `
      <ha-card header="⚡ Action Executor">
        <div class="card-content">
          <div class="summary">
            <span class="stat">
              <span class="value">${summary.total}</span>
              <span class="label">Actions</span>
            </span>
            <span class="stat">
              <span class="value">${summary.executions}</span>
              <span class="label">Ausgeführt</span>
            </span>
            <span class="stat">
              <span class="value">${summary.withScript}</span>
              <span class="label">Mit Script</span>
            </span>
          </div>
          
          <div class="actions-list">
            ${this._actions.map(action => `
              <div class="action-item">
                <div class="action-header">
                  <span class="action-name">${action.name}</span>
                  <span class="action-count">▶️ ${action.execution_count || 0}x</span>
                </div>
                <div class="action-details">
                  ${action.ha_script_id ? 
                    `<span class="badge script">📜 ${action.ha_script_id}</span>` : ''}
                  ${action.target_devices?.length > 0 ? 
                    `<span class="badge devices">🔗 ${action.target_devices.length} Devices</span>` : ''}
                  ${action.last_executed ? 
                    `<span class="badge time">⏰ ${action.last_executed}</span>` : 
                    '<span class="badge never">Noch nie ausgeführt</span>'}
                </div>
                <div class="action-buttons">
                  <button class="btn execute" onclick="this.dispatchEvent(new CustomEvent('execute', {detail: '${action.action_id}'}))">
                    ▶️ Ausführen
                  </button>
                  ${action.undo_state?.length > 0 ? 
                    `<button class="btn undo" onclick="this.dispatchEvent(new CustomEvent('undo', {detail: '${action.action_id}'}))">
                      ↩️ Undo
                    </button>` : ''}
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
        .actions-list { display: grid; gap: 8px; }
        .action-item {
          padding: 12px;
          border: 1px solid var(--divider-color);
          border-radius: 8px;
          transition: all 0.2s;
        }
        .action-item:hover {
          border-color: var(--primary-color);
        }
        .action-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 8px;
        }
        .action-name { font-weight: bold; font-size: 15px; }
        .action-count {
          font-size: 12px;
          padding: 2px 8px;
          background: var(--secondary-background-color);
          border-radius: 4px;
        }
        .action-details {
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
        .badge.script {
          background: var(--accent-color);
        }
        .badge.devices {
          background: var(--secondary-background-color);
        }
        .badge.time {
          background: var(--secondary-background-color);
        }
        .badge.never {
          background: var(--secondary-background-color);
          color: var(--secondary-text-color);
        }
        .action-buttons {
          display: flex;
          gap: 8px;
        }
        .btn {
          padding: 8px 16px;
          border: none;
          border-radius: 4px;
          cursor: pointer;
          font-size: 13px;
        }
        .btn.execute {
          background: var(--primary-color);
          color: var(--text-primary-color);
          flex: 1;
        }
        .btn.undo {
          background: var(--secondary-background-color);
          color: var(--primary-color);
          border: 1px solid var(--primary-color);
        }
      </style>
    `;

    this.addEventListener('execute', (e) => this._handleExecute(e.detail));
    this.addEventListener('undo', (e) => this._handleUndo(e.detail));
  }

  disconnectedCallback() {
    if (this._refreshInterval) clearInterval(this._refreshInterval);
  }

  getCardSize() {
    return this._actions.length + 3;
  }
}

customElements.define('pilotsuite-action-executor-card', ActionExecutorCard);
