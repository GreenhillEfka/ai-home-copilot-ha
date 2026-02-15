// Lovelace Custom Cards for Mood, Neurons, and Habitus
import { LitElement, html, css, nothing } from 'lit';
import { customElement, property, state } from 'lit/decorators.js';
import { HomeAssistant } from 'custom-card-helpers';

/**
 * Mood Card - Displays current mood context with visualization
 */
@customElement('ha-copilot-mood-card')
export class HaCopilotMoodCard extends LitElement {
  @property({ attribute: false }) public hass!: HomeAssistant;
  @property() public entity?: string;
  @property() public title?: string;
  @property({ type: Number }) public show_emotions?: number;
  
  @state() private mood?: any;
  @state() private emotions: any[] = [];

  public setConfig(config: any): void {
    if (!config.entity) {
      throw new Error('Mood card requires an entity');
    }
    this.entity = config.entity;
    this.title = config.title;
    this.show_emotions = config.show_emotions || 3;
  }

  public static getStubConfig(hass: HomeAssistant, entities: string[]): any {
    const entitiesList = entities.filter(ent => ent.includes('mood'));
    return { entity: entitiesList[0] || 'mood.current' };
  }

  protected firstUpdated(): void {
    this._updateMood();
  }

  protected updated(changedProps: any): void {
    if (changedProps.has('hass') || changedProps.has('entity')) {
      this._updateMood();
    }
  }

  private _updateMood(): void {
    if (!this.entity) return;
    
    const stateObj = this.hass.states[this.entity];
    if (!stateObj) return;

    this.mood = stateObj;
    this.emotions = this._parseEmotions(stateObj);
  }

  private _parseEmotions(stateObj: any): any[] {
    const emotions = stateObj.attributes?.emotions || [];
    
    if (Array.isArray(emotions)) {
      return emotions.slice(0, this.show_emotions);
    }
    
    if (typeof emotions === 'object' && emotions !== null) {
      return Object.entries(emotions)
        .slice(0, this.show_emotions)
        .map(([name, value]: [string, any]) => ({ name, value }));
    }
    
    return [];
  }

  protected render(): any {
    if (!this.mood) {
      return html`<div class="card">
        <ha-card .header="${this.title || 'Mood'}">
          <div class="content">No mood data available</div>
        </ha-card>
      </div>`;
    }

    return html`
      <div class="card">
        <ha-card .header="${this.title || 'Mood'}">
          <div class="content">
            <div class="mood-display">
              <div class="mood-icon">
                ${this._getMoodEmoji(this.mood.state)}
              </div>
              <div class="mood-text">
                <span class="primary">${this.mood.state}</span>
                ${this._renderConfidence()}
              </div>
            </div>
            
            <div class="emotions">
              ${this.emotions.map((emotion: any) => html`
                <div class="emotion-bar">
                  <span class="emotion-name">${emotion.name}</span>
                  <div class="emotion-progress">
                    <div class="emotion-fill" style="width: ${emotion.value * 100}%"></div>
                  </div>
                  <span class="emotion-value">${(emotion.value * 100).toFixed(0)}%</span>
                </div>
              `)}
            </div>

            ${this._renderTimestamp()}
          </div>
        </ha-card>
      </div>
    `;
  }

  private _getMoodEmoji(mood: string): string {
    const emojis: Record<string, string> = {
      'happy': '😊',
      'sad': '😢',
      'angry': '😠',
      'excited': '⚡',
      'calm': '🌿',
      'neutral': '😐',
      'focused': '🎯',
      'creative': '🎨',
      'tired': '😴',
      'hungry': '🍽️'
    };
    return emojis[mood] || '🙂';
  }

  private _renderConfidence(): any {
    const confidence = this.mood.attributes?.confidence;
    if (!confidence) return nothing;
    
    return html`<span class="confidence">(${(confidence * 100).toFixed(0)}% confident)</span>`;
  }

  private _renderTimestamp(): any {
    const lastUpdated = this.mood.attributes?.last_updated;
    if (!lastUpdated) return nothing;
    
    const time = new Date(lastUpdated).toLocaleTimeString('de-DE', { hour: '2-digit', minute: '2-digit' });
    return html`<div class="timestamp">Last updated: ${time}</div>`;
  }

  static get styles(): any {
    return css`
      .card {
        width: 100%;
      }
      
      .content {
        padding: 16px;
      }
      
      .mood-display {
        display: flex;
        align-items: center;
        gap: 16px;
        margin-bottom: 20px;
      }
      
      .mood-icon {
        font-size: 48px;
        line-height: 1;
      }
      
      .mood-text {
        flex: 1;
      }
      
      .primary {
        font-size: 24px;
        font-weight: bold;
        color: var(--primary-text-color);
      }
      
      .confidence {
        color: var(--secondary-text-color);
        font-size: 14px;
      }
      
      .emotions {
        margin-top: 20px;
      }
      
      .emotion-bar {
        display: flex;
        align-items: center;
        gap: 12px;
        margin-bottom: 8px;
      }
      
      .emotion-name {
        width: 100px;
        font-size: 14px;
        color: var(--primary-text-color);
      }
      
      .emotion-progress {
        flex: 1;
        height: 8px;
        background: var(--divider-color);
        border-radius: 4px;
        overflow: hidden;
      }
      
      .emotion-fill {
        height: 100%;
        background: var(--primary-color);
        border-radius: 4px;
        transition: width 0.3s ease;
      }
      
      .emotion-value {
        width: 50px;
        text-align: right;
        font-size: 14px;
        color: var(--secondary-text-color);
      }
      
      .timestamp {
        margin-top: 16px;
        text-align: right;
        font-size: 12px;
        color: var(--secondary-text-color);
      }
    `;
  }
}

/**
 * Neurons Card - Displays neuron status and activity
 */
@customElement('ha-copilot-neurons-card')
export class HaCopilotNeuronsCard extends LitElement {
  @property({ attribute: false }) public hass!: HomeAssistant;
  @property() public entity?: string;
  @property() public title?: string;
  
  @state() private neurons?: any;

  public setConfig(config: any): void {
    if (!config.entity) {
      throw new Error('Neurons card requires an entity');
    }
    this.entity = config.entity;
    this.title = config.title;
  }

  public static getStubConfig(hass: HomeAssistant, entities: string[]): any {
    const entitiesList = entities.filter(ent => ent.includes('neuron'));
    return { entity: entitiesList[0] || 'sensor.neuron_activity' };
  }

  protected firstUpdated(): void {
    this._updateNeurons();
  }

  protected updated(changedProps: any): void {
    if (changedProps.has('hass') || changedProps.has('entity')) {
      this._updateNeurons();
    }
  }

  private _updateNeurons(): void {
    if (!this.entity) return;
    
    const stateObj = this.hass.states[this.entity];
    if (!stateObj) return;

    this.neurons = stateObj;
  }

  protected render(): any {
    if (!this.neurons) {
      return html`<div class="card">
        <ha-card .header="${this.title || 'Neurons'}">
          <div class="content">No neuron data available</div>
        </ha-card>
      </div>`;
    }

    const activity = this.neurons.attributes?.activity || [];
    const activeCount = activity.filter((item: any) => item.active).length;
    const totalCount = activity.length;

    return html`
      <div class="card">
        <ha-card .header="${this.title || 'Neurons'}">
          <div class="content">
            <div class="status-row">
              <div class="status-item">
                <span class="label">Active</span>
                <span class="value active">${activeCount}</span>
              </div>
              <div class="status-item">
                <span class="label">Total</span>
                <span class="value">${totalCount}</span>
              </div>
              <div class="status-item">
                <span class="label">Activity</span>
                <span class="value">${this.neurons.state}</span>
              </div>
            </div>

            <div class="activity-grid">
              ${activity.map((item: any, index: number) => html`
                <div class="neuron-item ${item.active ? 'active' : ''}">
                  <div class="neuron-icon">
                    ${item.active ? '⚡' : '•'}
                  </div>
                  <div class="neuron-info">
                    <div class="neuron-name">${item.name}</div>
                    <div class="neuron-status">${item.active ? 'Active' : 'Idle'}</div>
                  </div>
                </div>
              `)}
            </div>

            ${this._renderActivityGraph()}
          </div>
        </ha-card>
      </div>
    `;
  }

  private _renderActivityGraph(): any {
    const history = this.neurons.attributes?.history || [];
    
    if (history.length < 2) return nothing;

    const maxActivity = Math.max(...history.map((h: any) => h.value), 1);
    
    return html`
      <div class="activity-chart">
        <div class="chart-label">Activity History</div>
        <div class="chart-bars">
          ${history.map((item: any, index: number) => html`
            <div class="chart-bar" style="height: ${(item.value / maxActivity) * 100}%">
              <div class="chart-tooltip">${item.value} activity</div>
            </div>
          `)}
        </div>
      </div>
    `;
  }

  static get styles(): any {
    return css`
      .card {
        width: 100%;
      }
      
      .content {
        padding: 16px;
      }
      
      .status-row {
        display: flex;
        justify-content: space-around;
        margin-bottom: 24px;
      }
      
      .status-item {
        text-align: center;
      }
      
      .label {
        display: block;
        font-size: 12px;
        color: var(--secondary-text-color);
        margin-bottom: 4px;
      }
      
      .value {
        font-size: 20px;
        font-weight: bold;
        color: var(--primary-text-color);
      }
      
      .value.active {
        color: var(--success-color);
      }
      
      .activity-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
        gap: 12px;
        margin-bottom: 24px;
      }
      
      .neuron-item {
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 8px;
        background: var(--card-background-color);
        border-radius: 8px;
        transition: all 0.3s ease;
      }
      
      .neuron-item.active {
        background: rgba(76, 175, 80, 0.1);
        border: 1px solid var(--success-color);
      }
      
      .neuron-icon {
        font-size: 16px;
      }
      
      .neuron-info {
        flex: 1;
      }
      
      .neuron-name {
        font-size: 14px;
        font-weight: 500;
        color: var(--primary-text-color);
      }
      
      .neuron-status {
        font-size: 12px;
        color: var(--secondary-text-color);
      }
      
      .activity-chart {
        margin-top: 20px;
      }
      
      .chart-label {
        font-size: 14px;
        color: var(--secondary-text-color);
        margin-bottom: 8px;
      }
      
      .chart-bars {
        display: flex;
        align-items: flex-end;
        gap: 4px;
        height: 60px;
      }
      
      .chart-bar {
        flex: 1;
        background: linear-gradient(180deg, var(--primary-color) 0%, var(--secondary-color) 100%);
        border-radius: 2px 2px 0 0;
        position: relative;
        transition: height 0.3s ease;
      }
      
      .chart-tooltip {
        position: absolute;
        top: -24px;
        left: 50%;
        transform: translateX(-50%);
        font-size: 12px;
        background: rgba(0, 0, 0, 0.8);
        color: white;
        padding: 4px 8px;
        border-radius: 4px;
        white-space: nowrap;
        opacity: 0;
        transition: opacity 0.3s ease;
      }
      
      .chart-bar:hover .chart-tooltip {
        opacity: 1;
      }
    `;
  }
}

/**
 * Habitus Card - Displays habitus zones and behaviors
 */
@customElement('ha-copilot-habitus-card')
export class HaCopilotHabitusCard extends LitElement {
  @property({ attribute: false }) public hass!: HomeAssistant;
  @property() public entity?: string;
  @property() public title?: string;
  
  @state() private habitus?: any;
  @state() private selectedZone?: string;

  public setConfig(config: any): void {
    if (!config.entity) {
      throw new Error('Habitus card requires an entity');
    }
    this.entity = config.entity;
    this.title = config.title;
  }

  public static getStubConfig(hass: HomeAssistant, entities: string[]): any {
    const entitiesList = entities.filter(ent => ent.includes('habitus'));
    return { entity: entitiesList[0] || 'habitus.current' };
  }

  protected firstUpdated(): void {
    this._updateHabitus();
  }

  protected updated(changedProps: any): void {
    if (changedProps.has('hass') || changedProps.has('entity')) {
      this._updateHabitus();
    }
  }

  private _updateHabitus(): void {
    if (!this.entity) return;
    
    const stateObj = this.hass.states[this.entity];
    if (!stateObj) return;

    this.habitus = stateObj;
  }

  protected render(): any {
    if (!this.habitus) {
      return html`<div class="card">
        <ha-card .header="${this.title || 'Habitus'}">
          <div class="content">No habitus data available</div>
        </ha-card>
      </div>`;
    }

    const zones = this.habitus.attributes?.zones || [];
    const currentZone = zones.find((z: any) => z.active) || zones[0];

    return html`
      <div class="card">
        <ha-card .header="${this.title || 'Habitus'}">
          <div class="content">
            <div class="zone-selector">
              ${zones.map((zone: any) => html`
                <button 
                  class="zone-btn ${zone.id === currentZone?.id ? 'active' : ''}"
                  @click="${() => this._selectZone(zone.id)}"
                >
                  ${zone.name}
                </button>
              `)}
            </div>

            ${currentZone ? html`
              <div class="zone-content">
                <div class="zone-header">
                  <div class="zone-icon">🏠</div>
                  <div class="zone-info">
                    <div class="zone-name">${currentZone.name}</div>
                    <div class="zone-description">${currentZone.description}</div>
                  </div>
                </div>

                ${currentZone.settings ? html`
                  <div class="zone-settings">
                    <div class="setting-item">
                      <span class="setting-label">Ambience</span>
                      <span class="setting-value">${currentZone.settings.ambience || 'Normal'}</span>
                    </div>
                    <div class="setting-item">
                      <span class="setting-label">Activity</span>
                      <span class="setting-value">${currentZone.settings.activity || 'Resting'}</span>
                    </div>
                    <div class="setting-item">
                      <span class="setting-label">Optimization</span>
                      <span class="setting-value">${currentZone.settings.optimization || 'Balanced'}</span>
                    </div>
                  </div>
                ` : nothing}

                ${currentZone.mood ? html`
                  <div class="zone-mood">
                    <div class="mood-label">Current Mood</div>
                    <div class="mood-bar">
                      <div class="mood-fill" style="width: ${currentZone.mood.intensity * 100}%"></div>
                    </div>
                    <div class="mood-text">${currentZone.mood.type}</div>
                  </div>
                ` : nothing}
              </div>
            ` : nothing}

            ${this._renderBehaviorHistory()}
          </div>
        </ha-card>
      </div>
    `;
  }

  private _selectZone(zoneId: string): void {
    this.selectedZone = zoneId;
    
    // Emit event for external listeners
    this.dispatchEvent(new CustomEvent('zone-selected', {
      detail: { zoneId },
      bubbles: true,
      composed: true
    }));
  }

  private _renderBehaviorHistory(): any {
    const behaviors = this.habitus.attributes?.behaviors || [];
    
    if (!behaviors || behaviors.length === 0) return nothing;

    return html`
      <div class="behavior-history">
        <div class="behavior-title">Recent Behaviors</div>
        <div class="behavior-list">
          ${behaviors.slice(0, 5).map((behavior: any, index: number) => html`
            <div class="behavior-item">
              <div class="behavior-icon">
                ${this._getBehaviorIcon(behavior.type)}
              </div>
              <div class="behavior-info">
                <div class="behavior-name">${behavior.name}</div>
                <div class="behavior-time">${new Date(behavior.timestamp).toLocaleTimeString('de-DE', { hour: '2-digit', minute: '2-digit' })}</div>
              </div>
            </div>
          `)}
        </div>
      </div>
    `;
  }

  private _getBehaviorIcon(type: string): string {
    const icons: Record<string, string> = {
      'sleep': '💤',
      'work': '💻',
      'relax': '🛋️',
      'social': '👥',
      'creative': '🎨',
      'exercise': '🏃',
      'learning': '📚',
      'eating': '🍽️'
    };
    return icons[type] || '⏰';
  }

  static get styles(): any {
    return css`
      .card {
        width: 100%;
      }
      
      .content {
        padding: 16px;
      }
      
      .zone-selector {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
        margin-bottom: 24px;
      }
      
      .zone-btn {
        padding: 8px 16px;
        background: var(--card-background-color);
        border: 1px solid var(--divider-color);
        border-radius: 20px;
        cursor: pointer;
        font-size: 14px;
        color: var(--primary-text-color);
        transition: all 0.3s ease;
      }
      
      .zone-btn.active {
        background: var(--primary-color);
        color: white;
        border-color: var(--primary-color);
      }
      
      .zone-content {
        margin-bottom: 24px;
      }
      
      .zone-header {
        display: flex;
        align-items: center;
        gap: 16px;
        margin-bottom: 16px;
      }
      
      .zone-icon {
        font-size: 32px;
      }
      
      .zone-info {
        flex: 1;
      }
      
      .zone-name {
        font-size: 20px;
        font-weight: bold;
        color: var(--primary-text-color);
      }
      
      .zone-description {
        font-size: 14px;
        color: var(--secondary-text-color);
      }
      
      .zone-settings {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
        gap: 16px;
        margin-bottom: 16px;
      }
      
      .setting-item {
        display: flex;
        flex-direction: column;
        gap: 4px;
      }
      
      .setting-label {
        font-size: 12px;
        color: var(--secondary-text-color);
      }
      
      .setting-value {
        font-size: 14px;
        font-weight: 500;
        color: var(--primary-text-color);
      }
      
      .zone-mood {
        margin-top: 16px;
      }
      
      .mood-label {
        font-size: 14px;
        color: var(--secondary-text-color);
        margin-bottom: 8px;
      }
      
      .mood-bar {
        height: 8px;
        background: var(--divider-color);
        border-radius: 4px;
        overflow: hidden;
        margin-bottom: 8px;
      }
      
      .mood-fill {
        height: 100%;
        background: linear-gradient(90deg, var(--primary-color), var(--secondary-color));
        border-radius: 4px;
        transition: width 0.3s ease;
      }
      
      .mood-text {
        font-size: 14px;
        color: var(--primary-text-color);
        font-weight: 500;
      }
      
      .behavior-history {
        margin-top: 24px;
      }
      
      .behavior-title {
        font-size: 14px;
        color: var(--secondary-text-color);
        margin-bottom: 12px;
      }
      
      .behavior-list {
        display: flex;
        flex-direction: column;
        gap: 8px;
      }
      
      .behavior-item {
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 8px;
        background: var(--card-background-color);
        border-radius: 8px;
      }
      
      .behavior-icon {
        font-size: 20px;
      }
      
      .behavior-info {
        flex: 1;
      }
      
      .behavior-name {
        font-size: 14px;
        font-weight: 500;
        color: var(--primary-text-color);
      }
      
      .behavior-time {
        font-size: 12px;
        color: var(--secondary-text-color);
      }
    `;
  }
}

// Register all custom elements
declare global {
  interface HTMLElementTagNameMap {
    'ha-copilot-mood-card': HaCopilotMoodCard;
    'ha-copilot-neurons-card': HaCopilotNeuronsCard;
    'ha-copilot-habitus-card': HaCopilotHabitusCard;
  }
}
