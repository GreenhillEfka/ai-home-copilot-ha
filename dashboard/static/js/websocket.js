/**
 * WebSocket Client with Performance Optimizations
 * - Client-side debouncing to prevent excessive re-renders
 * - Batch update handling
 * - Latency monitoring
 */

class DashboardWebSocket {
    constructor(url, options = {}) {
        this.url = url;
        this.socket = null;
        this.connected = false;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = options.maxReconnectAttempts || 5;
        this.reconnectDelay = options.reconnectDelay || 1000;
        
        // Debouncing configuration
        this.debounceInterval = options.debounceInterval || 300; // ms
        this.lastRenderTime = {};
        this.pendingUpdates = {};
        this.renderTimers = {};
        
        // Performance tracking
        this.latencyHistory = [];
        this.lastPingTime = null;
        this.currentLatency = 0;
        
        // Callbacks
        this.onConnect = options.onConnect || (() => {});
        this.onDisconnect = options.onDisconnect || (() => {});
        this.onError = options.onError || (() => {});
        this.onUpdate = options.onUpdate || (() => {});
    }
    
    connect() {
        console.log('[WebSocket] Connecting to', this.url);
        this.socket = io(this.url, {
            transports: ['websocket', 'polling'],
            upgrade: true,
            forceNew: false,
            reconnection: true,
            reconnectionDelay: this.reconnectDelay,
            reconnectionDelayMax: 5000,
            reconnectionAttempts: this.maxReconnectAttempts,
            timeout: 10000
        });
        
        this.socket.on('connect', () => {
            this.connected = true;
            this.reconnectAttempts = 0;
            console.log('[WebSocket] Connected');
            this.onConnect();
            
            // Start latency monitoring
            this.startLatencyMonitoring();
        });
        
        this.socket.on('disconnect', (reason) => {
            this.connected = false;
            console.log('[WebSocket] Disconnected:', reason);
            this.onDisconnect(reason);
        });
        
        this.socket.on('connect_error', (error) => {
            console.error('[WebSocket] Connection error:', error);
            this.onError(error);
        });
        
        this.socket.on('connected', (data) => {
            console.log('[WebSocket] Server confirmed connection:', data);
            if (data.performance) {
                console.log('[WebSocket] Performance config:', data.performance);
            }
        });
        
        this.socket.on('batch_update', (data) => {
            this.handleBatchUpdate(data);
        });
        
        this.socket.on('update', (data) => {
            this.handleUpdate(data);
        });
        
        this.socket.on('performance_pong', (data) => {
            this.handlePong(data);
        });
        
        this.socket.on('metrics', (data) => {
            this.handleWidgetUpdate('system_status', data);
        });
        
        this.socket.on('sensor_data', (data) => {
            this.handleWidgetUpdate('sensor_overview', data);
        });
    }
    
    handleBatchUpdate(data) {
        if (!data.batch || !data.updates) {
            console.warn('[WebSocket] Invalid batch update');
            return;
        }
        
        console.log(`[WebSocket] Received batch: ${data.count} updates`);
        
        // Process each update in the batch
        data.updates.forEach(update => {
            this.handleUpdate({
                type: update.event,
                data: update.data,
                timestamp: update.timestamp
            });
        });
    }
    
    handleUpdate(data) {
        const updateType = data.type || 'unknown';
        const now = Date.now();
        
        // Check if we should debounce this update
        const lastRender = this.lastRenderTime[updateType] || 0;
        const timeSinceLastRender = now - lastRender;
        
        if (timeSinceLastRender < this.debounceInterval) {
            // Queue for later
            if (!this.pendingUpdates[updateType]) {
                this.pendingUpdates[updateType] = [];
            }
            this.pendingUpdates[updateType].push(data);
            
            // Clear existing timer
            if (this.renderTimers[updateType]) {
                clearTimeout(this.renderTimers[updateType]);
            }
            
            // Schedule render after debounce interval
            this.renderTimers[updateType] = setTimeout(() => {
                this.flushPendingUpdates(updateType);
            }, this.debounceInterval - timeSinceLastRender);
            
            console.log(`[WebSocket] Debouncing ${updateType} (waiting ${this.debounceInterval - timeSinceLastRender}ms)`);
        } else {
            // Render immediately
            this.renderUpdate(updateType, data);
        }
    }
    
    flushPendingUpdates(updateType) {
        const pending = this.pendingUpdates[updateType];
        if (!pending || pending.length === 0) return;
        
        console.log(`[WebSocket] Flushing ${pending.length} pending ${updateType} updates`);
        
        // Only render the most recent update
        const latestUpdate = pending[pending.length - 1];
        this.renderUpdate(updateType, latestUpdate);
        
        // Clear pending
        this.pendingUpdates[updateType] = [];
        this.renderTimers[updateType] = null;
    }
    
    renderUpdate(updateType, data) {
        this.lastRenderTime[updateType] = Date.now();
        this.onUpdate(updateType, data);
    }
    
    handleWidgetUpdate(widgetType, data) {
        this.handleUpdate({
            type: widgetType,
            data: data,
            timestamp: Date.now()
        });
    }
    
    startLatencyMonitoring() {
        // Send ping every 5 seconds
        setInterval(() => {
            if (this.connected) {
                this.sendPing();
            }
        }, 5000);
    }
    
    sendPing() {
        this.lastPingTime = Date.now();
        this.socket.emit('performance_ping', {
            timestamp: this.lastPingTime
        });
    }
    
    handlePong(data) {
        const now = Date.now();
        const latency = now - data.client_timestamp;
        
        this.currentLatency = latency;
        this.latencyHistory.push({
            timestamp: now,
            latency: latency
        });
        
        // Keep only last 20 measurements
        if (this.latencyHistory.length > 20) {
            this.latencyHistory.shift();
        }
        
        // Calculate average
        const avgLatency = this.latencyHistory.reduce((sum, m) => sum + m.latency, 0) / this.latencyHistory.length;
        
        console.log(`[WebSocket] Latency: ${latency.toFixed(2)}ms (avg: ${avgLatency.toFixed(2)}ms)`);
        
        // Alert if latency exceeds target
        if (latency > 100) {
            console.warn(`[WebSocket] High latency detected: ${latency.toFixed(2)}ms (target: <100ms)`);
        }
    }
    
    getAverageLatency() {
        if (this.latencyHistory.length === 0) return null;
        return this.latencyHistory.reduce((sum, m) => sum + m.latency, 0) / this.latencyHistory.length;
    }
    
    emit(event, data) {
        if (this.connected && this.socket) {
            this.socket.emit(event, data);
        } else {
            console.warn('[WebSocket] Cannot emit, not connected');
        }
    }
    
    disconnect() {
        if (this.socket) {
            this.socket.disconnect();
            this.socket = null;
            this.connected = false;
        }
    }
}

// Export for use in dashboard
window.DashboardWebSocket = DashboardWebSocket;
