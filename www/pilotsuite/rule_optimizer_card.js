/**
 * PilotSuite Rule Optimizer Card — Lovelace Custom Card
 * Shows rule scores and optimization suggestions
 */
class RuleOptimizerCard extends HTMLElement {
  constructor() { super(); this._scores = []; this._suggestions = []; }
  setConfig(config) { this._config = config; this._fetch(); setInterval(() => this._fetch(), 60000); }
  async _fetch() {
    const [scR, sgR] = await Promise.all([
      fetch(`${this._config.core_url}/api/v1/optimizer/scores`),
      fetch(`${this._config.core_url}/api/v1/optimizer/suggestions`)
    ]);
    const [scD, sgD] = await Promise.all([scR.json(), sgR.json()]);
    this._scores = scD.scores || [];
    this._suggestions = sgD.suggestions || [];
    this._render();
  }
  async _submitFeedback(ruleId, useful) {
    await fetch(`${this._config.core_url}/api/v1/optimizer/feedback`, {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({rule_id: ruleId, was_useful: useful})
    });
    this._fetch();
  }
  _render() {
    this.innerHTML = `
      <ha-card header="⚡ Rule Optimizer">
        <div class="card-content">
          ${this._suggestions.length > 0 ? `<div style="padding:12px;background:rgba(255,193,7,0.2);border-radius:8px;margin-bottom:16px;"><b>⚠️ ${this._suggestions.length} Optimization Suggestions</b></div>` : ''}
          <h4>Rule Scores</h4>
          ${this._scores.slice(0, 10).map(s => `
            <div style="padding:8px;border-bottom:1px solid #eee;display:flex;justify-content:space-between;align-items:center;">
              <div>
                <b>${s.rule_id}</b><br/>
                <small>Score: ${s.score} | Exec: ${s.execution_count}</small>
              </div>
              <div>
                <button onclick="this.dispatchEvent(new CustomEvent('feedback', {detail: {rule: '${s.rule_id}', useful: true}}))" style="padding:4px 8px;background:#4caf50;color:white;border:none;border-radius:4px;cursor:pointer;">👍</button>
                <button onclick="this.dispatchEvent(new CustomEvent('feedback', {detail: {rule: '${s.rule_id}', useful: false}}))" style="padding:4px 8px;background:#f44336;color:white;border:none;border-radius:4px;cursor:pointer;margin-left:4px;">👎</button>
              </div>
            </div>
          `).join('')}
        </div>
      </ha-card>`;
    this.addEventListener('feedback', (e) => this._submitFeedback(e.detail.rule, e.detail.useful));
  }
}
customElements.define('pilotsuite-rule-optimizer-card', RuleOptimizerCard);
