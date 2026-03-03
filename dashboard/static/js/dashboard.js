/**
 * PilotSuite Styx - Dashboard Tab Logic & WebSocket Connection
 * Material Design Dashboard mit 3-Tab Layout:
 * - Tab 1: Habitus (Mood/Zonen)
 * - Tab 2: Hausverwaltung (Energie, Präsenz, Automationen)
 * - Tab 3: Styx (Neural Dashboard, Brain Graph)
 */

class HabitusDashboard {
    constructor() {
        // 3-Tab Layout Konfiguration (wiederhergestellt aus recovery)
        this.tabs = [
            { 
                id: 'habitus', 
                name: 'Habitus', 
                icon: 'mdi-heart-pulse', 
                alertCount: 0,
                description: 'Mood & Zonen Status'
            },
            { 
                id: 'hausverwaltung', 
                name: 'Hausverwaltung', 
                icon: 'mdi-home-city', 
                alertCount: 0,
                description: 'Energie, Präsenz & Automationen'
            },
            { 
                id: 'styx', 
                name: 'Styx', 
                icon: 'mdi-brain', 
                alertCount: 0,
                description: 'Neural Dashboard & Brain Graph'
            }
        ];
        
        // Legacy zone support (for backward compatibility)
        this.zones = [
            { id: 'wohn', name: 'Wohnbereich', icon: 'mdi-sofa', alertCount: 0 },
            { id: 'bad', name: 'Badbereich', icon: 'mdi-shower', alertCount: 0 },
            { id: 'koch', name: 'Kochbereich', icon: 'mdi-stove', alertCount: 0 },
            { id: 'buero', name: 'Bürobereich', icon: 'mdi-desk', alertCount: 0 },
            { id: 'gang', name: 'Gangbereich', icon: 'mdi-door-open', alertCount: 0 },
            { id: 'schlaf', name: 'Schlafbereich', icon: 'mdi-bed', alertCount: 0 },
            { id: 'mira', name: 'Zimmer Mira', icon: 'mdi-account-girl', alertCount: 0 },
            { id: 'paul', name: 'Zimmer Paul', icon: 'mdi-account-boy', alertCount: 0 },
            { id: 'terrasse', name: 'Terrassenbereich', icon: 'mdi-patio-grass', alertCount: 0 },
            { id: 'aussen', name: 'Aussenbereich', icon: 'mdi-tree', alertCount: 0 }
        ];
        
        this.socket = null;
        this.connected = false;
        this.activeTab = 'habitus';
        this.zoneData = {};
        this.theme = 'light';
        
        this.init();
    }
    
    init() {
        console.log('[Dashboard] Initializing Habitus Dashboard...');
        this.setupTheme();
        this.renderTabs();
        this.renderTabContent();
        this.setupTabNavigation();
        this.setupScrollButtons();
        this.setupWebSocket();
        this.setupThemeToggle();
        this.updateScrollButtons();
        
        // Auto-hide loading after 3 seconds (simulated HA discovery)
        setTimeout(() => {
            this.hideLoading();
        }, 3000);
    }
    
    setupTheme() {
        // Check for HA theme preference or system preference
        const savedTheme = localStorage.getItem('dashboard-theme');
        const systemPrefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
        
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
        if (toggle) {
            toggle.addEventListener('click', () => {
                this.theme = this.theme === 'light' ? 'dark' : 'light';
                document.documentElement.setAttribute('data-theme', this.theme);
                localStorage.setItem('dashboard-theme', this.theme);
                this.updateThemeIcon();
            });
        }
    }
    
    updateThemeIcon() {
        const toggle = document.getElementById('theme-toggle');
        if (toggle) {
            const icon = toggle.querySelector('i');
            if (this.theme === 'dark') {
                icon.className = 'mdi mdi-brightness-7';
            } else {
                icon.className = 'mdi mdi-brightness-auto';
            }
        }
    }
    
    renderTabs() {
        const container = document.getElementById('tabs-container');
        if (!container) return;
        
        // 3-Tab Layout rendering
        container.innerHTML = this.tabs.map((tab, index) => `
            <button class="tab-item ${index === 0 ? 'active' : ''}" 
                    data-tab="${tab.id}"
                    onclick="dashboard.switchTab('${tab.id}')"
                    title="${tab.description}">
                <i class="mdi ${tab.icon}"></i>
                <span class="label">${tab.name}</span>
                <span class="badge" id="badge-${tab.id}" style="display: none;">0</span>
            </button>
        `).join('');
    }
    
    renderTabContent() {
        const wrapper = document.getElementById('tab-content-wrapper');
        if (!wrapper) return;
        
        // 3-Tab Layout Content
        wrapper.innerHTML = this.tabs.map((tab, index) => `
            <div class="tab-pane ${index === 0 ? 'active' : ''}" id="pane-${tab.id}">
                <div class="tab-pane-header">
                    <h2><i class="mdi ${tab.icon}"></i> ${tab.name}</h2>
                    <p>${tab.description}</p>
                </div>
                <div class="tab-content-grid" id="grid-${tab.id}">
                    ${this.getTabContent(tab.id)}
                </div>
                <div class="quick-actions" id="actions-${tab.id}">
                    <button class="quick-action-btn" onclick="dashboard.refreshTab('${tab.id}')">
                        <i class="mdi mdi-refresh"></i> Aktualisieren
                    </button>
                    <button class="quick-action-btn" onclick="dashboard.showTabSettings('${tab.id}')">
                        <i class="mdi mdi-cog"></i> Einstellungen
                    </button>
                </div>
            </div>
        `).join('');
    }
    
    getTabContent(tabId) {
        // Return content based on tab
        switch(tabId) {
            case 'habitus':
                return `
                    <div class="content-card mood-gauges">
                        <h3><i class="mdi mdi-emoticon"></i> Mood Status</h3>
                        <div class="gauge-grid">
                            <div class="gauge">
                                <span class="gauge-label">Comfort</span>
                                <div class="gauge-bar"><div class="gauge-fill" style="width: 75%"></div></div>
                                <span class="gauge-value">75%</span>
                            </div>
                            <div class="gauge">
                                <span class="gauge-label">Joy</span>
                                <div class="gauge-bar"><div class="gauge-fill" style="width: 60%"></div></div>
                                <span class="gauge-value">60%</span>
                            </div>
                            <div class="gauge">
                                <span class="gauge-label">Frugality</span>
                                <div class="gauge-bar"><div class="gauge-fill" style="width: 85%"></div></div>
                                <span class="gauge-value">85%</span>
                            </div>
                        </div>
                    </div>
                    <div class="content-card zone-overview">
                        <h3><i class="mdi mdi-home-group"></i> Zonen Übersicht</h3>
                        <div class="zone-list">
                            ${this.zones.map(z => `
                                <div class="zone-item" data-zone="${z.id}">
                                    <i class="mdi ${z.icon}"></i>
                                    <span>${z.name}</span>
                                    <span class="zone-status active"> Aktiv</span>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                `;
            case 'hausverwaltung':
                return `
                    <div class="content-card energy-overview">
                        <h3><i class="mdi mdi-lightning-bolt"></i> Energie</h3>
                        <div class="energy-stats">
                            <div class="stat">
                                <span class="stat-value">2.4</span>
                                <span class="stat-unit">kW</span>
                                <span class="stat-label">Aktuell</span>
                            </div>
                            <div class="stat">
                                <span class="stat-value">18.5</span>
                                <span class="stat-unit">kWh</span>
                                <span class="stat-label">Heute</span>
                            </div>
                            <div class="stat">
                                <span class="stat-value">€4.20</span>
                                <span class="stat-label">Kosten</span>
                            </div>
                        </div>
                    </div>
                    <div class="content-card praesenz">
                        <h3><i class="mdi mdi-account-multiple"></i> Präsenz</h3>
                        <div class="praesenz-list">
                            <div class="praesenz-item"><i class="mdi mdi-account"></i> Zuhause: 3</div>
                            <div class="praesenz-item"><i class="mdi mdi-door"></i> Anwesend: 2</div>
                        </div>
                    </div>
                    <div class="content-card automationen">
                        <h3><i class="mdi mdi-robot"></i> Automationen</h3>
                        <div class="automation-list">
                            <div class="automation-item active">
                                <span>Autolicht</span>
                                <span class="status">aktiv</span>
                            </div>
                            <div class="automation-item active">
                                <span>Heizungssteuerung</span>
                                <span class="status">aktiv</span>
                            </div>
                        </div>
                    </div>
                `;
            case 'styx':
                return `
                    <div class="content-card brain-graph">
                        <h3><i class="mdi mdi-brain"></i> Brain Graph</h3>
                        <div class="brain-visualization" id="brain-graph-canvas">
                            <canvas id="brain-canvas"></canvas>
                        </div>
                    </div>
                    <div class="content-card neural-dashboard">
                        <h3><i class="mdi mdi-chart-timeline-variant"></i> Neural Dashboard</h3>
                        <div class="neural-stats">
                            <div class="stat"><span class="stat-value">12</span><span class="stat-label">Neuronen</span></div>
                            <div class="stat"><span class="stat-value">48</span><span class="stat-label">Synapsen</span></div>
                            <div class="stat"><span class="stat-value">98%</span><span class="stat-label">Uptime</span></div>
                        </div>
                    </div>
                `;
            default:
                return '<div class="empty-state"><p>Tab Content wird geladen...</p></div>';
        }
    }
    
    setupTabNavigation() {
        // Keyboard navigation for 3 tabs
        document.addEventListener('keydown', (e) => {
            if (e.key === 'ArrowLeft' || e.key === 'ArrowRight') {
                const currentIndex = this.tabs.findIndex(t => t.id === this.activeTab);
                let newIndex = currentIndex;
                
                if (e.key === 'ArrowLeft' && currentIndex > 0) {
                    newIndex = currentIndex - 1;
                } else if (e.key === 'ArrowRight' && currentIndex < this.tabs.length - 1) {
                    newIndex = currentIndex + 1;
                }
                
                if (newIndex !== currentIndex) {
                    this.switchTab(this.tabs[newIndex].id);
                }
            }
        });
    }
    
    setupScrollButtons() {
        const scrollLeft = document.getElementById('scroll-left');
        const scrollRight = document.getElementById('scroll-right');
        const container = document.getElementById('tabs-container');
        
        if (scrollLeft && scrollRight && container) {
            scrollLeft.addEventListener('click', () => {
                container.scrollBy({ left: -200, behavior: 'smooth' });
            });
            
            scrollRight.addEventListener('click', () => {
                container.scrollBy({ left: 200, behavior: 'smooth' });
            });
            
            container.addEventListener('scroll', () => {
                this.updateScrollButtons();
            });
        }
    }
    
    updateScrollButtons() {
        const scrollLeft = document.getElementById('scroll-left');
        const scrollRight = document.getElementById('scroll-right');
        const container = document.getElementById('tabs-container');
        
        if (scrollLeft && scrollRight && container) {
            scrollLeft.disabled = container.scrollLeft === 0;
            scrollRight.disabled = container.scrollLeft + container.clientWidth >= container.scrollWidth - 1;
        }
    }
    
    switchTab(tabId) {
        if (this.activeTab === tabId) return;
        
        this.activeTab = tabId;
        
        // Update tab buttons (using data-tab attribute)
        document.querySelectorAll('.tab-item').forEach(tab => {
            tab.classList.toggle('active', tab.dataset.tab === tabId);
        });
        
        // Update tab panes
        document.querySelectorAll('.tab-pane').forEach(pane => {
            pane.classList.toggle('active', pane.id === `pane-${tabId}`);
        });
        
        // Scroll active tab into view
        const activeTabElement = document.querySelector(`.tab-item[data-tab="${tabId}"]`);
        if (activeTabElement) {
            activeTabElement.scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'center' });
        }
        
        this.updateLastUpdateTime();
        console.log(`[Dashboard] Switched to tab: ${tabId}`);
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
            console.log('[Dashboard] WebSocket connected');
            
            // Request zone data
            this.socket.emit('request_zone_data', { zones: this.zones.map(z => z.id) });
        });
        
        this.socket.on('disconnect', (reason) => {
            this.connected = false;
            this.updateConnectionStatus('disconnected');
            console.log('[Dashboard] WebSocket disconnected:', reason);
        });
        
        this.socket.on('connect_error', (error) => {
            console.error('[Dashboard] WebSocket connection error:', error);
        });
        
        this.socket.on('zone_update', (data) => {
            this.handleZoneUpdate(data);
        });
        
        this.socket.on('alert_update', (data) => {
            this.handleAlertUpdate(data);
        });
        
        this.socket.on('ha_discovery_complete', (data) => {
            this.hideLoading();
            this.loadZoneData();
            console.log('[Dashboard] HA Discovery complete');
        });
    }
    
    updateConnectionStatus(status) {
        const indicator = document.getElementById('connection-indicator');
        const statusText = document.getElementById('connection-status');
        
        if (indicator && statusText) {
            indicator.className = `status-indicator ${status}`;
            statusText.textContent = status === 'connected' ? 'Verbunden' : 'Getrennt';
        }
    }
    
    handleZoneUpdate(data) {
        if (!data.zoneId || !data.data) return;
        
        this.zoneData[data.zoneId] = data.data;
        this.renderZoneCards(data.zoneId);
        this.updateLastUpdateTime();
    }
    
    handleAlertUpdate(data) {
        if (!data.zoneId || typeof data.alertCount !== 'number') return;
        
        const zone = this.zones.find(z => z.id === data.zoneId);
        if (zone) {
            zone.alertCount = data.alertCount;
            this.updateAlertBadge(data.zoneId, data.alertCount);
            this.updateTotalAlerts();
        }
    }
    
    updateAlertBadge(zoneId, count) {
        const badge = document.getElementById(`badge-${zoneId}`);
        if (badge) {
            if (count > 0) {
                badge.textContent = count > 9 ? '9+' : count;
                badge.style.display = 'inline-block';
            } else {
                badge.style.display = 'none';
            }
        }
    }
    
    updateTotalAlerts() {
        const total = this.zones.reduce((sum, z) => sum + z.alertCount, 0);
        const badge = document.getElementById('alert-badge');
        if (badge) {
            badge.textContent = total > 9 ? '9+' : total;
        }
    }
    
    renderZoneCards(zoneId) {
        const grid = document.getElementById(`grid-${zoneId}`);
        if (!grid || !this.zoneData[zoneId]) return;
        
        const data = this.zoneData[zoneId];
        
        // Beispielhafte Darstellung (wird durch echte HA-Daten ersetzt)
        grid.innerHTML = `
            <div class="zone-card widget-container" data-widget-id="temp-${zoneId}" data-x="0" data-y="0">
                <div class="drag-handle" title="Zum Verschieben ziehen">
                    <i class="mdi mdi-drag"></i>
                </div>
                <div class="position-controls">
                    <button class="position-btn" onclick="dragDropManager.undo()" title="Rückgängig (Strg+Z)">
                        <i class="mdi mdi-undo"></i>
                    </button>
                    <button class="position-btn" onclick="dragDropManager.redo()" title="Wiederherstellen (Strg+Y)">
                        <i class="mdi mdi-redo"></i>
                    </button>
                </div>
                <div class="zone-card-header">
                    <div class="zone-card-icon">
                        <i class="mdi mdi-thermometer"></i>
                    </div>
                    <div class="zone-card-status">
                        <span class="status-dot"></span>
                        <span>Aktiv</span>
                    </div>
                </div>
                <div class="zone-card-title">Temperatur</div>
                <div class="zone-card-subtitle">Durchschnittswert</div>
                <div class="zone-card-metrics">
                    <div class="zone-metric">
                        <span class="zone-metric-label">Aktuell</span>
                        <span class="zone-metric-value">${data.temperature || '21.5'}°C</span>
                    </div>
                    <div class="zone-metric">
                        <span class="zone-metric-label">Ziel</span>
                        <span class="zone-metric-value">${data.targetTemp || '22.0'}°C</span>
                    </div>
                </div>
            </div>
            
            <div class="zone-card widget-container" data-widget-id="humidity-${zoneId}" data-x="0" data-y="0">
                <div class="drag-handle" title="Zum Verschieben ziehen">
                    <i class="mdi mdi-drag"></i>
                </div>
                <div class="position-controls">
                    <button class="position-btn" onclick="dragDropManager.undo()" title="Rückgängig (Strg+Z)">
                        <i class="mdi mdi-undo"></i>
                    </button>
                    <button class="position-btn" onclick="dragDropManager.redo()" title="Wiederherstellen (Strg+Y)">
                        <i class="mdi mdi-redo"></i>
                    </button>
                </div>
                <div class="zone-card-header">
                    <div class="zone-card-icon">
                        <i class="mdi mdi-water-percent"></i>
                    </div>
                    <div class="zone-card-status">
                        <span class="status-dot"></span>
                        <span>Aktiv</span>
                    </div>
                </div>
                <div class="zone-card-title">Luftfeuchtigkeit</div>
                <div class="zone-card-subtitle">Relative Feuchte</div>
                <div class="zone-card-metrics">
                    <div class="zone-metric">
                        <span class="zone-metric-label">Aktuell</span>
                        <span class="zone-metric-value">${data.humidity || '45'}%</span>
                    </div>
                    <div class="zone-metric">
                        <span class="zone-metric-label">Bereich</span>
                        <span class="zone-metric-value">40-60%</span>
                    </div>
                </div>
            </div>
            
            <div class="zone-card widget-container" data-widget-id="lights-${zoneId}" data-x="0" data-y="0">
                <div class="drag-handle" title="Zum Verschieben ziehen">
                    <i class="mdi mdi-drag"></i>
                </div>
                <div class="position-controls">
                    <button class="position-btn" onclick="dragDropManager.undo()" title="Rückgängig (Strg+Z)">
                        <i class="mdi mdi-undo"></i>
                    </button>
                    <button class="position-btn" onclick="dragDropManager.redo()" title="Wiederherstellen (Strg+Y)">
                        <i class="mdi mdi-redo"></i>
                    </button>
                </div>
                <div class="zone-card-header">
                    <div class="zone-card-icon">
                        <i class="mdi mdi-lightbulb"></i>
                    </div>
                    <div class="zone-card-status">
                        <span class="status-dot"></span>
                        <span>Aktiv</span>
                    </div>
                </div>
                <div class="zone-card-title">Beleuchtung</div>
                <div class="zone-card-subtitle">Aktive Lichter</div>
                <div class="zone-card-metrics">
                    <div class="zone-metric">
                        <span class="zone-metric-label">Anzahl</span>
                        <span class="zone-metric-value">${data.lights || '3'}</span>
                    </div>
                    <div class="zone-metric">
                        <span class="zone-metric-label">Helligkeit</span>
                        <span class="zone-metric-value">${data.brightness || '60'}%</span>
                    </div>
                </div>
            </div>
        `;
        
        // Drag & Drop für neue Cards aktivieren
        if (window.dragDropManager) {
            window.dragDropManager.enableDrag(`#grid-${zoneId} .widget-container`);
        }
    }
    
    loadZoneData() {
        // Simuliertes Laden von Zonendaten (wird durch echte API ersetzt)
        this.zones.forEach(zone => {
            this.zoneData[zone.id] = {
                temperature: (20 + Math.random() * 3).toFixed(1),
                targetTemp: (21 + Math.random() * 2).toFixed(1),
                humidity: Math.floor(40 + Math.random() * 20),
                lights: Math.floor(Math.random() * 5),
                brightness: Math.floor(40 + Math.random() * 40)
            };
            this.renderZoneCards(zone.id);
        });
    }
    
    refreshZone(zoneId) {
        console.log(`[Dashboard] Refreshing zone: ${zoneId}`);
        if (this.socket && this.connected) {
            this.socket.emit('request_zone_data', { zones: [zoneId] });
        }
    }
    
    showZoneSettings(zoneId) {
        console.log(`[Dashboard] Opening settings for zone: ${zoneId}`);
        // Hier könnte ein Modal oder eine separate Einstellungsseite geöffnet werden
        alert(`Einstellungen für ${zoneId} werden geöffnet...`);
    }
    
    refreshTab(tabId) {
        console.log(`[Dashboard] Refreshing tab: ${tabId}`);
        // Trigger content refresh for the tab
        const pane = document.getElementById(`pane-${tabId}`);
        if (pane) {
            const grid = pane.querySelector('.tab-content-grid');
            if (grid) {
                // Re-render tab content
                grid.innerHTML = this.getTabContent(tabId);
            }
        }
        this.updateLastUpdateTime();
    }
    
    showTabSettings(tabId) {
        console.log(`[Dashboard] Show settings for tab: ${tabId}`);
        // Settings panel would open here
        alert(`Einstellungen für ${tabId} - wird in Kürze verfügbar sein`);
    }
    
    hideLoading() {
        const overlay = document.getElementById('loading-overlay');
        if (overlay) {
            overlay.classList.add('hidden');
        }
    }
    
    updateLastUpdateTime() {
        const now = new Date();
        const timeString = now.toLocaleTimeString('de-DE');
        const element = document.getElementById('last-update-time');
        if (element) {
            element.textContent = timeString;
        }
    }
}

// Dashboard initialisieren
let dashboard;
document.addEventListener('DOMContentLoaded', () => {
    dashboard = new HabitusDashboard();
});

// Export für globalen Zugriff
window.dashboard = dashboard;
