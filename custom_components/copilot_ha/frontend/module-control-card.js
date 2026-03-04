/**
 * PilotSuite Styx — Module Control Card
 *
 * Interactive card for viewing and toggling module states
 * (active/learning/off) via the Core REST API.
 *
 * Usage in Lovelace:
 *   type: custom:copilot-module-control-card
 *   core_url: /api/copilot_proxy
 */

class CopilotModuleControlCard extends HTMLElement {
  setConfig(config) {
    this.config = config;
    this._coreUrl = config.core_url || "/api/copilot_proxy";
  }

  set hass(hass) {
    this._hass = hass;
    if (!this._initialized) {
      this._initialize();
      this._initialized = true;
    }
  }

  _initialize() {
    this.attachShadow({ mode: "open" });
    this.shadowRoot.innerHTML = `
      <style>
        :host { display: block; }
        .card { background: var(--ha-card-background, #1a1a2e); border-radius: 12px; padding: 16px; color: var(--primary-text-color, #e0e0f0); font-family: var(--paper-font-body1_-_font-family, sans-serif); }
        .header { display: flex; align-items: center; gap: 8px; margin-bottom: 12px; }
        .header h3 { margin: 0; font-size: 1rem; font-weight: 600; flex: 1; }
        .module { display: flex; align-items: center; gap: 10px; padding: 8px 0; border-bottom: 1px solid rgba(255,255,255,0.05); }
        .module:last-child { border-bottom: none; }
        .mod-icon { font-size: 1.1rem; width: 28px; text-align: center; }
        .mod-info { flex: 1; min-width: 0; }
        .mod-name { font-size: 0.85rem; font-weight: 500; }
        .mod-desc { font-size: 0.7rem; opacity: 0.4; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
        .state-btn { border: none; padding: 4px 10px; border-radius: 12px; font-size: 0.72rem; font-weight: 600; cursor: pointer; transition: all 0.2s; min-width: 60px; text-align: center; }
        .state-btn:hover { filter: brightness(1.2); }
        .state-btn.active { background: rgba(129,199,132,0.2); color: #81c784; }
        .state-btn.learning { background: rgba(255,183,77,0.2); color: #ffb74d; }
        .state-btn.off { background: rgba(239,83,80,0.2); color: #ef5350; }
        .toast { position: fixed; bottom: 20px; left: 50%; transform: translateX(-50%); background: #333; color: #fff; padding: 8px 16px; border-radius: 8px; font-size: 0.8rem; opacity: 0; transition: opacity 0.3s; z-index: 1000; pointer-events: none; }
        .toast.show { opacity: 1; }
      </style>
      <ha-card>
        <div class="card">
          <div class="header">
            <h3>🔧 Module</h3>
          </div>
          <div id="modules">Laden…</div>
        </div>
        <div class="toast" id="toast"></div>
      </ha-card>
    `;
    this._fetchModules();
  }

  async _fetchModules() {
    try {
      const url = this._coreUrl + "/api/v1/styx/config";
      const resp = await fetch(url, {
        headers: this._hass ? { Authorization: "Bearer " + this._hass.auth.accessToken } : {},
      });
      if (!resp.ok) throw new Error("HTTP " + resp.status);
      const data = await resp.json();
      this._renderModules(data.modules || []);
    } catch (e) {
      this.shadowRoot.getElementById("modules").innerHTML =
        '<div style="opacity:0.4;font-size:0.85rem">Module nicht verfügbar</div>';
    }
  }

  _renderModules(modules) {
    const el = this.shadowRoot.getElementById("modules");
    const states = ["active", "learning", "off"];
    const stateLabels = { active: "Aktiv", learning: "Lernen", off: "Aus" };

    el.innerHTML = modules.map(m => {
      const nextState = states[(states.indexOf(m.state) + 1) % states.length];
      return `<div class="module">
        <span class="mod-icon">${m.icon ? this._mdiToEmoji(m.icon) : "⚙️"}</span>
        <div class="mod-info">
          <div class="mod-name">${m.label}</div>
          <div class="mod-desc">${m.description || ""}</div>
        </div>
        <button class="state-btn ${m.state}" data-id="${m.id}" data-next="${nextState}">
          ${stateLabels[m.state] || m.state}
        </button>
      </div>`;
    }).join("");

    el.querySelectorAll(".state-btn").forEach(btn => {
      btn.addEventListener("click", () => this._toggleModule(btn.dataset.id, btn.dataset.next));
    });
  }

  async _toggleModule(moduleId, newState) {
    try {
      const url = this._coreUrl + `/api/v1/modules/${moduleId}/configure`;
      const resp = await fetch(url, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(this._hass ? { Authorization: "Bearer " + this._hass.auth.accessToken } : {}),
        },
        body: JSON.stringify({ state: newState }),
      });
      if (!resp.ok) throw new Error("HTTP " + resp.status);
      this._showToast(`${moduleId} → ${newState}`);
      this._fetchModules();
    } catch (e) {
      this._showToast("Fehler: " + e.message);
    }
  }

  _showToast(msg) {
    const toast = this.shadowRoot.getElementById("toast");
    toast.textContent = msg;
    toast.classList.add("show");
    setTimeout(() => toast.classList.remove("show"), 2000);
  }

  _mdiToEmoji(icon) {
    const map = {
      "mdi:emoticon": "🎭", "mdi:pickaxe": "⛏️", "mdi:brain": "🧠",
      "mdi:chart-timeline-variant-shimmer": "📊", "mdi:swap-horizontal": "🔄",
      "mdi:school": "🎓", "mdi:lightbulb-on": "💡", "mdi:solar-power": "☀️",
      "mdi:microphone": "🎤", "mdi:alert-circle": "⚠️",
    };
    return map[icon] || "⚙️";
  }

  static getStubConfig() { return {}; }
  getCardSize() { return 5; }
}

customElements.define("copilot-module-control-card", CopilotModuleControlCard);
window.customCards = window.customCards || [];
window.customCards.push({
  type: "copilot-module-control-card",
  name: "PilotSuite Module Control",
  description: "Interactive module state control (active/learning/off)",
});
