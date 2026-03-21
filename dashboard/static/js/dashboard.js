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
    this.loadVersions();
    this.loadZones();
    this.setupTheme();
    this.setupTabNavigation();
    this.setupScrollButtons();
    this.setupWebSocket();
    this.setupThemeToggle();
    // renderTabs/renderTabContent called by loadZones once zones are available
  }

  loadZones() {
    // Load zones from Core API (falls back to hardcoded list on error)
    fetch('/api/v1/dashboard/zones')
      .then(r => r.ok ? r.json() : null)
      .then(data => {
        if (data && data.zones && data.zones.length) {
          this.zones = data.zones.map(z => ({
            id: z.id,
            name: z.name,
            icon: z.icon || 'mdi:home-floor-1',
          }));
        }
        // Always render — even if API failed we use hardcoded this.zones
        this.renderTabs();
        this.renderTabContent();
        this.updateScrollButtons();
        this.zones.forEach(z => this.renderZoneLoading(z.id));

        // Fallback demo data after timeout
        setTimeout(() => {
          this.hideLoading();
          if (!Object.keys(this.zoneData).length) {
            this.loadZoneDataDemo();
          }
        }, 3000);
      })
      .catch(() => {
        // Core unreachable — render with hardcoded zones
        this.renderTabs();
        this.renderTabContent();
        this.updateScrollButtons();
        this.zones.forEach(z => this.renderZoneLoading(z.id));
        setTimeout(() => {
          this.hideLoading();
          if (!Object.keys(this.zoneData).length) {
            this.loadZoneDataDemo();
          }
        }, 3000);
      });
  }

  loadVersions() {
    fetch('/api/v1/dashboard/version')
      .then(r => r.ok ? r.json() : null)
      .then(data => {
        if (!data) return;
        const haEl = document.getElementById('ha-version');
        const coreEl = document.getElementById('core-version');
        const syncEl = document.getElementById('version-sync-status');
        if (haEl) haEl.textContent = 'HA ' + (data.ha || '?');
        if (coreEl) coreEl.textContent = 'Core ' + (data.core || '?');
        if (syncEl) {
          syncEl.textContent = data.sync_status === 'ok' ? '●' : '⚠';
          syncEl.className = data.sync_status === 'ok' ? 'version-pill sync-ok' : 'version-pill sync-warn';
        }
      })
      .catch(() => {});
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
          <button class="quick-action-btn primary" onclick="dashboard.showCreateZoneModal('${zone.id}')">
            <i class="mdi mdi-plus"></i> Zone erstellen
          </button>
          <button class="quick-action-btn danger" onclick="dashboard.showDeleteZoneModal('${zone.id}')">
            <i class="mdi mdi-delete"></i> Zone löschen
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
    const requiredKeys = ['temperature', 'humidity', 'lights_on', 'lights_total', 'presence', 'media_playing'];
    const missingKeys = requiredKeys.filter(k => data[k] === undefined || data[k] === null);
    // Optional: presence + media_playing from Core modules
    const hasPresence = data.presence !== undefined && data.presence !== null;
    const hasMedia = data.media_playing !== undefined && data.media_playing !== null;

    const isStale = Boolean(meta.stale || this._globalStale || !this.connected);
    const isPartial = missingKeys.length > 0;

    const statusText = isStale ? 'Offline' : (isPartial ? 'Teildaten' : 'Aktiv');
    const statusDotClass = isStale ? 'warning' : (isPartial ? 'warning' : '');

    const zoneBannerHtml = isStale
      ? `<div class="zone-card-banner warn">Offline · letzte bekannte Daten</div>
         <button class="quick-action-btn" style="margin:4px 0;" onclick="dashboard.showEditZoneModal('${zoneId}')"><i class="mdi mdi-pencil"></i> Zone bearbeiten</button>`
      : (isPartial ? `<div class="zone-card-banner warn">Teildaten · ${missingKeys.length} Feld(er) fehlen</div>
         <button class="quick-action-btn" style="margin:4px 0;" onclick="dashboard.showEditZoneModal('${zoneId}')"><i class="mdi mdi-pencil"></i> Zone bearbeiten</button>`
      : `<div style="padding:4px 0;">
         <button class="quick-action-btn primary" style="margin:4px 4px 4px 0;" onclick="dashboard.showEditZoneModal('${zoneId}')"><i class="mdi mdi-pencil"></i> Bearbeiten</button>
         <button class="quick-action-btn danger" style="margin:4px 0;" onclick="dashboard.showDeleteZoneModal('${zoneId}')"><i class="mdi mdi-delete"></i> Löschen</button>
         </div>`);

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
            <span class="zone-metric-label">An</span>
            <span class="zone-metric-value">${data.lights_on ?? '--'}</span>
          </div>
          <div class="zone-metric">
            <span class="zone-metric-label">Gesamt</span>
            <span class="zone-metric-value">${data.lights_total ?? '--'}</span>
          </div>
        </div>
      </div>

      <div class="zone-card widget widget-container card" data-widget-id="presence-${zoneId}" data-x="0" data-y="0">
        <div class="zone-card-header">
          <div class="zone-card-icon"><i class="mdi mdi-account-multiple"></i></div>
          <div class="zone-card-status"><span class="status-dot ${data.presence ? 'ok' : ''}"></span><span>${data.presence ? 'Anwesend' : 'Abwesend'}</span></div>
        </div>
        <div class="zone-card-title">Anwesenheit</div>
        <div class="zone-card-metrics">
          <div class="zone-metric">
            <span class="zone-metric-label">Personen</span>
            <span class="zone-metric-value">${data.person_count ?? 0}</span>
          </div>
        </div>
      </div>

      <div class="zone-card widget widget-container card" data-widget-id="media-${zoneId}" data-x="0" data-y="0">
        <div class="zone-card-header">
          <div class="zone-card-icon"><i class="mdi ${data.media_playing ? 'mdi-music-note' : 'mdi-music-note-outline'}"></i></div>
          <div class="zone-card-status"><span class="status-dot ${data.media_playing ? 'ok' : ''}"></span><span>${data.media_playing ? 'Spielt' : 'Still'}</span></div>
        </div>
        <div class="zone-card-title">Musik</div>
        <div class="zone-card-metrics">
          <div class="zone-metric">
            <span class="zone-metric-label">Status</span>
            <span class="zone-metric-value">${data.media_playing ? 'Aktiv' : 'Aus'}</span>
          </div>
        </div>
      </div>

      ${hasPresence ? `
      <div class="zone-card widget widget-container card" data-widget-id="presence-${zoneId}" data-x="0" data-y="0">
        <div class="zone-card-header">
          <div class="zone-card-icon"><i class="mdi mdi-account-multiple"></i></div>
          <div class="zone-card-status"><span class="status-dot ${statusDotClass}"></span><span>${statusText}</span></div>
        </div>
        <div class="zone-card-title">Anwesenheit</div>
        <div class="zone-card-metrics">
          <div class="zone-metric">
            <span class="zone-metric-label">Erkannt</span>
            <span class="zone-metric-value">${data.presence ? 'Ja' : 'Nein'}</span>
          </div>
          ${data.person_count !== undefined ? `
          <div class="zone-metric">
            <span class="zone-metric-label">Personen</span>
            <span class="zone-metric-value">${data.person_count}</span>
          </div>` : ''}
        </div>
      </div>` : ''}

      ${hasMedia ? `
      <div class="zone-card widget widget-container card" data-widget-id="media-${zoneId}" data-x="0" data-y="0">
        <div class="zone-card-header">
          <div class="zone-card-icon"><i class="mdi ${data.media_playing ? 'mdi-play-circle' : 'mdi-pause-circle'}"></i></div>
          <div class="zone-card-status"><span class="status-dot ${statusDotClass}"></span><span>${statusText}</span></div>
        </div>
        <div class="zone-card-title">Medien</div>
        <div class="zone-card-metrics">
          <div class="zone-metric">
            <span class="zone-metric-label">Status</span>
            <span class="zone-metric-value">${data.media_playing ? 'Abspielen' : 'Pausiert'}</span>
          </div>
        </div>
      </div>` : ''}
    `;

    // Drag & Drop optional
    if (window.dragDropManager && typeof window.dragDropManager.enableDrag === 'function') {
      window.dragDropManager.enableDrag(`#grid-${zoneId} .widget-container`);
    }
  }

  loadZoneDataDemo() {
    // Simulierter Payload (E2E + UX) — spiegelt Core module data Struktur
    this._globalStale = false;
    this.zones.forEach(zone => {
      this.zoneData[zone.id] = {
        temperature: Number((20 + Math.random() * 3).toFixed(1)),
        humidity: Math.floor(40 + Math.random() * 20),
        lights_on: Math.floor(Math.random() * 4),
        lights_total: Math.floor(4 + Math.random() * 4),
        presence: Math.random() > 0.5,
        person_count: Math.floor(Math.random() * 3),
        media_playing: Math.random() > 0.6,
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

  createZone(zoneId) {
    const name = prompt(`Name für neue Zone (${zoneId}):`);
    if (!name || !name.trim()) return;

    const actionBtns = document.querySelectorAll(`#actions-${zoneId} .quick-action-btn`);
    actionBtns.forEach(b => b.setAttribute('disabled', 'true'));

    const payload = {
      zone_id: zoneId,
      name: name.trim(),
      icon: 'mdi:room',
      enabled: true,
      priority: 10,
      rooms: [],
      entities: {},
    };

    this._setZoneMeta(zoneId, { stale: false, lastError: null });
    this.renderZoneLoading(zoneId, 'Zone wird erstellt…');

    fetch('/api/v1/dashboard/zone-editor/zones', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    })
      .then((resp) => {
        if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
        return resp.json();
      })
      .then(() => {
        // Invalidate cache so next refresh gets fresh data
        if (this.socket && this.connected) {
          this.socket.emit('request_zone_data', { zones: [zoneId] });
        }
        // Refresh zone list so new zone appears in tabs
        this.loadZones();
      })
      .catch((err) => {
        console.error('[Dashboard] createZone error:', err);
        this._setZoneMeta(zoneId, { stale: true, lastError: String(err) });
        this.renderZoneError(zoneId, {
          message: 'Zone konnte nicht erstellt werden.',
          detail: String(err),
        });
      })
      .finally(() => {
        actionBtns.forEach(b => b.removeAttribute('disabled'));
      });
  }

  showEditZoneModal(zoneId) {
    const existing = document.getElementById('edit-zone-modal');
    if (existing) existing.remove();

    const zone = this.zones.find(z => z.id === zoneId) || { id: zoneId, name: zoneId };
    const data = this.zoneData[zoneId] || {};

    const html = `
      <div id="edit-zone-modal" style="
        position:fixed;top:0;left:0;right:0;bottom:0;z-index:9999;
        background:rgba(0,0,0,0.5);display:flex;align-items:center;justify-content:center;
        font-family:system-ui,sans-serif;
      ">
        <div style="
          background:#fff;padding:24px;border-radius:12px;width:340px;max-width:90vw;
          box-shadow:0 8px 32px rgba(0,0,0,0.2);
        ">
          <h3 style="margin:0 0 16px;font-size:18px;">Zone bearbeiten — ${zoneId}</h3>
          <input id="ez-zone-id" type="hidden" value="${zoneId}">
          <div style="margin-bottom:12px;">
            <label style="display:block;font-size:12px;color:#666;margin-bottom:4px;">Name</label>
            <input id="ez-name" value="${zone.name}" style="width:100%;padding:8px;border:1px solid #ddd;border-radius:6px;">
          </div>
          <div style="margin-bottom:12px;">
            <label style="display:block;font-size:12px;color:#666;margin-bottom:4px;">Icon (MDI)</label>
            <input id="ez-icon" value="${zone.icon || 'mdi:home-floor-1'}" style="width:100%;padding:8px;border:1px solid #ddd;border-radius:6px;">
          </div>
          <div style="margin-bottom:16px;">
            <label style="display:flex;align-items:center;gap:8px;cursor:pointer;">
              <input id="ez-enabled" type="checkbox" ${data.enabled !== false ? 'checked' : ''}>
              Zone aktiv
            </label>
          </div>
          <div style="display:flex;gap:8px;justify-content:flex-end;">
            <button id="ez-cancel" style="padding:8px 16px;border:1px solid #ddd;background:#f5f5f5;border-radius:6px;cursor:pointer;">Abbrechen</button>
            <button id="ez-save" style="padding:8px 16px;border:none;background:#1976d2;color:#fff;border-radius:6px;cursor:pointer;">Speichern</button>
          </div>
          <p id="ez-error" style="color:#d32f2f;font-size:12px;margin:8px 0 0;display:none;"></p>
        </div>
      </div>`;

    document.body.insertAdjacentHTML('beforeend', html);
    const modal = document.getElementById('edit-zone-modal');

    const cleanup = () => modal.remove();

    document.getElementById('ez-cancel').onclick = cleanup;
    modal.onclick = (e) => { if (e.target === modal) cleanup(); };


    document.getElementById('ez-save').onclick = () => {
      const idVal    = document.getElementById('ez-zone-id').value;
      const nameVal  = document.getElementById('ez-name').value.trim();
      const iconVal = document.getElementById('ez-icon').value.trim() || 'mdi:home-floor-1';
      const enabledVal = document.getElementById('ez-enabled').checked;

      const err = document.getElementById('ez-error');

      // Basic guard (also covered by schema validation, but gives immediate feedback)
      if (!nameVal) { err.textContent = 'Name erforderlich.'; err.style.display = 'block'; return; }

      const payload = { name: nameVal, icon: iconVal, enabled: enabledVal };

      document.getElementById('ez-save').disabled = true;
      document.getElementById('ez-save').textContent = '…';

      fetch(`/api/v1/dashboard/zone-editor/zones/${encodeURIComponent(idVal)}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      })
        .then(resp => { if (!resp.ok) throw new Error('HTTP ' + resp.status); return resp.json(); })
        .then(() => {
          // Update local zone data on success
          const z = this.zones.find(z => z.id === idVal);
          if (z) { z.name = nameVal; z.icon = iconVal; }
          if (this.socket && this.connected) this.socket.emit('request_zone_data', { zones: [idVal] });
          cleanup();
        })
        .catch(err => {
          err.textContent = 'Fehler: ' + err.message;
          err.style.display = 'block';
          document.getElementById('ez-save').disabled = false;
          document.getElementById('ez-save').textContent = 'Speichern';
        });
    };
  }

  showDeleteZoneModal(zoneId) {
    const existing = document.getElementById('delete-zone-modal');
    if (existing) existing.remove();

    const btns = document.querySelectorAll('#actions-' + zoneId + ' .quick-action-btn');
    btns.forEach(b => b.setAttribute('disabled', 'true'));

    const html = `
      <div id="delete-zone-modal" style="
        position:fixed;top:0;left:0;right:0;bottom:0;z-index:9999;
        background:rgba(0,0,0,0.5);display:flex;align-items:center;justify-content:center;
        font-family:system-ui,sans-serif;
      ">
        <div style="
          background:#fff;padding:24px;border-radius:12px;width:340px;max-width:90vw;
          box-shadow:0 8px 32px rgba(0,0,0,0.2);
        ">
          <h3 style="margin:0 0 8px;font-size:18px;">Zone löschen</h3>
          <p style="margin:0 0 16px;color:#444;font-size:14px;">
            Zone <strong id="dz-zone-name"></strong> wirklich löschen? Diese Aktion kann nicht rückgängig gemacht werden.
          </p>
          <input id="dz-zone-id" type="hidden" value="${zoneId}">
          <div style="display:flex;gap:8px;justify-content:flex-end;">
            <button id="dz-cancel" style="padding:8px 16px;border:1px solid #ddd;background:#f5f5f5;border-radius:6px;cursor:pointer;">Abbrechen</button>
            <button id="dz-confirm" style="padding:8px 16px;border:none;background:#d32f2f;color:#fff;border-radius:6px;cursor:pointer;">Löschen</button>
          </div>
          <p id="dz-error" style="color:#d32f2f;font-size:12px;margin:8px 0 0;display:none;"></p>
        </div>
      </div>`;

    document.body.insertAdjacentHTML('beforeend', html);
    const modal = document.getElementById('delete-zone-modal');
    document.getElementById('dz-zone-name').textContent = zoneId;

    const cleanup = () => { modal.remove(); btns.forEach(b => b.removeAttribute('disabled')); };

    document.getElementById('dz-cancel').onclick = cleanup;
    modal.onclick = (e) => { if (e.target === modal) cleanup(); };

    document.getElementById('dz-confirm').onclick = () => {
      this._setZoneMeta(zoneId, { stale: false, lastError: null });
      this.renderZoneLoading(zoneId, 'Zone wird gelöscht…');
      document.getElementById('dz-confirm').disabled = true;
      document.getElementById('dz-confirm').textContent = '…';

      fetch(`/api/v1/dashboard/zone-editor/zones/${encodeURIComponent(zoneId)}`, {
        method: 'DELETE',
      })
        .then(resp => { if (!resp.ok) throw new Error('HTTP ' + resp.status); return resp.json(); })
        .then(() => {
          if (this.socket && this.connected) this.socket.emit('request_zone_data', { zones: [zoneId] });
          delete this.zoneData[zoneId];
          this.renderZoneEmpty(zoneId, 'Zone wurde gelöscht.');
          cleanup();
        })
        .catch(err => {
          console.error('[Dashboard] deleteZone error:', err);
          this._setZoneMeta(zoneId, { stale: true, lastError: String(err) });
          this.renderZoneError(zoneId, { message: 'Zone konnte nicht gelöscht werden.', detail: String(err) });
          document.getElementById('dz-error').textContent = 'Fehler: ' + err.message;
          document.getElementById('dz-error').style.display = 'block';
          document.getElementById('dz-confirm').disabled = false;
          document.getElementById('dz-confirm').textContent = 'Löschen';
        });
    };
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

  // ── Zone Create Modal ─────────────────────────────────────────────────────

  showCreateZoneModal(zoneId) {
    const existing = document.getElementById('create-zone-modal');
    if (existing) existing.remove();

    const btns = document.querySelectorAll('#actions-' + zoneId + ' .quick-action-btn');
    btns.forEach(b => b.setAttribute('disabled', 'true'));

    const html = `
      <div id="create-zone-modal" style="
        position:fixed;top:0;left:0;right:0;bottom:0;z-index:9999;
        background:rgba(0,0,0,0.5);display:flex;align-items:center;justify-content:center;
        font-family:system-ui, sans-serif;
      ">
        <div style="
          background:#fff;padding:24px;border-radius:12px;width:360px;max-width:90vw;
          box-shadow:0 8px 32px rgba(0,0,0,0.2);
        ">
          <h3 style="margin:0 0 16px;font-size:18px;">Neue Zone erstellen</h3>
          <input id="cz-zone-id" type="hidden" value="${zoneId}">
          <div style="margin-bottom:12px;">
            <label style="display:block;font-size:12px;color:#666;margin-bottom:4px;">Zone-ID</label>
            <input id="cz-id" value="${zoneId}" style="width:100%;padding:8px;border:1px solid #ddd;border-radius:6px;" disabled>
          </div>
          <div style="margin-bottom:12px;">
            <label style="display:block;font-size:12px;color:#666;margin-bottom:4px;">Name</label>
            <input id="cz-name" placeholder="z.B. Wohnbereich" style="width:100%;padding:8px;border:1px solid #ddd;border-radius:6px;">
          </div>
          <div style="margin-bottom:12px;">
            <label style="display:block;font-size:12px;color:#666;margin-bottom:4px;">Icon (MDI)</label>
            <input id="cz-icon" value="mdi:home-floor-1" style="width:100%;padding:8px;border:1px solid #ddd;border-radius:6px;">
          </div>
          <div style="display:flex;gap:8px;justify-content:flex-end;">
            <button id="cz-cancel" style="padding:8px 16px;border:1px solid #ddd;background:#f5f5f5;border-radius:6px;cursor:pointer;">Abbrechen</button>
            <button id="cz-submit" style="padding:8px 16px;border:none;background:#1976d2;color:#fff;border-radius:6px;cursor:pointer;">Erstellen</button>
          </div>
          <p id="cz-error" style="color:#d32f2f;font-size:12px;margin:8px 0 0;display:none;"></p>
        </div>
      </div>`;

    document.body.insertAdjacentHTML('beforeend', html);
    const modal = document.getElementById('create-zone-modal');

    document.getElementById('cz-cancel').onclick = () => {
      modal.remove();
      btns.forEach(b => b.removeAttribute('disabled'));
    };
    modal.onclick = (e) => { if (e.target === modal) { modal.remove(); btns.forEach(b => b.removeAttribute('disabled')); }};

    document.getElementById('cz-submit').onclick = () => {
      const idVal    = document.getElementById('cz-id').value;
      const nameVal  = document.getElementById('cz-name').value.trim();
      const iconVal = document.getElementById('cz-icon').value.trim() || 'mdi:home-floor-1';

      const err = document.getElementById('cz-error');
      if (!nameVal) { err.textContent = 'Name erforderlich.'; err.style.display = 'block'; return; }

      const payload = { zone_id: idVal, name: nameVal, icon: iconVal };


      document.getElementById('cz-submit').disabled = true;
      document.getElementById('cz-submit').textContent = '…';

      fetch('/api/v1/dashboard/zone-editor/zones', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      })
        .then(resp => { if (!resp.ok) throw new Error('HTTP ' + resp.status); return resp.json(); })
        .then(() => {
          modal.remove();
          // Refresh zone list from Core so new zone appears in tabs
          this.loadZones();
        })
        .catch(err => { err.textContent = 'Fehler: ' + err.message; err.style.display = 'block'; document.getElementById('cz-submit').disabled = false; document.getElementById('cz-submit').textContent = 'Erstellen'; })
        .finally(() => { btns.forEach(b => b.removeAttribute('disabled')); });
    };
  }
}

// Dashboard initialisieren — IIFE, window.dashboard VOR Constructor
(function () {
  window.dashboard = new HabitusDashboard();
})();
