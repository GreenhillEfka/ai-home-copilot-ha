/**
 * PilotSuite Event Bus Card — Lovelace Custom Card
 */
class EventBusCard extends HTMLElement {
  constructor() { super(); this._events = []; }
  setConfig(config) { this._config = config; this._fetch(); setInterval(() => this._fetch(), 5000); }
  async _fetch() {
    const r = await fetch(`${this._config.core_url}/api/v1/events/recent?limit=10`);
    const d = await r.json();
    this._events = d.events || [];
    this._render();
  }
  _render() {
    this.innerHTML = `
      <ha-card header="📡 Event Bus">
        <div class="card-content">
          ${this._events.reverse().map(e => `
            <div style="font-size:11px; border-bottom:1px solid #eee; padding:4px;">
              <b>${e.event_type}</b> <i style="color:gray">${e.source}</i><br/>
              <pre style="margin:2px 0; font-size:9px;">${JSON.stringify(e.payload)}</pre>
            </div>
          `).join('')}
        </div>
      </ha-card>`;
  }
}
customElements.define('pilotsuite-event-bus-card', EventBusCard);
