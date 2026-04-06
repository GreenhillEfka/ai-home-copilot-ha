/**
 * PilotSuite Learning Memory Card — Lovelace Custom Card
 */
class LearningMemoryCard extends HTMLElement {
  constructor() { super(); this._patterns = []; }
  setConfig(config) { this._config = config; this._fetch(); setInterval(() => this._fetch(), 30000); }
  async _fetch() {
    const r = await fetch(`${this._config.core_url}/api/v1/memory/patterns`);
    const d = await r.json();
    this._patterns = d.patterns || [];
    this._render();
  }
  _render() {
    this.innerHTML = `
      <ha-card header="🧠 Learning Memory">
        <div class="card-content">
          <div style="display:flex;gap:16px;margin-bottom:12px;">
            <div style="text-align:center;flex:1;"><div style="font-size:24px;font-weight:bold;">${this._patterns.length}</div><div style="font-size:12px;">Patterns</div></div>
            <div style="text-align:center;flex:1;"><div style="font-size:24px;font-weight:bold;">${this._patterns.filter(p=>p.confidence>0.8).length}</div><div style="font-size:12px;">High Conf</div></div>
          </div>
          ${this._patterns.slice(0, 10).map(p => `
            <div style="padding:8px;border-bottom:1px solid #eee;font-size:13px;">
              <b>${p.pattern_id}</b> <span style="float:right;">${Math.round(p.confidence*100)}%</span><br/>
              <small style="color:gray">Freq: ${p.frequency}</small>
            </div>
          `).join('')}
        </div>
      </ha-card>`;
  }
}
customElements.define('pilotsuite-learning-memory-card', LearningMemoryCard);
