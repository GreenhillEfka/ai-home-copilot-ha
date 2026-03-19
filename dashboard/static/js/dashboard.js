/**
 * PilotSuite Styx - Habitus Dashboard (10 Zonen Tabs)
 *
 * Ziele (PS-UX-012):
 * - Partial States: Loading / Empty / Error pro Zone-Grid
 * - Telemetrie: ui_state_* Events über UiState-Komponenten
 * - E2E: /dashboard/home Route kann als Einstieg genutzt werden
 */

class HabitusDashboard {
  constructor() {
    // 10 Zone Tabs (E2E-konform: data-zone + #grid-<zone> + #actions-<zone>)
    // Zone-IDs synchron mit pilotsuite-styx-core Habituszonen
    this.zones = [
      { id: 'living', name: 'Wohnbereich', icon: 'mdi-sofa' },
      { id: 'kitchen', name: 'Kochbereich', icon: 'mdi-stove' },
      { id: 'bath', name: 'Badbereich', icon: 'mdi-shower' },
      { id: 'office', name: 'Buerobereich', icon: 'mdi-desk' },
      { id: 'hallway', name: 'Gangbereich', icon: 'mdi-door-open' },
      { id: 'bedroom', name: 'Schlafbereich', icon: 'mdi-bed' },
      { id: 'room_mira', name: 'Zimmer Mira', icon: 'mdi-account-girl' },
      { id: 'room_paul', name: 'Zimmer Paul', icon: 'mdi-account-boy' },
      { id: 'terrace', name: 'Terrassenbereich', icon: 'mdi-patio-grass' },
      { id: 'outside', name: 'Aussenbereich', icon: 'mdi-tree' }
    ];

    this.socket = null;
    this.connected = false;
    this.activeZone = this.zones[0]?.id || 'living';
    this.zoneData = {};
    this.zoneMeta = {};
    this._globalStale = false;
    this.theme = 'light';

    // Shared UI State toolkit (wenn geladen)
    this.ui = window.UiState && window.UiState.UiStateToolkit
      ? new window.UiState.UiStateToolkit({ scope: 'dashboard/home' })
      : null;

    this.init();
  }

  init() {
    console.log('[Dashboard] init');
    this.setupTheme();
    this.renderTabs();
    this.renderTabContent();
    this.setupTabNavigation();
    this.setupScrollButtons();
    this.setupWebSocket();
    this.setupThemeToggle();
    this.updateScrollButtons();

    // Start in Loading-State
    this.zones.forEach(z => this.renderZoneLoading(z.id));

    // Simulierter First Paint: Loading-Overlay nach kurzer Zeit ausblenden,
    // danach mindestens Empty/Content für E2E/UX.
    setTimeout(() => {
      this.hideLoading();
      // Wenn bis dahin keine Daten kamen, fall back auf Demo-Daten.
      if (!Object.keys(this.zoneData).length) {
        this.loadZoneDataDemo();
      }
    }, 3000);
  }

  setupTheme() {
    const savedTheme = localStorage.getItem('dashboard-theme');
    const systemPrefersDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;

    if (savedTheme) {
      this.theme = savedTheme;
    } else if (systemPrefersDark) {
      this.theme = 'dark';
    }

    document.documentElement.setAttribute('data-theme', this.theme);
    this.updateThemeIcon();
  }

  setupThemeToggle() {
    const toggle = document.getElementById('theme-toggle');
    if (!toggle) return;

    toggle.addEventListener('click', () => {
      this.theme = this.theme === 'light' ? 'dark' : 'light';
      document.documentElement.setAttribute('data-theme', this.theme);
      localStorage.setItem('dashboard-theme', this.theme);
      this.updateThemeIcon();
    });
  }

  updateThemeIcon() {
    const toggle = document.getElementById('theme-toggle');
    if (!toggle) return;
    const icon = toggle.querySelector('i');
    if (!icon) return;

    icon.className = this.theme === 'dark'
      ? 'mdi mdi-brightness-7'
      : 'mdi mdi-brightness-auto';
  }

  renderTabs() {
    const container = document.getElementById('tabs-container');
    if (!container) return;

    container.innerHTML = this.zones.map((zone, index) => `
      <button class="tab-item ${index === 0 ? 'active' : ''}"
              data-zone="${zone.id}"
              onclick="dashboard.switchZone('${zone.id}')"
              title="${zone.name}">
        <i class="mdi ${zone.icon}"></i>
        <span class="label">${zone.name}</span>
        <span class="badge" id="badge-${zone.id}" style="display:none;">0</span>
      </button>
    `).join('');
  }

  renderTabContent() {
    const wrapper = document.getElementById('tab-content-wrapper');
    if (!wrapper) return;

    wrapper.innerHTML = this.zones.map((zone, index) => `
      <div class="tab-pane ${index === 0 ? 'active' : ''}" id="pane-${zone.id}">
        <div class="tab-pane-header">
          <h2><i class="mdi ${zone.icon}"></i> ${zone.name}</h2>
          <p>Live-Status und Widgets</p>
        </div>

        <div class="tab-content-grid" id="grid-${zone.id}">
          <div class="empty-state"><p>Initialisiere…</p></div>
        </div>

        <div class="quick-actions" id="actions-${zone.id}">
          <button class="quick-action-btn" onclick="dashboard.refreshZone('${zone.id}')">
            <i class="mdi mdi-refresh"></i> Aktualisieren
          </button>
          <button class="quick-action-btn" onclick="dashboard.showZoneSettings('${zone.id}')">
            <i class="mdi mdi-cog"></i> Einstellungen
          </button>
        </div>
      </div>
    `).join('');
  }

  setupTabNavigation() {
    document.addEventListener('keydown', (e) => {
      if (e.key !== 'ArrowLeft' && e.key !== 'ArrowRight') return;

      const currentIndex = this.zones.findIndex(z => z.id === this.activeZone);
      if (currentIndex < 0) return;

      let newIndex = currentIndex;
      if (e.key === 'ArrowLeft' && currentIndex > 0) newIndex = currentIndex - 1;
      if (e.key === 'ArrowRight' && currentIndex < this.zones.length - 1) newIndex = currentIndex + 1;

      if (newIndex !== currentIndex) {
        this.switchZone(this.zones[newIndex].id);
      }
    });
  }

  setupScrollButtons() {
    const scrollLeft = document.getElementById('scroll-left');
    const scrollRight = document.getElementById('scroll-right');
    const container = document.getElementById('tabs-container');
    if (!scrollLeft || !scrollRight || !container) return;

    scrollLeft.addEventListener('click', () => container.scrollBy({ left: -200, behavior: 'smooth' }));
    scrollRight.addEventListener('click', () => container.scrollBy({ left: 200, behavior: 'smooth' }));
    container.addEventListener('scroll', () => this.updateScrollButtons());
  }

  updateScrollButtons() {
    const scrollLeft = document.getElementById('scroll-left');
    const scrollRight = document.getElementById('scroll-right');
    const container = document.getElementById('tabs-container');
    if (!scrollLeft || !scrollRight || !container) return;

    scrollLeft.disabled = container.scrollLeft === 0;
    scrollRight.disabled = container.scrollLeft + container.clientWidth >= container.scrollWidth - 1;
  }

  switchZone(zoneId) {
    if (this.activeZone === zoneId) return;
    this.activeZone = zoneId;

    document.querySelectorAll('.tab-item').forEach(tab => {
      tab.classList.toggle('active', tab.dataset.zone === zoneId);
    });

    document.querySelectorAll('.tab-pane').forEach(pane => {
      pane.classList.toggle('active', pane.id === `pane-${zoneId}`);
    });

    const activeTabElement = document.querySelector(`.tab-item[data-zone="${zoneId}"]`);
    if (activeTabElement) {
      activeTabElement.scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'center' });
    }

    this.updateLastUpdateTime();
  }

  setupWebSocket() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}`;

    console.log('[Dashboard] Connecting to WebSocket:', wsUrl);

    this.socket = io(wsUrl, {
      transports: ['websocket', 'polling'],
      upgrade: true,
      reconnection: true,
      reconnectionDelay: 1000,
      reconnectionDelayMax: 5000,
      reconnectionAttempts: 10
    });

    this.socket.on('connect', () => {
      this.connected = true;
      this.updateConnectionStatus('connected');
      if (this.ui) this.ui.setGlobalDegraded(false, { reason: 'ws_connected' });

      // Start a sync pass (widget-level partial failure instead of full-page error).
      this._markAllZonesLoading('Synchronisiere…');

      // Request zone data
      this.socket.emit('request_zone_data', { zones: this.zones.map(z => z.id) });
    });

    this.socket.on('disconnect', (reason) => {
      this.connected = false;
      this.updateConnectionStatus('disconnected');
      if (this.ui) this.ui.setGlobalDegraded(true, { reason: reason || 'ws_disconnected' });

      // Partial failure feedback: keep last-known values but mark stale in every widget.
      this._markAllZonesStale(reason ? String(reason) : 'disconnect');

      // If the active zone has no cached data, show an explicit error state.
      if (!this.zoneData[this.activeZone]) {
        this.renderZoneError(this.activeZone, {
          message: 'Verbindung unterbrochen.',
          detail: reason ? String(reason) : 'disconnect'
        });
      }
    });

    this.socket.on('connect_error', (error) => {
      this.connected = false;
      this.updateConnectionStatus('disconnected');
      if (this.ui) this.ui.setGlobalDegraded(true, { reason: error?.message || 'connect_error' });

      this._markAllZonesStale(error?.message || 'connect_error');

      if (!this.zoneData[this.activeZone]) {
        this.renderZoneError(this.activeZone, {
          message: 'Konnte keine Live-Verbindung aufbauen.',
          detail: error?.message || 'connect_error'
        });
      }
    });

    this.socket.on('zone_update', (data) => {
      this.handleZoneUpdate(data);
    });

    this.socket.on('alert_update', (data) => {
      this.handleAlertUpdate(data);
    });

    this.socket.on('ha_discovery_complete', () => {
      this.hideLoading();
      this.loadZoneDataDemo();
      console.log('[Dashboard] HA Discovery complete');
    });
  }

  updateConnectionStatus(status) {
    const indicator = document.getElementById('connection-indicator');
    const statusText = document.getElementById('connection-status');

    if (indicator) indicator.className = `status-indicator ${status}`;
    if (statusText) statusText.textContent = status === 'connected' ? 'Verbunden' : 'Getrennt';
  }

  _getZoneMeta(zoneId) {
    if (!this.zoneMeta[zoneId]) {
      this.zoneMeta[zoneId] = {
        stale: false,
        lastUpdatedAt: null,
        lastError: null,
        missingKeys: [],
      };
    }
    return this.zoneMeta[zoneId];
  }

  _setZoneMeta(zoneId, patch = {}) {
    const meta = this._getZoneMeta(zoneId);
    this.zoneMeta[zoneId] = { ...meta, ...patch };
  }

  _markAllZonesStale(reason) {
    this._globalStale = true;
    this.zones.forEach(z => {
      this._setZoneMeta(z.id, { stale: true, lastError: reason || 'disconnected' });
      // If we have data, keep rendering cards but mark them stale.
      if (this.zoneData[z.id]) {
        this.renderZoneCards(z.id);
      } else {
        this.renderZoneEmpty(z.id, 'Offline — keine Daten verfügbar.');
      }
    });
  }

  _markAllZonesLoading(message = 'Synchronisiere…') {
    this._globalStale = false;
    this.zones.forEach(z => {
      this._setZoneMeta(z.id, { stale: false, lastError: null });
      this.renderZoneLoading(z.id, message);
    });
  }

  handleZoneUpdate(data) {
    if (!data || !data.zoneId) return;

    // Merge payload
    this.zoneData[data.zoneId] = {
      ...(this.zoneData[data.zoneId] || {}),
      ...(data.data || {})
    };

    this._globalStale = false;
    this._setZoneMeta(data.zoneId, {
      stale: false,
      lastUpdatedAt: new Date().toISOString(),
      lastError: null,
    });

    // Render only affected zone
    this.renderZoneCards(data.zoneId);
    this.updateLastUpdateTime();
  }

  handleAlertUpdate(data) {
    if (!data || !data.zoneId || typeof data.alertCount !== 'number') return;

    const badge = document.getElementById(`badge-${data.zoneId}`);
    if (!badge) return;

    if (data.alertCount > 0) {
      badge.textContent = data.alertCount > 9 ? '9+' : String(data.alertCount);
      badge.style.display = 'inline-block';
    } else {
      badge.style.display = 'none';
    }
  }

  renderZoneLoading(zoneId, message = 'Daten werden geladen…') {
    const grid = document.getElementById(`grid-${zoneId}`);
    if (!grid) return;

    if (this.ui) {
      this.ui.loading(grid, {
        source: `zone:${zoneId}`,
        message,
        detail: 'Bitte kurz warten…'
      });
      return;
    }

    grid.innerHTML = `<div class="empty-state"><p>${message}</p></div>`;
  }

  renderZoneEmpty(zoneId, message = 'Keine Daten verfügbar.') {
    const grid = document.getElementById(`grid-${zoneId}`);
    if (!grid) return;

    if (this.ui) {
      this.ui.empty(grid, {
        source: `zone:${zoneId}`,
        title: 'Keine Daten',
        message,
        actionLabel: 'Erneut versuchen',
        onAction: () => this.refreshZone(zoneId)
      });
      return;
    }

    grid.innerHTML = `<div class="empty-state"><p>${message}</p></div>`;
  }

  renderZoneError(zoneId, { message = 'Fehler', detail = '', errorClass = null } = {}) {
    const grid = document.getElementById(`grid-${zoneId}`);
    if (!grid) return;

    const resolvedErrorClass = errorClass
      || (window.UiState && window.UiState.ErrorClass ? window.UiState.ErrorClass.NETWORK : 'network');

    if (this.ui) {
      this.ui.error(grid, {
        source: `zone:${zoneId}`,
        message,
        detail,
        degraded: true,
        errorClass: resolvedErrorClass,
        onRetry: () => this.refreshZone(zoneId)
      });
      return;
    }

    grid.innerHTML = `<div class="empty-state"><p>${message}</p><p>${detail}</p></div>`;
  }

  renderZoneCards(zoneId) {
    const grid = document.getElementById(`grid-${zoneId}`);
    const data = this.zoneData[zoneId];
    if (!grid) return;

    if (!data) {
      if (this._globalStale || !this.connected) {
        this.renderZoneEmpty(zoneId, 'Offline — keine Daten verfügbar.');
      } else {
        this.renderZoneEmpty(zoneId);
      }
      return;
    }

    const meta = this._getZoneMeta(zoneId);
    const requiredKeys = ['temperature', 'targetTemp', 'humidity', 'lights', 'brightness'];
    const missingKeys = requiredKeys.filter(k => data[k] === undefined || data[k] === null);

    const isStale = Boolean(meta.stale || this._globalStale || !this.connected);
    const isPartial = missingKeys.length > 0;

    const statusText = isStale ? 'Offline' : (isPartial ? 'Teildaten' : 'Aktiv');
    const statusDotClass = isStale ? 'warning' : (isPartial ? 'warning' : '');

    const zoneBannerHtml = isStale
      ? `<div class="zone-card-banner warn">Offline · letzte bekannte Daten</div>`
      : (isPartial ? `<div class="zone-card-banner warn">Teildaten · ${missingKeys.length} Feld(er) fehlen</div>` : '');

    // Mindestens 1 Element mit .widget/.card/.zone-item für E2E
    grid.innerHTML = `${zoneBannerHtml}

      <div class="zone-card widget widget-container card" data-widget-id="temp-${zoneId}" data-x="0" data-y="0">
        <div class="zone-card-header">
          <div class="zone-card-icon"><i class="mdi mdi-thermometer"></i></div>
          <div class="zone-card-status"><span class="status-dot ${statusDotClass}"></span><span>${statusText}</span></div>
        </div>
        <div class="zone-card-title">Temperatur</div>
        <div class="zone-card-metrics">
          <div class="zone-metric">
            <span class="zone-metric-label">Aktuell</span>
            <span class="zone-metric-value">${data.temperature ?? '--'}°C</span>
          </div>
          <div class="zone-metric">
            <span class="zone-metric-label">Ziel</span>
            <span class="zone-metric-value">${data.targetTemp ?? '--'}°C</span>
          </div>
        </div>
      </div>

      <div class="zone-card widget widget-container card" data-widget-id="humidity-${zoneId}" data-x="0" data-y="0">
        <div class="zone-card-header">
          <div class="zone-card-icon"><i class="mdi mdi-water-percent"></i></div>
          <div class="zone-card-status"><span class="status-dot ${statusDotClass}"></span><span>${statusText}</span></div>
        </div>
        <div class="zone-card-title">Luftfeuchtigkeit</div>
        <div class="zone-card-metrics">
          <div class="zone-metric">
            <span class="zone-metric-label">Aktuell</span>
            <span class="zone-metric-value">${data.humidity ?? '--'}%</span>
          </div>
          <div class="zone-metric">
            <span class="zone-metric-label">Bereich</span>
            <span class="zone-metric-value">40–60%</span>
          </div>
        </div>
      </div>

      <div class="zone-card widget widget-container card" data-widget-id="lights-${zoneId}" data-x="0" data-y="0">
        <div class="zone-card-header">
          <div class="zone-card-icon"><i class="mdi mdi-lightbulb"></i></div>
          <div class="zone-card-status"><span class="status-dot ${statusDotClass}"></span><span>${statusText}</span></div>
        </div>
        <div class="zone-card-title">Beleuchtung</div>
        <div class="zone-card-metrics">
          <div class="zone-metric">
            <span class="zone-metric-label">Anzahl</span>
            <span class="zone-metric-value">${data.lights ?? '--'}</span>
          </div>
          <div class="zone-metric">
            <span class="zone-metric-label">Helligkeit</span>
            <span class="zone-metric-value">${data.brightness ?? '--'}%</span>
          </div>
        </div>
      </div>
    `;

    // Drag & Drop optional
    if (window.dragDropManager && typeof window.dragDropManager.enableDrag === 'function') {
      window.dragDropManager.enableDrag(`#grid-${zoneId} .widget-container`);
    }
  }

  loadZoneDataDemo() {
    // Simulierter Payload (E2E + UX)
    this._globalStale = false;
    this.zones.forEach(zone => {
      this.zoneData[zone.id] = {
        temperature: Number((20 + Math.random() * 3).toFixed(1)),
        targetTemp: Number((21 + Math.random() * 2).toFixed(1)),
        humidity: Math.floor(40 + Math.random() * 20),
        lights: Math.floor(Math.random() * 5),
        brightness: Math.floor(40 + Math.random() * 40)
      };
      this._setZoneMeta(zone.id, {
        stale: false,
        lastUpdatedAt: new Date().toISOString(),
        lastError: null,
      });
      this.renderZoneCards(zone.id);
    });

    this.updateLastUpdateTime();
  }

  refreshZone(zoneId) {
    if (this.socket && this.connected) {
      this.renderZoneLoading(zoneId, 'Aktualisiere…');
      this.socket.emit('request_zone_data', { zones: [zoneId] });
      return;
    }

    // Offline fallback
    this._setZoneMeta(zoneId, { stale: true, lastError: 'offline' });
    this.renderZoneLoading(zoneId, 'Aktualisiere…');
    setTimeout(() => {
      if (!this.zoneData[zoneId]) {
        this.renderZoneEmpty(zoneId, 'Offline — keine Daten verfügbar.');
      } else {
        this.renderZoneCards(zoneId);
      }
    }, 400);
  }

  showZoneSettings(zoneId) {
    alert(`Einstellungen für ${zoneId} werden geöffnet…`);
  }

  hideLoading() {
    const overlay = document.getElementById('loading-overlay');
    if (overlay) overlay.classList.add('hidden');
  }

  updateLastUpdateTime() {
    const now = new Date();
    const timeString = now.toLocaleTimeString('de-DE');
    const element = document.getElementById('last-update-time');
    if (element) element.textContent = timeString;
  }
}

// Dashboard initialisieren
let dashboard;
document.addEventListener('DOMContentLoaded', () => {
  dashboard = new HabitusDashboard();
  window.dashboard = dashboard;
});
