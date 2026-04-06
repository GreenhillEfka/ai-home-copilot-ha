/**
 * PilotSuite Intent Manager Card — Lovelace Custom Card
 * Displays and manages Intents with resolution testing
 */

class IntentManagerCard extends HTMLElement {
  constructor() {
    super();
    this._hass = null;
    this._config = null;
    this._intents = [];
    this._coreUrl = null;
  }

  setConfig(config) {
    this._config = config;
    this._coreUrl = config.core_url || 'http://localhost:8909';
    this._fetchIntents();
    this._refreshInterval = setInterval(() => this._fetchIntents(), 30000);
  }

  set hass(hass) {
    this._hass = hass;
  }

  async _fetchIntents() {
    try {
      const response = await fetch(`${this._coreUrl}/api/v1/intents`);
      const data = await response.json();
      this._intents = data.intents || [];
      this._render();
    } catch (err) {
      console.error('Failed to fetch Intents:', err);
    }
  }

  async _testResolution(phrase) {
    const result = await fetch(`${this._coreUrl}/api/v1/intents/resolve`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ phrase })
    });
    const data = await result.json();
    alert(data.resolved ? 
      `✅ Intent gefunden: ${data.intent.name} (${Math.round(data.confidence * 100)}%)` : 
      `❌ Kein Intent gefunden`);
  }

  _render() {
    const summary = {
      total: this._intents.length,
      active: this._intents.filter(i => i.active !== false).length,
      withScript: this._intents.filter(i => i.ha_script_id).length
    };
    
    this.innerHTML = `
      <ha-card header="🎯 Intent Manager">
        <div class="card-content">
          <div class="summary">
            <span class="stat">
              <span class="value">${summary.total}</span>
              <span class="label">Intents</span>
            </span>
            <span class="stat">
              <span class="value">${summary.active}</span>
              <span class="label">Aktiv</span>
            </span>
            <span class="stat">
              <span class="value">${summary.withScript}</span>
              <span class="label">Mit Script</span>
            </span>
          </div>
          
          <div class="test-section">
            <input type="text" class="test-input" id="testPhrase" placeholder="Test-Phrase eingeben..." />
            <button class="btn test-btn" onclick="this.dispatchEvent(new CustomEvent('test-resolution'))">
              🔍 Testen
            </button>
          </div>
          
          <div class="intents-list">
            ${this._intents.map(intent => `
              <div class="intent-item ${intent.active !== false ? 'active' : 'inactive'}">
                <div class="intent-header">
                  <span class="intent-name">${intent.name}</span>
                  <span class="intent-status ${intent.active !== false ? 'on' : 'off'}">
                    ${intent.active !== false ? '● AKTIV' : '○ INAKTIV'}
                  </span>
                </div>
                <div class="intent-details">
                  <div class="trigger-phrases">
                    <span class="label">Trigger:</span>
                    ${intent.trigger_phrases?.map(p => `<span class="badge">"${p}"</span>`).join('') || '<span class="empty">Keine Trigger</span>'}
                  </div>
                  ${intent.ha_script_id ? 
                    `<span class="badge script">📜 ${intent.ha_script_id}</span>` : ''}
                  ${intent.zone_ref ? 
                    `<span class="badge zone">📍 ${intent.zone_ref}</span>` : ''}
                  <span class="badge confidence">🎯 ${intent.confidence_threshold * 100}%</span>
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
        .test-section {
          display: flex;
          gap: 8px;
          margin-bottom: 16px;
        }
        .test-input {
          flex: 1;
          padding: 10px 12px;
          border: 1px solid var(--divider-color);
          border-radius: 6px;
          background: var(--secondary-background-color);
          color: var(--primary-text-color);
          font-size: 14px;
        }
        .test-btn {
          padding: 10px 20px;
          background: var(--primary-color);
          color: var(--text-primary-color);
          border: none;
          border-radius: 6px;
          cursor: pointer;
          font-size: 14px;
        }
        .intents-list { display: grid; gap: 8px; }
        .intent-item {
          padding: 12px;
          border: 1px solid var(--divider-color);
          border-radius: 8px;
          transition: all 0.2s;
        }
        .intent-item.active {
          border-color: var(--accent-color);
        }
        .intent-item.inactive {
          opacity: 0.6;
        }
        .intent-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 8px;
        }
        .intent-name { font-weight: bold; font-size: 15px; }
        .intent-status {
          font-size: 11px;
          padding: 2px 6px;
          border-radius: 4px;
          font-weight: bold;
        }
        .intent-status.on {
          background: var(--accent-color);
          color: var(--text-primary-color);
        }
        .intent-status.off {
          background: var(--secondary-background-color);
          color: var(--secondary-text-color);
        }
        .intent-details {
          display: flex;
          flex-direction: column;
          gap: 8px;
        }
        .trigger-phrases {
          display: flex;
          flex-wrap: wrap;
          gap: 6px;
          align-items: center;
        }
        .trigger-phrases .label {
          font-size: 12px;
          color: var(--secondary-text-color);
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
        .badge.zone {
          background: var(--secondary-background-color);
        }
        .badge.confidence {
          background: var(--secondary-background-color);
          align-self: flex-start;
        }
        .empty {
          font-size: 12px;
          color: var(--secondary-text-color);
        }
      </style>
    `;

    this.addEventListener('test-resolution', () => {
      const input = this.querySelector('#testPhrase');
      if (input.value) {
        this._testResolution(input.value);
      }
    });
  }

  disconnectedCallback() {
    if (this._refreshInterval) clearInterval(this._refreshInterval);
  }

  getCardSize() {
    return this._intents.length + 3;
  }
}

customElements.define('pilotsuite-intent-manager-card', IntentManagerCard);
