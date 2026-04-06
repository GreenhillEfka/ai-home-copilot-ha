/**
 * Styx Sonos Card - Lovelace Card für Sonos/Musikwolke Steuerung
 * 
 * Features:
 * - Zone-basierte Sonos-Steuerung
 * - Musikwolke (Multi-Room-Gruppen)
 * - Volume Control mit Slider
 * - Play/Pause/Next/Previous
 * - Favoriten-Auswahl
 * - TTS (Say) Funktion
 */

import { LitElement, html, css } from 'https://unpkg.com/lit@2.7.3/index.js?module';

class StyxSonosCard extends LitElement {
  static get properties() {
    return {
      hass: {},
      config: {},
      _sonosStatus: { state: true },
      _zoneMap: { state: true },
      _favorites: { state: true },
      _loading: { state: true },
      _error: { state: true },
    };
  }

  constructor() {
    super();
    this._sonosStatus = null;
    this._zoneMap = {};
    this._favorites = [];
    this._loading = false;
    this._error = null;
    this._refreshInterval = null;
  }

  setConfig(config) {
    this.config = {
      title: '🎵 Sonos Steuerung',
      show_volume: true,
      show_favorites: true,
      show_tts: true,
      show_musikwolke: true,
      refresh_interval: 10000,
      ...config,
    };
  }

  connectedCallback() {
    super.connectedCallback();
    this._startRefresh();
  }

  disconnectedCallback() {
    super.disconnectedCallback();
    this._stopRefresh();
  }

  _startRefresh() {
    this._refreshData();
    if (this.config.refresh_interval > 0) {
      this._refreshInterval = setInterval(
        () => this._refreshData(),
        this.config.refresh_interval
      );
    }
  }

  _stopRefresh() {
    if (this._refreshInterval) {
      clearInterval(this._refreshInterval);
      this._refreshInterval = null;
    }
  }

  async _refreshData() {
    if (!this.hass) return;

    this._loading = true;
    try {
      // Sonos Status
      const statusResponse = await this.hass.callApi(
        'GET',
        'api/copilot_ha/sonos/status'
      );
      this._sonosStatus = statusResponse;

      // Zone Map
      const zoneMapResponse = await this.hass.callApi(
        'GET',
        'api/copilot_ha/musikwolke/zone-map'
      );
      this._zoneMap = zoneMapResponse.zone_speaker_map || {};

      // Favorites
      if (this.config.show_favorites) {
        const favResponse = await this.hass.callApi(
          'GET',
          'api/copilot_ha/sonos/favorites'
        );
        this._favorites = favResponse.favorites || [];
      }

      this._error = null;
    } catch (err) {
      this._error = err.message || 'Fehler beim Laden der Sonos-Daten';
      console.error('Styx Sonos Card error:', err);
    } finally {
      this._loading = false;
    }
  }

  _callService(service, data = {}) {
    if (!this.hass) return;

    this.hass.callApi('POST', `api/copilot_ha/sonos/${service}`, data)
      .then(() => {
        setTimeout(() => this._refreshData(), 500);
      })
      .catch(err => {
        console.error(`Sonos ${service} failed:`, err);
        this._error = `Fehler bei ${service}: ${err.message}`;
      });
  }

  _callMusikwolke(service, data = {}) {
    if (!this.hass) return;

    this.hass.callApi('POST', `api/copilot_ha/musikwolke/${service}`, data)
      .then(() => {
        setTimeout(() => this._refreshData(), 500);
      })
      .catch(err => {
        console.error(`Musikwolke ${service} failed:`, err);
        this._error = `Fehler bei ${service}: ${err.message}`;
      });
  }

  _handlePlay(room) {
    this._callService('play', { room });
  }

  _handlePause(room) {
    this._callService('pause', { room });
  }

  _handleVolume(room, volume) {
    this._callService('volume', { room, volume: parseInt(volume) });
  }

  _handleFavorite(room, favoriteName) {
    this._callService('favorite/play', { room, name: favoriteName });
  }

  _handleSay(room, text) {
    if (!text) return;
    this._callService('say', { room, text, language: 'de-de', volume: 40 });
  }

  _handleCreateMusikwolke() {
    const rooms = Object.values(this._zoneMap);
    if (rooms.length < 2) {
      this._error = 'Mindestens 2 Räume für Musikwolke benötigt';
      return;
    }
    this._callMusikwolke('create', { zone_ids: Object.keys(this._zoneMap) });
  }

  _handleDissolveMusikwolke() {
    const rooms = Object.values(this._zoneMap);
    this._callMusikwolke('dissolve', { zone_ids: Object.keys(this._zoneMap) });
  }

  render() {
    if (this._loading && !this._sonosStatus) {
      return html`
        <ha-card header="${this.config.title}">
          <div class="card-content">
            <ha-circular-progress active></ha-circular-progress>
            <p>Lade Sonos-Daten...</p>
          </div>
        </ha-card>
      `;
    }

    if (this._error && !this._sonosStatus) {
      return html`
        <ha-card header="${this.config.title}">
          <div class="card-content error">
            <ha-icon icon="mdi:alert-circle"></ha-icon>
            <p>${this._error}</p>
            <mwc-button @click="${() => this._refreshData()}">
              Erneut versuchen
            </mwc-button>
          </div>
        </ha-card>
      `;
    }

    const speakers = this._sonosStatus?.speakers || [];
    const activeZones = this._sonosStatus?.active_zones || [];

    return html`
      <ha-card header="${this.config.title}">
        <div class="card-content">
          ${this._error ? html`
            <div class="error-banner">
              <ha-icon icon="mdi:alert-circle"></ha-icon>
              <span>${this._error}</span>
              <mwc-button dense @click="${() => this._error = null}">
                Schließen
              </mwc-button>
            </div>
          ` : ''}

          ${this.config.show_musikwolke ? this._renderMusikwolkeSection(activeZones) : ''}
          
          ${this._renderSpeakersSection(speakers)}
          
          ${this.config.show_favorites && this._favorites.length > 0 
            ? this._renderFavoritesSection() 
            : ''}
        </div>
      </ha-card>
    `;
  }

  _renderMusikwolkeSection(activeZones) {
    const isMusikwolkeActive = activeZones.length > 1;

    return html`
      <div class="section musikwolke">
        <div class="section-header">
          <ha-icon icon="mdi:cloud-music"></ha-icon>
          <span>Musikwolke</span>
          ${isMusikwolkeActive 
            ? html`<span class="badge">${activeZones.length} Zonen</span>` 
            : ''}
        </div>
        <div class="button-row">
          <mwc-button 
            raised 
            ?disabled="${isMusikwolkeActive || Object.keys(this._zoneMap).length < 2}"
            @click="${() => this._handleCreateMusikwolke()}"
          >
            <ha-icon icon="mdi:plus"></ha-icon>
            Musikwolke starten
          </mwc-button>
          <mwc-button 
            outlined
            ?disabled="${!isMusikwolkeActive}"
            @click="${() => this._handleDissolveMusikwolke()}"
          >
            <ha-icon icon="mdi:close"></ha-icon>
            Auflösen
          </mwc-button>
        </div>
      </div>
    `;
  }

  _renderSpeakersSection(speakers) {
    if (speakers.length === 0) {
      return html`
        <div class="section">
          <div class="section-header">
            <ha-icon icon="mdi:speaker"></ha-icon>
            <span>Sonos Speaker</span>
          </div>
          <p class="no-data">Keine Sonos Speaker gefunden</p>
        </div>
      `;
    }

    return html`
      <div class="section">
        <div class="section-header">
          <ha-icon icon="mdi:speaker"></ha-icon>
          <span>Sonos Speaker (${speakers.length})</span>
        </div>
        <div class="speakers-grid">
          ${speakers.map(speaker => this._renderSpeaker(speaker))}
        </div>
      </div>
    `;
  }

  _renderSpeaker(speaker) {
    const isPlaying = speaker.state === 'playing';
    const volume = speaker.volume || 0;
    const track = speaker.track || {};
    const room = speaker.room_name || 'Unbekannt';

    return html`
      <div class="speaker-card ${isPlaying ? 'playing' : ''}">
        <div class="speaker-header">
          <ha-icon icon="${isPlaying ? 'mdi:speaker' : 'mdi:speaker-off'}"></ha-icon>
          <span class="room-name">${room}</span>
        </div>
        
        ${track.title ? html`
          <div class="track-info">
            <div class="track-title">${track.title}</div>
            ${track.artist ? html`<div class="track-artist">${track.artist}</div>` : ''}
          </div>
        ` : html`<div class="track-info"><span class="no-track">Keine Wiedergabe</span></div>`}

        ${this.config.show_volume ? html`
          <div class="volume-control">
            <ha-icon icon="mdi:volume-high"></ha-icon>
            <input 
              type="range" 
              min="0" 
              max="100" 
              value="${volume}"
              @input="${(e) => this._handleVolume(room, e.target.value)}"
              class="volume-slider"
            />
            <span class="volume-value">${volume}%</span>
          </div>
        ` : ''}

        <div class="button-row">
          ${isPlaying 
            ? html`
                <mwc-icon-button 
                  icon="mdi:pause"
                  @click="${() => this._handlePause(room)}"
                ></mwc-icon-button>
              ` 
            : html`
                <mwc-icon-button 
                  icon="mdi:play"
                  @click="${() => this._handlePlay(room)}"
                ></mwc-icon-button>
              `
          }
          <mwc-icon-button 
            icon="mdi:skip-previous"
            @click="${() => this._callService('previous', { room })}"
          ></mwc-icon-button>
          <mwc-icon-button 
            icon="mdi:skip-next"
            @click="${() => this._callService('next', { room })}"
          ></mwc-icon-button>
        </div>

        ${this.config.show_favorites && this._favorites.length > 0 ? html`
          <div class="favorites-select">
            <select 
              @change="${(e) => this._handleFavorite(room, e.target.value)}"
            >
              <option value="">Favorit wählen...</option>
              ${this._favorites.map(fav => html`
                <option value="${fav.name}">${fav.name}</option>
              `)}
            </select>
          </div>
        ` : ''}

        ${this.config.show_tts ? html`
          <div class="tts-input">
            <ha-textfield
              placeholder="Durchsage..."
              outlined
              dense
              @keydown="${(e) => {
                if (e.key === 'Enter') {
                  this._handleSay(room, e.target.value);
                  e.target.value = '';
                }
              }}"
            ></ha-textfield>
            <mwc-icon-button 
              icon="mdi:record-voice-over"
              @click="${(e) => {
                const input = e.target.parentElement.querySelector('ha-textfield');
                this._handleSay(room, input.value);
                input.value = '';
              }}"
            ></mwc-icon-button>
          </div>
        ` : ''}
      </div>
    `;
  }

  _renderFavoritesSection() {
    return html`
      <div class="section">
        <div class="section-header">
          <ha-icon icon="mdi:heart"></ha-icon>
          <span>Favoriten</span>
        </div>
        <div class="favorites-list">
          ${this._favorites.map(fav => html`
            <div class="favorite-item" @click="${() => {
              const rooms = Object.values(this._zoneMap);
              if (rooms.length > 0) {
                this._handleFavorite(rooms[0], fav.name);
              }
            }}">
              <ha-icon icon="mdi:music"></ha-icon>
              <span>${fav.name}</span>
            </div>
          `)}
        </div>
      </div>
    `;
  }

  static get styles() {
    return css`
      :host {
        display: block;
      }
      
      ha-card {
        height: 100%;
        box-sizing: border-box;
      }
      
      .card-content {
        padding: 16px;
      }
      
      .section {
        margin-bottom: 20px;
        padding-bottom: 20px;
        border-bottom: 1px solid var(--divider-color);
      }
      
      .section:last-child {
        border-bottom: none;
        margin-bottom: 0;
      }
      
      .section-header {
        display: flex;
        align-items: center;
        gap: 8px;
        margin-bottom: 12px;
        font-weight: 500;
        color: var(--primary-text-color);
      }
      
      .section-header ha-icon {
        color: var(--primary-color);
      }
      
      .badge {
        margin-left: auto;
        background: var(--primary-color);
        color: white;
        padding: 2px 8px;
        border-radius: 12px;
        font-size: 12px;
      }
      
      .button-row {
        display: flex;
        gap: 8px;
        flex-wrap: wrap;
      }
      
      .speakers-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
        gap: 16px;
      }
      
      .speaker-card {
        border: 1px solid var(--divider-color);
        border-radius: 8px;
        padding: 12px;
        background: var(--card-background-color);
        transition: all 0.2s ease;
      }
      
      .speaker-card.playing {
        border-color: var(--primary-color);
        box-shadow: 0 2px 8px rgba(var(--primary-color-rgb), 0.2);
      }
      
      .speaker-header {
        display: flex;
        align-items: center;
        gap: 8px;
        margin-bottom: 8px;
      }
      
      .speaker-header ha-icon {
        color: var(--primary-color);
      }
      
      .room-name {
        font-weight: 500;
      }
      
      .track-info {
        margin-bottom: 12px;
        min-height: 40px;
      }
      
      .track-title {
        font-weight: 500;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
      }
      
      .track-artist {
        font-size: 12px;
        color: var(--secondary-text-color);
      }
      
      .no-track {
        color: var(--secondary-text-color);
        font-style: italic;
      }
      
      .volume-control {
        display: flex;
        align-items: center;
        gap: 8px;
        margin-bottom: 12px;
      }
      
      .volume-slider {
        flex: 1;
        height: 4px;
      }
      
      .volume-value {
        min-width: 40px;
        text-align: right;
        font-size: 12px;
        color: var(--secondary-text-color);
      }
      
      .favorites-select {
        margin-top: 8px;
      }
      
      .favorites-select select {
        width: 100%;
        padding: 8px;
        border-radius: 4px;
        border: 1px solid var(--divider-color);
        background: var(--card-background-color);
        color: var(--primary-text-color);
      }
      
      .tts-input {
        display: flex;
        gap: 4px;
        margin-top: 8px;
      }
      
      .tts-input ha-textfield {
        flex: 1;
      }
      
      .favorites-list {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
      }
      
      .favorite-item {
        display: flex;
        align-items: center;
        gap: 6px;
        padding: 6px 12px;
        background: var(--secondary-background-color);
        border-radius: 16px;
        cursor: pointer;
        transition: background 0.2s;
      }
      
      .favorite-item:hover {
        background: var(--primary-color);
        color: white;
      }
      
      .error {
        text-align: center;
        color: var(--error-color);
      }
      
      .error ha-icon {
        font-size: 48px;
        margin-bottom: 12px;
      }
      
      .error-banner {
        display: flex;
        align-items: center;
        gap: 8px;
        padding: 12px;
        background: rgba(var(--error-color-rgb), 0.1);
        border-radius: 8px;
        margin-bottom: 16px;
        color: var(--error-color);
      }
      
      .no-data {
        color: var(--secondary-text-color);
        font-style: italic;
        text-align: center;
        padding: 20px;
      }
      
      mwc-icon-button {
        --mdc-icon-size: 24px;
      }
    `;
  }
}

customElements.define('styx-sonos-card', StyxSonosCard);
