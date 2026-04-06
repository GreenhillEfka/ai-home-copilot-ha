/**
 * PilotSuite Predictive Card — Lovelace Custom Card
 * Shows ML-generated patterns and rule suggestions
 */
class PredictiveCard extends HTMLElement {
  constructor() { super(); this._patterns = []; this._suggestions = []; }
  setConfig(config) { this._config = config; this._fetch(); setInterval(() => this._fetch(), 60000); }
  async _fetch() {
    const [pR, sR] = await Promise.all([
      fetch(`${this._config.core_url}/api/v1/predictive/patterns`),
      fetch(`${this._config.core_url}/api/v1/predictive/suggestions`)
    ]);
    const [pD, sD] = await Promise.all([pR.json(), sR.json()]);
    this._patterns = pD.patterns || [];
    this._suggestions = sD.suggestions || [];
    this._render();
  }
  async _acceptSuggestion(id) {
    await fetch(`${this._config.core_url}/api/v1/predictive/suggestions/${id}/accept`, {method: 'POST'});
    this._fetch();
  }
  _render() {
    this.innerHTML = `
      <ha-card header="🧠 Predictive Symbiosis">
        <div class="card-content">
          <div style="display:flex;gap:16px;margin-bottom:16px;">
            <div style="text-align:center;flex:1;"><div style="font-size:24px;font-weight:bold;">${this._patterns.length}</div><div style="font-size:12px;">Patterns</div></div>
            <div style="text-align:center;flex:1;"><div style="font-size:24px;font-weight:bold;">${this._suggestions.length}</div><div style="font-size:12px;">Suggestions</div></div>
          </div>
          ${this._suggestions.length > 0 ? `<h4>Rule Suggestions</h4>` : ''}
          ${this._suggestions.map(s => `
            <div style="padding:12px;border:1px solid var(--primary-color);border-radius:8px;margin-bottom:8px;">
              <b>${s.pattern_id}</b><br/>
              <small>Confidence: ${Math.round(s.confidence*100)}%</small><br/>
              <button onclick="this.dispatchEvent(new CustomEvent('accept', {detail: '${s.pattern_id}'}))" style="margin-top:8px;padding:6px 12px;background:var(--primary-color);color:white;border:none;border-radius:4px;cursor:pointer;">✅ Accept</button>
            </div>
          `).join('')}
          ${this._patterns.length > 0 ? `<h4>Active Patterns</h4>` : ''}
          ${this._patterns.slice(0, 5).map(p => `
            <div style="padding:8px;border-bottom:1px solid #eee;font-size:13px;">
              <b>${p.pattern_id}</b> <span style="float:right;">${p.frequency}x @ ${Math.round(p.confidence*100)}%</span>
            </div>
          `).join('')}
        </div>
      </ha-card>`;
    this.addEventListener('accept', (e) => this._acceptSuggestion(e.detail));
  }
}
customElements.define('pilotsuite-predictive-card', PredictiveCard);
