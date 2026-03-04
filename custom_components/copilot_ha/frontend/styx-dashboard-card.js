/**
 * PilotSuite Styx — Dashboard Overview Card
 *
 * Displays a compact overview of the Styx system:
 * - Mood badge with confidence
 * - Neuron count (context/state/mood)
 * - Brain Graph stats (nodes/edges)
 * - Module states (active/learning/off chips)
 * - Integration Bus throughput
 *
 * Usage in Lovelace:
 *   type: custom:copilot-styx-dashboard-card
 *   entity: sensor.copilot_mood
 *   show_modules: true
 *   show_bus: true
 */

class CopilotStyxDashboardCard extends HTMLElement {
  setConfig(config) {
    this.config = config;
    this._refreshInterval = config.refresh_interval || 30;
    this._showModules = config.show_modules !== false;
    this._showBus = config.show_bus !== false;
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
        :host { display: block; }
        .card { background: var(--ha-card-background, #1a1a2e); border-radius: 12px; padding: 16px; color: var(--primary-text-color, #e0e0f0); font-family: var(--paper-font-body1_-_font-family, sans-serif); }
        .header { display: flex; align-items: center; gap: 8px; margin-bottom: 12px; }
        .header h3 { margin: 0; font-size: 1rem; font-weight: 600; flex: 1; }
        .mood-badge { padding: 3px 10px; border-radius: 16px; font-size: 0.8rem; font-weight: 600; text-transform: capitalize; }
        .mood-relax { background: #1a472a; color: #81c784; }
        .mood-focus { background: #1a2e4a; color: #4fc3f7; }
        .mood-active { background: #4a2a1a; color: #ffb74d; }
        .mood-sleep { background: #2a1a4a; color: #ce93d8; }
        .mood-alert { background: #4a1a1a; color: #ef5350; }
        .mood-away { background: #2a2a2a; color: #888; }
        .row { display: flex; justify-content: space-between; padding: 4px 0; font-size: 0.85rem; }
        .label { opacity: 0.6; }
        .value { font-weight: 500; font-variant-numeric: tabular-nums; }
        .section { margin-top: 10px; padding-top: 8px; border-top: 1px solid rgba(255,255,255,0.08); }
        .section-title { font-size: 0.75rem; text-transform: uppercase; opacity: 0.4; letter-spacing: 0.05em; margin-bottom: 6px; }
        .chips { display: flex; flex-wrap: wrap; gap: 4px; }
        .chip { padding: 2px 8px; border-radius: 10px; font-size: 0.7rem; display: flex; align-items: center; gap: 4px; }
        .chip .dot { width: 6px; height: 6px; border-radius: 50%; }
        .chip.active { background: rgba(129,199,132,0.15); }
        .chip.active .dot { background: #81c784; }
        .chip.learning { background: rgba(255,183,77,0.15); }
        .chip.learning .dot { background: #ffb74d; }
        .chip.off { background: rgba(239,83,80,0.15); }
        .chip.off .dot { background: #ef5350; }
        .bar { display: flex; align-items: center; gap: 6px; margin: 3px 0; }
        .bar-label { width: 70px; font-size: 0.75rem; opacity: 0.5; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
        .bar-track { flex: 1; height: 4px; background: rgba(255,255,255,0.06); border-radius: 2px; overflow: hidden; }
        .bar-fill { height: 100%; border-radius: 2px; transition: width 0.4s; }
        .bar-val { width: 30px; text-align: right; font-size: 0.72rem; opacity: 0.7; font-variant-numeric: tabular-nums; }
        .error { color: #ef5350; font-size: 0.8rem; padding: 8px; }
      </style>
      <ha-card>
        <div class="card">
          <div class="header">
            <h3>🧠 Styx</h3>
            <span class="mood-badge" id="mood">–</span>
          </div>
          <div id="content">Laden…</div>
        </div>
      </ha-card>
    `;
    this._fetchData();
    this._timer = setInterval(() => this._fetchData(), this._refreshInterval * 1000);
  }

  _updateFromHass() {
    const entity = this.config.entity || "sensor.copilot_mood";
    const state = this._hass?.states?.[entity];
    if (state) {
      const mood = state.state || "unknown";
      const el = this.shadowRoot.getElementById("mood");
      if (el) {
        el.textContent = mood;
        el.className = "mood-badge mood-" + mood.toLowerCase().replace(/[^a-z]/g, "");
      }
    }
  }

  async _fetchData() {
    try {
      const url = this._coreUrl + "/api/v1/styx/dashboard/compact";
      const resp = await fetch(url, {
        headers: this._hass ? { Authorization: "Bearer " + this._hass.auth.accessToken } : {},
      });
      if (!resp.ok) throw new Error("HTTP " + resp.status);
      const data = await resp.json();
      this._render(data);
    } catch (e) {
      // Silently fail - just keep showing last data
    }
  }

  _render(data) {
    const el = this.shadowRoot.getElementById("content");
    if (!el || !data.ok) return;

    let html = "";

    // Mood details
    if (data.mood?.mood_values) {
      const colors = { relax: "#81c784", focus: "#4fc3f7", active: "#ffb74d", sleep: "#ce93d8", alert: "#ef5350", away: "#888" };
      for (const [k, v] of Object.entries(data.mood.mood_values)) {
        const pct = Math.round(v * 100);
        html += `<div class="bar"><span class="bar-label">${k}</span><span class="bar-track"><span class="bar-fill" style="width:${pct}%;background:${colors[k] || '#4fc3f7'}"></span></span><span class="bar-val">${pct}%</span></div>`;
      }
    }

    // Bus
    if (this._showBus && data.bus) {
      html += `<div class="section"><div class="section-title">Integration Bus</div>`;
      html += `<div class="row"><span class="label">Events</span><span class="value">${data.bus.events_published || 0}</span></div>`;
      html += `<div class="row"><span class="label">Fehler</span><span class="value" style="color:${(data.bus.errors||0)>0?'#ef5350':'inherit'}">${data.bus.errors || 0}</span></div>`;
      html += `</div>`;
    }

    // Modules
    if (this._showModules && data.modules && Object.keys(data.modules).length > 0) {
      html += `<div class="section"><div class="section-title">Module</div><div class="chips">`;
      for (const [id, state] of Object.entries(data.modules)) {
        const label = id.replace(/_/g, " ").replace(/\b\w/g, c => c.toUpperCase());
        html += `<span class="chip ${state}"><span class="dot"></span>${label}</span>`;
      }
      html += `</div></div>`;
    }

    el.innerHTML = html;
  }

  static getConfigElement() {
    return document.createElement("copilot-styx-dashboard-editor");
  }

  static getStubConfig() {
    return { entity: "sensor.copilot_mood", show_modules: true, show_bus: true };
  }

  getCardSize() { return 4; }
}

customElements.define("copilot-styx-dashboard-card", CopilotStyxDashboardCard);
window.customCards = window.customCards || [];
window.customCards.push({
  type: "copilot-styx-dashboard-card",
  name: "PilotSuite Styx Dashboard",
  description: "Compact Styx system overview with mood, modules, and bus stats",
});
