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

class StyxChatCard extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: 'open' });
    this._config = {};
    this._hass = null;
    this._messages = [];
    this._loading = false;
    this._historyLoaded = false;
  }

  static getConfigElement() {
    return document.createElement('hui-generic-entity-row');
  }

  static getStubConfig() {
    return {
      title: 'Styx Chat',
      max_messages: 50,
      show_history: true,
    };
  }

  setConfig(config) {
    this._config = {
      title: config.title || 'Styx Chat',
      max_messages: config.max_messages || 50,
      show_history: config.show_history !== false,
      core_url: config.core_url || '',
      ...config,
    };
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

  _getCoreUrl() {
    if (this._config.core_url) return this._config.core_url;
    // Try to derive from known sensor
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
        content: e.name === 'AbortError' ? 'Zeitueberschreitung (30s).' : `Verbindungsfehler: ${e.message}`,
        timestamp: new Date().toLocaleTimeString('de-DE', { hour: '2-digit', minute: '2-digit' }),
      });
    }

    this._loading = false;
    this._renderTypingIndicator(false);
    this._renderMessages();
  }

  _esc(s) {
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
    this.shadowRoot.innerHTML = `
      <style>
        :host { display: block; }
        .card {
          background: var(--card-background-color, #1a1a2e);
          border-radius: var(--ha-card-border-radius, 12px);
          padding: 16px;
          color: var(--primary-text-color, #e6eef6);
          font-family: var(--paper-font-body1_-_font-family, system-ui, sans-serif);
          display: flex;
          flex-direction: column;
          height: 480px;
        }
        .header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 12px;
          flex-shrink: 0;
        }
        .title { font-size: 16px; font-weight: 600; }
        .status {
          font-size: 11px;
          color: var(--secondary-text-color, #9fb1c3);
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
        }
        .msg-user {
          background: rgba(79, 195, 247, 0.15);
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
          background: rgba(255, 152, 0, 0.1);
          border: 1px solid rgba(255, 152, 0, 0.2);
          margin: 0 auto;
          font-size: 12px;
          text-align: center;
        }
        .msg-header {
          display: flex;
          justify-content: space-between;
          margin-bottom: 4px;
        }
        .msg-role {
          font-size: 11px;
          font-weight: 600;
          color: var(--secondary-text-color, #9fb1c3);
        }
        .msg-time {
          font-size: 10px;
          color: var(--secondary-text-color, #9fb1c3);
          opacity: 0.7;
        }
        .msg-content {
          font-size: 13px;
          line-height: 1.5;
          white-space: pre-wrap;
        }
        .msg-meta {
          font-size: 10px;
          color: var(--secondary-text-color, #9fb1c3);
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
          background: var(--secondary-text-color, #9fb1c3);
          animation: bounce 1.4s infinite;
        }
        .typing-indicator span:nth-child(2) { animation-delay: 0.2s; }
        .typing-indicator span:nth-child(3) { animation-delay: 0.4s; }
        @keyframes bounce {
          0%, 80%, 100% { transform: scale(1); opacity: 0.4; }
          40% { transform: scale(1.3); opacity: 1; }
        }
        .typing-label {
          font-size: 11px;
          color: var(--secondary-text-color, #9fb1c3);
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
          color: var(--primary-text-color, #e6eef6);
          font-size: 13px;
          outline: none;
          transition: border-color 0.2s;
        }
        .input-area input:focus {
          border-color: rgba(79, 195, 247, 0.5);
        }
        .input-area input::placeholder {
          color: var(--secondary-text-color, #9fb1c3);
          opacity: 0.5;
        }
        .send-btn {
          padding: 8px 16px;
          border-radius: 20px;
          border: none;
          background: rgba(79, 195, 247, 0.2);
          color: #4fc3f7;
          cursor: pointer;
          font-size: 13px;
          font-weight: 600;
          transition: background 0.2s;
          flex-shrink: 0;
        }
        .send-btn:hover { background: rgba(79, 195, 247, 0.35); }
        .send-btn:disabled { opacity: 0.4; cursor: not-allowed; }
        .empty {
          text-align: center;
          color: var(--secondary-text-color, #9fb1c3);
          padding: 40px 0;
          font-size: 13px;
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
          <input type="text" placeholder="Nachricht eingeben..." />
          <button class="send-btn">Senden</button>
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

customElements.define('styx-chat-card', StyxChatCard);

window.customCards = window.customCards || [];
window.customCards.push({
  type: 'styx-chat-card',
  name: 'PilotSuite Styx Chat',
  description: 'Chat interface for PilotSuite Styx AI assistant',
});
