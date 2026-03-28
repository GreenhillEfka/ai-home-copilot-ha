/**
 * PilotSuite Styx Chat Card v1.0.0
 *
 * Lovelace custom card for embedded chat interface.
 * Communicates with PilotSuite Core via /api/styx/chat endpoint.
 *
 * Features:
 * - Message bubbles (user/assistant) with timestamps
 * - Text input with send button
 * - Typing indicator animation
 * - Chat history from /api/v1/conversation/history
 * - Auto-scroll to latest message
 */

const _ChatBase = window.StyxCoreApiCard || HTMLElement;

class StyxChatCard extends _ChatBase {
  constructor() {
    super();
    if (!this.shadowRoot) {
      this.attachShadow({ mode: 'open' });
      this._config = {};
      this._hass = null;
    }
    this._messages = [];
    this._loading = false;
    this._historyLoaded = false;
    // Bound refs for event listener cleanup
    this._sendHandler = null;
    this._keydownHandler = null;
    // Track abort controller for pending fetch requests
    this._historyCtrl = null;
    this._chatCtrl = null;
  }

  disconnectedCallback() {
    super.disconnectedCallback?.();
    // Remove dynamically attached shadow DOM listeners
    if (this.shadowRoot) {
      const btn = this.shadowRoot.querySelector('.send-btn');
      const input = this.shadowRoot.querySelector('.input-area input');
      if (btn && this._sendHandler) btn.removeEventListener('click', this._sendHandler);
      if (input && this._keydownHandler) input.removeEventListener('keydown', this._keydownHandler);
    }
    // Abort any in-flight fetch requests
    this._historyCtrl?.abort();
    this._chatCtrl?.abort();
  }

  static getConfigElement() {
    return super.getConfigElement?.() || document.createElement('hui-generic-entity-row');
  }

  static getStubConfig() {
    return {
      title: 'Styx Chat',
      max_messages: 50,
      show_history: true,
      core_url: '',
    };
  }

  static getConfigForm() {
    return [
      {
        name: 'title',
        label: 'Title',
        selector: 'text',
        placeholder: 'Styx Chat',
        help: 'Optional card title shown in the header.',
      },
      {
        name: 'core_url',
        label: 'Core URL',
        selector: 'text',
        placeholder: 'http://homeassistant.local:8909',
        help: 'Optional Core base URL override for chat endpoints.',
      },
      {
        name: 'max_messages',
        label: 'Max messages',
        selector: 'text',
        placeholder: '50',
        help: 'Maximum number of history messages to render.',
      },
      { name: 'show_history', label: 'Show history', selector: 'boolean', default: true },
    ];
  }

  static normalizeConfig(config = {}) {
    const defaults = this.getStubConfig();
    const normalize = window.styxNormalizeConfigWithSchema;
    const normalized = typeof normalize === 'function'
      ? normalize(config, this.getConfigForm(), defaults)
      : { ...defaults, ...(config || {}) };

    if (typeof normalized.title !== 'string') {
      normalized.title = defaults.title;
    }
    if (typeof normalized.core_url !== 'string') {
      normalized.core_url = defaults.core_url;
    }

    normalized.title = normalized.title.trim() || defaults.title;
    normalized.core_url = normalized.core_url.trim();

    const parsedMax = Number.parseInt(normalized.max_messages, 10);
    normalized.max_messages = Number.isFinite(parsedMax) && parsedMax > 0 ? parsedMax : defaults.max_messages;
    return normalized;
  }

  static validateConfig(config = {}) {
    const validate = window.styxValidateConfigWithSchema;
    const errors = typeof validate === 'function'
      ? validate(config, this.getConfigForm())
      : {};

    if (config.title !== undefined && typeof config.title !== 'string') {
      errors.title = 'title must be string';
    }
    if (config.core_url !== undefined && typeof config.core_url !== 'string') {
      errors.core_url = 'core_url must be string';
    }

    const rawMax = config.max_messages;
    if (rawMax !== undefined) {
      const parsed = Number.parseInt(rawMax, 10);
      if (!Number.isFinite(parsed) || parsed <= 0) {
        errors.max_messages = 'max_messages must be a positive integer';
      }
    }

    return errors;
  }

  setConfig(config) {
    const normalized = this.constructor.normalizeConfig(config);
    const errors = this.constructor.validateConfig(normalized);
    const errorList = Object.values(errors || {});
    if (errorList.length > 0) {
      throw new Error(errorList[0]);
    }

    if (typeof super.setConfig === 'function') {
      super.setConfig(normalized);
    } else {
      this._config = normalized;
    }
  }

  set hass(hass) {
    this._hass = hass;
    if (!this._historyLoaded) {
      this._historyLoaded = true;
      this._render();
      if (this._config.show_history) {
        this._loadHistory();
      }
    }
  }

  getCardSize() {
    return 6;
  }

  /* _getCoreUrl / _getToken inherited from StyxCoreApiCard if available */
  _getCoreUrl() {
    if (super._getCoreUrl) return super._getCoreUrl();
    if (this._config.core_url) return this._config.core_url;
    if (this._hass) {
      const apiSensor = this._hass.states['sensor.copilot_ha_core_api_v1'] ||
                        this._hass.states['sensor.pilotsuite_core_api_v1'];
      if (apiSensor && apiSensor.attributes && apiSensor.attributes.base_url) {
        return apiSensor.attributes.base_url;
      }
    }
    return 'http://homeassistant.local:8909';
  }

  _getToken() {
    if (super._getToken) return super._getToken();
    if (this._config.auth_token) return this._config.auth_token;
    if (this._hass && this._hass.auth && this._hass.auth.data) {
      return this._hass.auth.data.access_token || '';
    }
    return '';
  }

  async _loadHistory() {
    const url = this._getCoreUrl();
    const ctrl = new AbortController();
    const timer = setTimeout(() => ctrl.abort(), 10000);
    try {
      const resp = await fetch(`${url}/api/v1/conversation/history?limit=${this._config.max_messages}`, {
        headers: { 'X-Auth-Token': this._getToken() },
        signal: ctrl.signal,
      });
      clearTimeout(timer);
      if (resp.ok) {
        const data = await resp.json();
        if (data.ok && data.messages) {
          this._messages = data.messages.reverse().map(m => ({
            role: m.role,
            content: m.content,
            timestamp: m.timestamp ? new Date(m.timestamp * 1000).toLocaleTimeString('de-DE', { hour: '2-digit', minute: '2-digit' }) : '',
          }));
          this._renderMessages();
        }
      }
    } catch (e) {
      clearTimeout(timer);
    }
  }

  async _sendMessage(text) {
    if (!text.trim() || this._loading) return;

    this._messages.push({
      role: 'user',
      content: text,
      timestamp: new Date().toLocaleTimeString('de-DE', { hour: '2-digit', minute: '2-digit' }),
    });
    this._renderMessages();
    this._loading = true;
    this._renderTypingIndicator(true);

    const url = this._getCoreUrl();
    const ctrl = new AbortController();
    const timer = setTimeout(() => ctrl.abort(), 30000);
    try {
      const resp = await fetch(`${url}/api/styx/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Auth-Token': this._getToken(),
        },
        body: JSON.stringify({ query: text }),
        signal: ctrl.signal,
      });

      if (resp.ok) {
        const data = await resp.json();
        this._messages.push({
          role: 'assistant',
          content: data.response || data.message || 'Keine Antwort.',
          timestamp: new Date().toLocaleTimeString('de-DE', { hour: '2-digit', minute: '2-digit' }),
          sources: data.sources,
          query_type: data.query_type,
        });
      } else {
        this._messages.push({
          role: 'system',
          content: `Fehler: ${resp.status} ${resp.statusText}`,
          timestamp: new Date().toLocaleTimeString('de-DE', { hour: '2-digit', minute: '2-digit' }),
        });
      }
    } catch (e) {
      clearTimeout(timer);
      this._messages.push({
        role: 'system',
        content: e.name === 'AbortError' ? 'Zeitüberschreitung (30s).' : `Verbindungsfehler: ${e.message}`,
        timestamp: new Date().toLocaleTimeString('de-DE', { hour: '2-digit', minute: '2-digit' }),
      });
    }

    this._loading = false;
    this._renderTypingIndicator(false);
    this._renderMessages();
  }

  _esc(s) {
    if (typeof window.styxEsc === 'function') return window.styxEsc(s);
    const el = document.createElement('span');
    el.textContent = s;
    return el.innerHTML;
  }

  _renderTypingIndicator(show) {
    const indicator = this.shadowRoot.querySelector('.typing-indicator');
    if (indicator) {
      indicator.style.display = show ? 'flex' : 'none';
    }
  }

  _renderMessages() {
    const container = this.shadowRoot.querySelector('.messages');
    if (!container) return;

    const msgs = this._messages.slice(-this._config.max_messages);
    container.innerHTML = msgs.map(m => {
      const cls = m.role === 'user' ? 'msg-user' : m.role === 'assistant' ? 'msg-assistant' : 'msg-system';
      const label = m.role === 'user' ? 'Du' : m.role === 'assistant' ? 'Styx' : 'System';
      return `
        <div class="msg ${cls}">
          <div class="msg-header">
            <span class="msg-role">${label}</span>
            <span class="msg-time">${this._esc(m.timestamp || '')}</span>
          </div>
          <div class="msg-content">${this._esc(m.content)}</div>
          ${m.sources ? `<div class="msg-meta">${m.sources.length} Quelle(n) | ${m.query_type || ''}</div>` : ''}
        </div>`;
    }).join('');

    container.scrollTop = container.scrollHeight;
  }

  _render() {
    const designTokens = typeof this._designTokens === 'function' ? this._designTokens() : '';
    this.shadowRoot.innerHTML = `
      <style>
        ${designTokens}
        :host {
          display: block;
          --ps-accent: var(--accent-color, #4fc3f7);
          --ps-bg: var(--card-background-color, var(--ha-card-background, #1a1a2e));
          --ps-surface: var(--secondary-background-color, #222240);
          --ps-text: var(--primary-text-color, #e0e0f0);
          --ps-text-secondary: var(--secondary-text-color, #9e9eb8);
          --ps-radius: var(--ha-card-border-radius, 12px);
          --ps-transition: 0.2s ease;
        }
        .card {
          background: var(--ps-bg);
          border-radius: var(--ps-radius);
          padding: 16px;
          color: var(--ps-text);
          font-family: var(--paper-font-body1_-_font-family, system-ui, sans-serif);
          display: flex;
          flex-direction: column;
          height: min(480px, 60vh);
        }
        .header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 12px;
          flex-shrink: 0;
        }
        .title { font-size: 0.9375rem; font-weight: 600; }
        .status {
          font-size: 0.75rem;
          color: var(--ps-text-secondary);
        }
        .messages {
          flex: 1;
          overflow-y: auto;
          padding: 4px 0;
          scroll-behavior: smooth;
        }
        .messages::-webkit-scrollbar { width: 4px; }
        .messages::-webkit-scrollbar-thumb {
          background: rgba(255,255,255,0.15);
          border-radius: 2px;
        }
        .msg {
          margin-bottom: 10px;
          padding: 8px 12px;
          border-radius: 12px;
          max-width: 85%;
          word-wrap: break-word;
          transition: opacity var(--ps-transition);
        }
        .msg-user {
          background: linear-gradient(135deg, rgba(79,195,247,0.18), rgba(79,195,247,0.08));
          border: 1px solid rgba(79, 195, 247, 0.3);
          margin-left: auto;
          border-bottom-right-radius: 4px;
        }
        .msg-assistant {
          background: rgba(255, 255, 255, 0.06);
          border: 1px solid rgba(255, 255, 255, 0.1);
          margin-right: auto;
          border-bottom-left-radius: 4px;
        }
        .msg-system {
          background: rgba(255, 183, 77, 0.1);
          border: 1px solid rgba(255, 183, 77, 0.2);
          margin: 0 auto;
          font-size: 0.8125rem;
          text-align: center;
        }
        .msg-header {
          display: flex;
          justify-content: space-between;
          margin-bottom: 4px;
        }
        .msg-role {
          font-size: 0.75rem;
          font-weight: 600;
          color: var(--ps-text-secondary);
        }
        .msg-time {
          font-size: 0.75rem;
          color: var(--ps-text-secondary);
          opacity: 0.7;
        }
        .msg-content {
          font-size: 0.875rem;
          line-height: 1.5;
          white-space: pre-wrap;
        }
        .msg-meta {
          font-size: 0.75rem;
          color: var(--ps-text-secondary);
          margin-top: 4px;
          opacity: 0.6;
        }
        .typing-indicator {
          display: none;
          align-items: center;
          gap: 4px;
          padding: 8px 12px;
          margin-bottom: 8px;
        }
        .typing-indicator span {
          display: inline-block;
          width: 6px;
          height: 6px;
          border-radius: 50%;
          background: var(--ps-accent);
          animation: bounce 1.4s infinite;
        }
        .typing-indicator span:nth-child(2) { animation-delay: 0.2s; }
        .typing-indicator span:nth-child(3) { animation-delay: 0.4s; }
        @keyframes bounce {
          0%, 80%, 100% { transform: scale(1); opacity: 0.4; }
          40% { transform: scale(1.3); opacity: 1; }
        }
        .typing-label {
          font-size: 0.8125rem;
          color: var(--ps-text-secondary);
          margin-left: 4px;
        }
        .input-area {
          display: flex;
          gap: 8px;
          margin-top: 8px;
          flex-shrink: 0;
        }
        .input-area input {
          flex: 1;
          padding: 10px 14px;
          border-radius: 20px;
          border: 1px solid rgba(255,255,255,0.15);
          background: rgba(255,255,255,0.06);
          color: var(--ps-text);
          font-size: 0.875rem;
          outline: none;
          transition: border-color var(--ps-transition), box-shadow var(--ps-transition);
        }
        .input-area input:focus {
          border-color: var(--ps-accent);
          box-shadow: 0 0 0 2px rgba(79, 195, 247, 0.15);
        }
        .input-area input::placeholder {
          color: var(--ps-text-secondary);
          opacity: 0.5;
        }
        .send-btn {
          padding: 8px 16px;
          border-radius: 20px;
          border: none;
          background: rgba(79, 195, 247, 0.2);
          color: var(--ps-accent);
          cursor: pointer;
          font-size: 0.875rem;
          font-weight: 600;
          transition: background var(--ps-transition);
          flex-shrink: 0;
        }
        .send-btn:hover { background: rgba(79, 195, 247, 0.35); }
        .send-btn:disabled { opacity: 0.4; cursor: not-allowed; }
        .empty {
          text-align: center;
          color: var(--ps-text-secondary);
          padding: 40px 0;
          font-size: 0.875rem;
        }
      </style>
      <div class="card">
        <div class="header">
          <span class="title">${this._esc(this._config.title)}</span>
          <span class="status">${this._messages.length} Nachrichten</span>
        </div>
        <div class="messages">
          <div class="empty">Starte eine Unterhaltung mit Styx...</div>
        </div>
        <div class="typing-indicator">
          <span></span><span></span><span></span>
          <span class="typing-label">Styx denkt nach...</span>
        </div>
        <div class="input-area">
          <input type="text" placeholder="Nachricht eingeben..." aria-label="Chat-Nachricht" />
          <button class="send-btn" aria-label="Nachricht senden">Senden</button>
        </div>
      </div>`;

    const input = this.shadowRoot.querySelector('.input-area input');
    const btn = this.shadowRoot.querySelector('.send-btn');

    const send = () => {
      const text = input.value.trim();
      if (text) {
        this._sendMessage(text);
        input.value = '';
      }
    };

    btn.addEventListener('click', send);
    input.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') send();
    });

    if (this._messages.length > 0) {
      this._renderMessages();
    }
  }
}

if (typeof registerStyxCard === 'function') {
  registerStyxCard('styx-chat-card', StyxChatCard, {
    name: 'PilotSuite Styx Chat',
    description: 'Chat-Interface fuer den PilotSuite Styx KI-Assistenten',
  });
} else {
  customElements.define('styx-chat-card', StyxChatCard);
  window.customCards = window.customCards || [];
  window.customCards.push({
    type: 'styx-chat-card',
    name: 'PilotSuite Styx Chat',
    description: 'Chat-Interface fuer den PilotSuite Styx KI-Assistenten',
  });
}
