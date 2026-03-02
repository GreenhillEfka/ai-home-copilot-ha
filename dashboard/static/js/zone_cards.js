/**
 * Zone Cards - Live Data Loading & Interactive Features
 * - WebSocket connection for live updates (5s interval)
 * - D3.js Sparklines for 24h history charts
 * - Quick actions for light control and scene activation
 * - Alert badges and status indicators
 */

class ZoneCardsManager {
    constructor(options = {}) {
        this.containerSelector = options.containerSelector || '#zone-cards-container';
        this.socket = null;
        this.zonesData = {};
        this.zonesHistory = {};
        this.charts = {};
        this.updateInterval = options.updateInterval || 5000; // 5 seconds
        this.d3 = null;
        
        // Initialize
        this.init();
    }
    
    init() {
        console.log('[ZoneCards] Initializing...');
        this.loadD3();
        this.connectWebSocket();
        this.setupEventListeners();
    }
    
    loadD3() {
        // Load D3.js if not already loaded
        if (typeof d3 !== 'undefined') {
            this.d3 = d3;
            this.onD3Loaded();
        } else {
            const script = document.createElement('script');
            script.src = 'https://d3js.org/d3.v7.min.js';
            script.onload = () => {
                this.d3 = window.d3;
                console.log('[ZoneCards] D3.js loaded');
                this.onD3Loaded();
            };
            document.head.appendChild(script);
        }
    }
    
    onD3Loaded() {
        console.log('[ZoneCards] D3.js ready, initializing charts');
    }
    
    connectWebSocket() {
        // Use existing Socket.IO connection or create new one
        if (typeof io !== 'undefined') {
            this.socket = io('/zone_summary', {
                transports: ['websocket', 'polling'],
                reconnection: true,
                reconnectionDelay: 1000,
                reconnectionAttempts: 5
            });
            
            this.socket.on('connect', () => {
                console.log('[ZoneCards] Connected to zone_summary namespace');
                this.socket.emit('request_zones');
            });
            
            this.socket.on('zone_data', (data) => {
                this.handleZoneData(data);
            });
            
            this.socket.on('zone_update', (data) => {
                this.handleZoneUpdate(data);
            });
            
            this.socket.on('light_control_result', (data) => {
                this.handleLightControlResult(data);
            });
            
            this.socket.on('scene_result', (data) => {
                this.handleSceneResult(data);
            });
            
            this.socket.on('disconnect', () => {
                console.log('[ZoneCards] Disconnected from zone_summary namespace');
            });
        } else {
            console.error('[ZoneCards] Socket.IO not available');
        }
    }
    
    handleZoneData(data) {
        console.log('[ZoneCards] Received zone data:', data);
        this.zonesData = data.zones || {};
        this.zonesHistory = data.history || {};
        
        // Render all zone cards
        this.renderZoneCards();
        
        // Update charts
        this.updateAllCharts();
    }
    
    handleZoneUpdate(data) {
        const zoneId = data.zoneId || data.id;
        if (zoneId && this.zonesData[zoneId]) {
            this.zonesData[zoneId] = { ...this.zonesData[zoneId], ...data.data };
            this.updateZoneCard(zoneId);
            
            // Update chart if history is included
            if (data.history) {
                this.zonesHistory[zoneId] = data.history;
                this.updateChart(zoneId);
            }
        }
    }
    
    renderZoneCards() {
        const container = document.querySelector(this.containerSelector);
        if (!container) {
            console.error('[ZoneCards] Container not found:', this.containerSelector);
            return;
        }
        
        container.innerHTML = '';
        
        Object.keys(this.zonesData).forEach(zoneId => {
            const zoneData = this.zonesData[zoneId];
            const card = this.createZoneCard(zoneId, zoneData);
            container.appendChild(card);
        });
    }
    
    createZoneCard(zoneId, data) {
        const card = document.createElement('div');
        card.className = 'zone-card';
        card.dataset.zoneId = zoneId;
        
        // Determine status classes
        const tempStatus = this.getTemperatureStatus(data.temperature, zoneId);
        const humidityStatus = this.getHumidityStatus(data.humidity, zoneId);
        const lightState = data.light_state || 'off';
        const motionClass = data.motion ? 'active' : 'idle';
        const hasAlerts = data.alerts && data.alerts.length > 0;
        const statusClass = hasAlerts ? 'has-alerts' : 'ok';
        const statusText = hasAlerts ? `${data.alerts.length} Probleme` : 'OK';
        
        card.innerHTML = `
            <div class="zone-card-header">
                <div class="zone-card-icon">
                    <span class="mdi mdi-${data.icon || 'home'}"></span>
                </div>
                <div class="zone-card-title">
                    <h3 class="zone-name">${data.name || zoneId}</h3>
                    <span class="zone-status ${statusClass}">${statusText}</span>
                </div>
                <div class="zone-card-alerts">
                    ${hasAlerts ? `
                    <span class="alert-badge ${data.alerts[0].type}">
                        <span class="mdi mdi-${data.alerts[0].icon}"></span>
                        <span class="alert-count">${data.alerts.length}</span>
                    </span>
                    ` : ''}
                </div>
            </div>
            
            <div class="zone-card-metrics">
                <!-- Temperature -->
                <div class="metric-item ${tempStatus}" title="Temperatur">
                    <div class="metric-icon">
                        <span class="mdi mdi-thermometer"></span>
                    </div>
                    <div class="metric-value">
                        <span class="value">${data.temperature !== undefined ? data.temperature.toFixed(1) : '--'}</span>
                        <span class="unit">°C</span>
                    </div>
                    <div class="metric-label">Temperatur</div>
                    ${tempStatus === 'warning' || tempStatus === 'danger' ? `
                    <div class="metric-alert">
                        <span class="mdi mdi-alert"></span>
                    </div>
                    ` : ''}
                </div>
                
                <!-- Humidity -->
                <div class="metric-item ${humidityStatus}" title="Luftfeuchtigkeit">
                    <div class="metric-icon">
                        <span class="mdi mdi-water-percent"></span>
                    </div>
                    <div class="metric-value">
                        <span class="value">${data.humidity !== undefined ? data.humidity.toFixed(1) : '--'}</span>
                        <span class="unit">%</span>
                    </div>
                    <div class="metric-label">Luftfeuchtigkeit</div>
                </div>
                
                <!-- Light Status -->
                <div class="metric-item light-status ${lightState}" title="Licht">
                    <div class="metric-icon">
                        <span class="mdi mdi-lightbulb"></span>
                    </div>
                    <div class="metric-value">
                        <span class="value">${lightState === 'on' ? 'An' : 'Aus'}</span>
                    </div>
                    <div class="metric-label">Licht</div>
                    ${lightState === 'on' ? `
                    <div class="metric-detail">${data.light_brightness || 0}%</div>
                    ` : ''}
                </div>
                
                <!-- Motion -->
                <div class="metric-item motion-status ${motionClass}" title="Bewegung">
                    <div class="metric-icon">
                        <span class="mdi mdi-motion-sensor"></span>
                    </div>
                    <div class="metric-value">
                        <span class="value">${data.motion ? 'Ja' : 'Nein'}</span>
                    </div>
                    <div class="metric-label">Bewegung</div>
                </div>
            </div>
            
            <!-- Mini Chart (24h Sparkline) -->
            <div class="zone-card-chart">
                <div class="chart-header">
                    <span class="chart-title">24h Verlauf</span>
                    <div class="chart-toggle">
                        <button class="chart-btn active" data-zone="${zoneId}" data-metric="temperature">
                            <span class="mdi mdi-thermometer"></span>
                        </button>
                        <button class="chart-btn" data-zone="${zoneId}" data-metric="humidity">
                            <span class="mdi mdi-water-percent"></span>
                        </button>
                    </div>
                </div>
                <div class="chart-container" id="chart-${zoneId}">
                    <svg class="sparkline" width="100%" height="60"></svg>
                </div>
            </div>
            
            <!-- Quick Actions -->
            <div class="zone-card-actions">
                <button class="action-btn light-toggle" data-zone-id="${zoneId}" data-action="toggle" title="Licht umschalten">
                    <span class="mdi mdi-${lightState === 'on' ? 'lightbulb' : 'lightbulb-outline'}"></span>
                    <span>Licht</span>
                </button>
                <button class="action-btn scene-btn" data-zone-id="${zoneId}" data-action="scene" title="Szene wählen">
                    <span class="mdi mdi-palette"></span>
                    <span>Szene</span>
                </button>
                <button class="action-btn details-btn" data-zone-id="${zoneId}" data-action="details" title="Details anzeigen">
                    <span class="mdi mdi-chevron-right"></span>
                    <span>Details</span>
                </button>
            </div>
            
            <!-- Alert Details (hidden by default, shown on hover) -->
            ${hasAlerts ? `
            <div class="zone-card-alert-details">
                ${data.alerts.map(alert => `
                <div class="alert-item ${alert.type}">
                    <span class="mdi mdi-${alert.icon}"></span>
                    <span class="alert-message">${alert.message}</span>
                </div>
                `).join('')}
            </div>
            ` : ''}
        `;
        
        return card;
    }
    
    updateZoneCard(zoneId) {
        const card = document.querySelector(`.zone-card[data-zone-id="${zoneId}"]`);
        if (!card) return;
        
        const data = this.zonesData[zoneId];
        if (!data) return;
        
        // Update temperature
        const tempValue = card.querySelector('.metric-item .metric-value .value');
        if (tempValue && data.temperature !== undefined) {
            tempValue.textContent = data.temperature.toFixed(1);
        }
        
        // Update humidity
        const humidityValue = card.querySelectorAll('.metric-item .metric-value .value')[1];
        if (humidityValue && data.humidity !== undefined) {
            humidityValue.textContent = data.humidity.toFixed(1);
        }
        
        // Update light status
        const lightMetric = card.querySelector('.light-status');
        if (lightMetric) {
            lightMetric.classList.remove('on', 'off');
            lightMetric.classList.add(data.light_state || 'off');
            
            const lightValue = lightMetric.querySelector('.metric-value .value');
            if (lightValue) {
                lightValue.textContent = data.light_state === 'on' ? 'An' : 'Aus';
            }
            
            const lightIcon = lightMetric.querySelector('.metric-icon .mdi');
            if (lightIcon) {
                lightIcon.className = `mdi mdi-${data.light_state === 'on' ? 'lightbulb' : 'lightbulb-outline'}`;
            }
        }
        
        // Update motion
        const motionMetric = card.querySelector('.motion-status');
        if (motionMetric) {
            motionMetric.classList.remove('active', 'idle');
            motionMetric.classList.add(data.motion ? 'active' : 'idle');
            
            const motionValue = motionMetric.querySelector('.metric-value .value');
            if (motionValue) {
                motionValue.textContent = data.motion ? 'Ja' : 'Nein';
            }
        }
        
        // Update status badge
        const statusBadge = card.querySelector('.zone-status');
        const alertBadge = card.querySelector('.alert-badge');
        const alertDetails = card.querySelector('.zone-card-alert-details');
        
        if (data.alerts && data.alerts.length > 0) {
            if (statusBadge) {
                statusBadge.className = `zone-status has-alerts`;
                statusBadge.textContent = `${data.alerts.length} Probleme`;
            }
            if (!alertBadge && data.alerts.length > 0) {
                // Create alert badge if not exists
                const alertsContainer = card.querySelector('.zone-card-alerts');
                if (alertsContainer) {
                    alertsContainer.innerHTML = `
                        <span class="alert-badge ${data.alerts[0].type}">
                            <span class="mdi mdi-${data.alerts[0].icon}"></span>
                            <span class="alert-count">${data.alerts.length}</span>
                        </span>
                    `;
                }
            }
            if (!alertDetails && data.alerts.length > 0) {
                // Create alert details if not exists
                const alertHtml = `
                    <div class="zone-card-alert-details">
                        ${data.alerts.map(alert => `
                        <div class="alert-item ${alert.type}">
                            <span class="mdi mdi-${alert.icon}"></span>
                            <span class="alert-message">${alert.message}</span>
                        </div>
                        `).join('')}
                    </div>
                `;
                card.insertAdjacentHTML('beforeend', alertHtml);
            }
        } else {
            if (statusBadge) {
                statusBadge.className = 'zone-status ok';
                statusBadge.textContent = 'OK';
            }
            if (alertBadge) {
                alertBadge.remove();
            }
            if (alertDetails) {
                alertDetails.remove();
            }
        }
    }
    
    updateAllCharts() {
        Object.keys(this.zonesData).forEach(zoneId => {
            this.updateChart(zoneId);
        });
    }
    
    updateChart(zoneId) {
        if (!this.d3) return;
        
        const history = this.zonesHistory[zoneId];
        if (!history || !history.temperature) return;
        
        const svg = document.querySelector(`#chart-${zoneId} .sparkline`);
        if (!svg) return;
        
        // Get current metric (default: temperature)
        const chartBtn = document.querySelector(`.chart-btn.active[data-zone="${zoneId}"]`);
        const metric = chartBtn ? chartBtn.dataset.metric : 'temperature';
        
        const data = history[metric] || history.temperature;
        if (!data || data.length === 0) return;
        
        // Clear existing chart
        this.d3.select(svg).selectAll('*').remove();
        
        const width = svg.clientWidth || 300;
        const height = svg.clientHeight || 60;
        const margin = { top: 5, right: 5, bottom: 5, left: 5 };
        const innerWidth = width - margin.left - margin.right;
        const innerHeight = height - margin.top - margin.bottom;
        
        // Create scales
        const x = this.d3.scaleLinear()
            .domain([0, data.length - 1])
            .range([0, innerWidth]);
        
        const values = data.map(d => d.value);
        const min = Math.min(...values);
        const max = Math.max(...values);
        const range = max - min || 1;
        
        const y = this.d3.scaleLinear()
            .domain([min - range * 0.1, max + range * 0.1])
            .range([innerHeight, 0]);
        
        // Create line generator
        const line = this.d3.line()
            .x((d, i) => x(i))
            .y(d => y(d.value))
            .curve(this.d3.curveMonotoneX);
        
        // Add gradient
        const gradient = this.d3.select(svg)
            .append('defs')
            .append('linearGradient')
            .attr('id', `gradient-${zoneId}-${metric}`)
            .attr('x1', '0%')
            .attr('y1', '0%')
            .attr('x2', '0%')
            .attr('y2', '100%');
        
        gradient.append('stop')
            .attr('offset', '0%')
            .attr('stop-color', metric === 'temperature' ? '#ef4444' : '#3b82f6')
            .attr('stop-opacity', 0.3);
        
        gradient.append('stop')
            .attr('offset', '100%')
            .attr('stop-color', metric === 'temperature' ? '#ef4444' : '#3b82f6')
            .attr('stop-opacity', 0);
        
        // Add area
        const area = this.d3.area()
            .x((d, i) => x(i))
            .y0(innerHeight)
            .y1(d => y(d.value))
            .curve(this.d3.curveMonotoneX);
        
        this.d3.select(svg)
            .append('path')
            .datum(data)
            .attr('fill', `url(#gradient-${zoneId}-${metric})`)
            .attr('d', area);
        
        // Add line
        this.d3.select(svg)
            .append('path')
            .datum(data)
            .attr('fill', 'none')
            .attr('stroke', metric === 'temperature' ? '#ef4444' : '#3b82f6')
            .attr('stroke-width', 2)
            .attr('d', line);
        
        // Add current value dot
        const lastPoint = data[data.length - 1];
        this.d3.select(svg)
            .append('circle')
            .attr('cx', x(data.length - 1))
            .attr('cy', y(lastPoint.value))
            .attr('r', 3)
            .attr('fill', metric === 'temperature' ? '#ef4444' : '#3b82f6');
    }
    
    setupEventListeners() {
        // Chart metric toggle
        document.addEventListener('click', (e) => {
            if (e.target.closest('.chart-btn')) {
                const btn = e.target.closest('.chart-btn');
                const zoneId = btn.dataset.zone;
                const metric = btn.dataset.metric;
                
                // Update active state
                document.querySelectorAll(`.chart-btn[data-zone="${zoneId}"]`).forEach(b => {
                    b.classList.remove('active');
                });
                btn.classList.add('active');
                
                // Redraw chart
                this.updateChart(zoneId);
            }
            
            // Light toggle
            if (e.target.closest('.light-toggle')) {
                const btn = e.target.closest('.light-toggle');
                const zoneId = btn.dataset.zoneId;
                this.toggleLight(zoneId);
            }
            
            // Scene button
            if (e.target.closest('.scene-btn')) {
                const btn = e.target.closest('.scene-btn');
                const zoneId = btn.dataset.zoneId;
                this.showSceneSelector(zoneId);
            }
            
            // Details button
            if (e.target.closest('.details-btn')) {
                const btn = e.target.closest('.details-btn');
                const zoneId = btn.dataset.zoneId;
                this.showZoneDetails(zoneId);
            }
        });
    }
    
    toggleLight(zoneId) {
        const currentData = this.zonesData[zoneId];
        if (!currentData) return;
        
        const newAction = currentData.light_state === 'on' ? 'off' : 'on';
        const brightness = newAction === 'on' ? 80 : 0;
        
        if (this.socket) {
            this.socket.emit('light_control', {
                zone_id: zoneId,
                action: newAction,
                brightness: brightness
            });
        }
    }
    
    showSceneSelector(zoneId) {
        // In production, this would show a scene selection modal
        const scenes = ['Entspannen', 'Fokus', 'Lesen', 'Film', 'Nacht'];
        const selectedScene = prompt('Szene wählen:\n' + scenes.map((s, i) => `${i + 1}. ${s}`).join('\n'));
        
        if (selectedScene && scenes[selectedScene - 1]) {
            const scene = scenes[selectedScene - 1];
            if (this.socket) {
                this.socket.emit('scene_activate', {
                    zone_id: zoneId,
                    scene: scene
                });
            }
        }
    }
    
    showZoneDetails(zoneId) {
        // In production, this would open a detailed zone modal
        const data = this.zonesData[zoneId];
        if (!data) return;
        
        alert(`${data.name}\n\n` +
              `Temperatur: ${data.temperature}°C\n` +
              `Luftfeuchtigkeit: ${data.humidity}%\n` +
              `Licht: ${data.light_state === 'on' ? 'An (' + data.light_brightness + '%)' : 'Aus'}\n` +
              `Bewegung: ${data.motion ? 'Ja' : 'Nein'}\n` +
              `Fenster: ${data.window_open ? 'Offen' : 'Geschlossen'}\n` +
              (data.alerts && data.alerts.length > 0 ? `\nProbleme:\n${data.alerts.map(a => '- ' + a.message).join('\n')}` : '')
        );
    }
    
    handleLightControlResult(data) {
        console.log('[ZoneCards] Light control result:', data);
        if (data.success) {
            // Visual feedback
            const btn = document.querySelector(`.light-toggle[data-zone-id="${data.zone_id}"]`);
            if (btn) {
                btn.classList.add('action-success');
                setTimeout(() => btn.classList.remove('action-success'), 1000);
            }
        }
    }
    
    handleSceneResult(data) {
        console.log('[ZoneCards] Scene result:', data);
        if (data.success) {
            // Visual feedback
            const btn = document.querySelector(`.scene-btn[data-zone-id="${data.zone_id}"]`);
            if (btn) {
                btn.classList.add('action-success');
                setTimeout(() => btn.classList.remove('action-success'), 1000);
            }
        }
    }
    
    getTemperatureStatus(temp, zoneId) {
        // In production, use actual thresholds from ZONE_CONFIG
        if (temp < 18) return 'danger';
        if (temp < 20 || temp > 26) return 'warning';
        return 'ok';
    }
    
    getHumidityStatus(humidity, zoneId) {
        // In production, use actual thresholds from ZONE_CONFIG
        if (humidity < 30 || humidity > 70) return 'warning';
        return 'ok';
    }
}

// Auto-initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.zoneCardsManager = new ZoneCardsManager({
        containerSelector: '#zone-cards-container'
    });
});
