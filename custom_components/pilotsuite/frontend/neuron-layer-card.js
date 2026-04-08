/**
 * PilotSuite Styx — Neuron Layer Lovelace Card
 *
 * Displays the 3-layer neural pipeline (Context → State → Mood)
 * with live neuron values, synapse connections, and dominant mood.
 *
 * Usage in Lovelace:
 *   type: custom:copilot-neuron-layer-card
 *   entity: sensor.copilot_mood
 *   refresh_interval: 30
 */

class CopilotNeuronLayerCard extends HTMLElement {
  static get properties() {
    return {
      hass: {},
      config: {},
    };
  }

  setConfig(config) {
    this.config = config;
    this._refreshInterval = config.refresh_interval || 30;
    this._coreUrl = config.core_url || "/api/copilot_proxy";
  }

  set hass(hass) {
    this._hass = hass;
    if (!this._initialized) {
      this._initialize();
      this._initialized = true;
    }
    this._updateFromHass();
  }

  _initialize() {
    this.attachShadow({ mode: "open" });
    this.shadowRoot.innerHTML = `
      <style>
        :host {
          display: block;
        }
        .card {
          background: var(--ha-card-background, var(--card-background-color, #1c1c1c));
          border-radius: var(--ha-card-border-radius, 12px);
          padding: 16px;
          color: var(--primary-text-color, #e1e1e1);
          font-family: var(--paper-font-body1_-_font-family, 'Roboto', sans-serif);
        }
        .header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 12px;
        }
        .title {
          font-size: 16px;
          font-weight: 500;
        }
        .mood-badge {
          background: var(--primary-color, #03a9f4);
          color: white;
          padding: 4px 12px;
          border-radius: 16px;
          font-size: 12px;
          font-weight: 600;
          text-transform: uppercase;
        }
        .svg-container {
          width: 100%;
          overflow-x: auto;
        }
        .svg-container svg {
          width: 100%;
          height: auto;
        }
        .stats {
          display: flex;
          gap: 16px;
          margin-top: 12px;
          font-size: 12px;
          opacity: 0.7;
        }
        .stat {
          display: flex;
          align-items: center;
          gap: 4px;
        }
        .dot {
          width: 8px;
          height: 8px;
          border-radius: 50%;
          display: inline-block;
        }
        .dot-green { background: #34D399; }
        .dot-amber { background: #FBBF24; }
        .dot-red { background: #F87171; }
        .dot-purple { background: #8B5CF6; }
        .loading {
          text-align: center;
          padding: 40px;
          opacity: 0.5;
        }
        .error {
          text-align: center;
          padding: 20px;
          color: var(--error-color, #db4437);
          font-size: 13px;
        }
      </style>
      <ha-card>
        <div class="card">
          <div class="header">
            <span class="title">Neural Pipeline</span>
            <span class="mood-badge" id="mood-badge">—</span>
          </div>
          <div class="svg-container" id="svg-container">
            <div class="loading">Loading neural pipeline...</div>
          </div>
          <div class="stats" id="stats">
            <div class="stat"><span class="dot dot-green"></span> Excitatory</div>
            <div class="stat"><span class="dot dot-red"></span> Inhibitory</div>
            <div class="stat"><span class="dot dot-purple"></span> Dominant</div>
          </div>
        </div>
      </ha-card>
    `;
    this._fetchVisualization();
    this._timer = setInterval(() => this._fetchVisualization(), this._refreshInterval * 1000);
  }

  _updateFromHass() {
    if (!this._hass || !this.config.entity) return;
    const state = this._hass.states[this.config.entity];
    if (state) {
      const badge = this.shadowRoot.getElementById("mood-badge");
      if (badge) badge.textContent = state.state || "—";
    }
  }

  async _fetchVisualization() {
    try {
      const resp = await fetch(`${this._coreUrl}/api/v1/neurons/layers/snapshot.svg`);
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
      const svg = await resp.text();
      const container = this.shadowRoot.getElementById("svg-container");
      if (container) container.innerHTML = svg;
    } catch (err) {
      const container = this.shadowRoot.getElementById("svg-container");
      if (container) {
        container.innerHTML = `<div class="error">Cannot load: ${err.message}</div>`;
      }
    }
  }

  disconnectedCallback() {
    if (this._timer) {
      clearInterval(this._timer);
      this._timer = null;
    }
  }

  getCardSize() {
    return 5;
  }

  static getStubConfig() {
    return {
      entity: "sensor.copilot_mood",
      refresh_interval: 30,
    };
  }
}

customElements.define("copilot-neuron-layer-card", CopilotNeuronLayerCard);

window.customCards = window.customCards || [];
window.customCards.push({
  type: "copilot-neuron-layer-card",
  name: "Copilot Neuron Layer",
  description: "Visualizes the PilotSuite Styx neural pipeline with 3 layers",
  preview: true,
});
