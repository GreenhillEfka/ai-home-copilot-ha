/**
 * PilotSuite Styx — Habitus Zone Configuration Card
 *
 * Displays all Habitus zones with icons, names, priorities, and
 * zone metrics. Supports zone-level entity assignment viewing.
 *
 * Usage in Lovelace:
 *   type: custom:copilot-habitus-zone-card
 *   entity: sensor.pilotsuite_habitus_zones
 *   show_metrics: true
 *   locale: de
 */

class CopilotHabitusZoneCard extends HTMLElement {
  setConfig(config) {
    this.config = config;
    this._locale = config.locale || "de";
    this._showMetrics = config.show_metrics !== false;
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
        .count { font-size: 0.8rem; opacity: 0.5; }
        .zone { display: flex; align-items: center; gap: 10px; padding: 8px 0; border-bottom: 1px solid rgba(255,255,255,0.05); }
        .zone:last-child { border-bottom: none; }
        .zone-icon { font-size: 1.3rem; width: 32px; text-align: center; }
        .zone-info { flex: 1; min-width: 0; }
        .zone-name { font-size: 0.88rem; font-weight: 500; }
        .zone-desc { font-size: 0.72rem; opacity: 0.45; margin-top: 1px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
        .zone-prio { font-size: 0.7rem; opacity: 0.4; padding: 2px 6px; border-radius: 8px; background: rgba(255,255,255,0.05); }
        .metrics { display: flex; gap: 8px; margin-top: 4px; }
        .metric { font-size: 0.7rem; opacity: 0.5; }
        .metric-val { font-weight: 600; opacity: 0.8; }
      </style>
      <ha-card>
        <div class="card">
          <div class="header">
            <h3>🏠 Habitus-Zonen</h3>
            <span class="count" id="count"></span>
          </div>
          <div id="zones">Laden…</div>
        </div>
      </ha-card>
    `;
    this._fetchZones();
  }

  async _fetchZones() {
    try {
      const url = this._coreUrl + "/api/v1/habitus/zones?include_metrics=" + this._showMetrics;
      const resp = await fetch(url, {
        headers: this._hass ? { Authorization: "Bearer " + this._hass.auth.accessToken } : {},
      });
      if (!resp.ok) throw new Error("HTTP " + resp.status);
      const data = await resp.json();
      this._renderZones(data);
    } catch (e) {
      this.shadowRoot.getElementById("zones").innerHTML =
        '<div style="opacity:0.4;font-size:0.85rem">Zonen nicht verfügbar</div>';
    }
  }

  _renderZones(data) {
    const zones = data.zones || [];
    const el = this.shadowRoot.getElementById("zones");
    const countEl = this.shadowRoot.getElementById("count");
    countEl.textContent = zones.length + " Zonen";

    const icons = {
      living: "🛋️", bath: "🚿", kitchen: "🍳", office: "💼", hallway: "🚪",
      bedroom: "🛏️", room_mira: "👧", room_paul: "👦", terrace: "🌿", outside: "🌳",
      kino: "🎬", gaming: "🎮", fitness: "💪", home_office: "🖥️", wellness: "🧖",
      meditation: "🧘", arbeitsraum: "🔧",
    };

    el.innerHTML = zones.map(z => {
      const name = this._locale === "de" ? (z.name_de || z.id) : (z.name_en || z.id);
      const icon = icons[z.id] || z.icon || "🏠";
      let metricsHtml = "";
      if (this._showMetrics && z.metrics) {
        const m = z.metrics;
        const parts = [];
        if (m.entity_count > 0) parts.push(`<span class="metric"><span class="metric-val">${m.entity_count}</span> Geräte</span>`);
        if (m.occupancy) parts.push(`<span class="metric"><span class="metric-val">●</span> Anwesend</span>`);
        if (m.avg_temperature != null) parts.push(`<span class="metric"><span class="metric-val">${m.avg_temperature}°C</span></span>`);
        if (parts.length) metricsHtml = `<div class="metrics">${parts.join("")}</div>`;
      }
      return `<div class="zone">
        <span class="zone-icon">${icon}</span>
        <div class="zone-info">
          <div class="zone-name">${name}</div>
          <div class="zone-desc">${z.description || ""}</div>
          ${metricsHtml}
        </div>
        <span class="zone-prio">P${z.priority || 0}</span>
      </div>`;
    }).join("");
  }

  static getStubConfig() {
    return { entity: "sensor.pilotsuite_habitus_zones", show_metrics: true, locale: "de" };
  }

  getCardSize() { return Math.max(2, Math.ceil((this._zones || 5) / 3)); }
}

customElements.define("copilot-habitus-zone-card", CopilotHabitusZoneCard);
window.customCards = window.customCards || [];
window.customCards.push({
  type: "copilot-habitus-zone-card",
  name: "PilotSuite Habitus Zones",
  description: "Habitus zone overview with metrics and entity counts",
});
