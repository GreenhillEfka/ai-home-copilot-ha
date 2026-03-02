/**
 * PilotSuite Styx - Drag & Drop Logic
 * Interact.js based drag & drop with touch support, snap-to-grid, and undo/redo
 */

class DragDropManager {
    constructor(options = {}) {
        this.options = {
            gridSnap: options.gridSnap || 20,          // Grid-Größe in Pixeln
            snapToGrid: options.snapToGrid !== false,  // Snap-to-Grid aktivieren
            showGrid: options.showGrid || false,       // Grid anzeigen
            allowResize: options.allowResize || true,  // Resize aktivieren
            maxWidgets: options.maxWidgets || 50,      // Maximale Widget-Anzahl
            apiBaseUrl: options.apiBaseUrl || '/api/v1/widgets',
            ...options
        };

        this.widgets = new Map();           // Widget-Daten speichern
        this.dragState = {                  // Aktueller Drag-Status
            activeWidget: null,
            startX: 0,
            startY: 0,
            initialX: 0,
            initialY: 0
        };
        this.undoStack = [];                // Undo-History
        this.redoStack = [];                // Redo-History
        this.socket = null;                 // WebSocket-Verbindung
        this.interact = null;               // Interact.js Instanz

        this.init();
    }

    init() {
        console.log('[DragDrop] Initializing Drag & Drop Manager...');
        
        // Interact.js laden (wenn nicht vorhanden)
        this.loadInteractJS().then(() => {
            this.setupInteract();
            this.loadWidgetPositions();
            this.setupWebSocket();
            this.setupKeyboardShortcuts();
            this.showGridIfEnabled();
        });

        // Touch-Gesten für Mobile
        this.setupTouchGestures();
    }

    async loadInteractJS() {
        if (typeof interact !== 'undefined') {
            return Promise.resolve();
        }

        return new Promise((resolve, reject) => {
            const script = document.createElement('script');
            script.src = 'https://cdn.jsdelivr.net/npm/interactjs@1.10.26/dist/interact.min.js';
            script.onload = () => {
                console.log('[DragDrop] Interact.js loaded');
                resolve();
            };
            script.onerror = () => {
                console.error('[DragDrop] Failed to load Interact.js');
                reject(new Error('Failed to load Interact.js'));
            };
            document.head.appendChild(script);
        });
    }

    setupInteract() {
        // Interact.js Konfiguration
        interact('.widget-container, .zone-card, .dashboard-widget')
            .draggable({
                allowFrom: '.drag-handle',  // Nur von特定 Elementen draggen
                listeners: {
                    start: (event) => this.onDragStart(event),
                    move: (event) => this.onDragMove(event),
                    end: (event) => this.onDragEnd(event)
                },
                modifiers: this.options.snapToGrid ? [
                    interact.modifiers.snap({
                        targets: [
                            interact.createSnapGrid({
                                x: this.options.gridSnap,
                                y: this.options.gridSnap
                            })
                        ],
                        relativePoints: [{ x: 0, y: 0 }]
                    }),
                    interact.modifiers.restrictRect({
                        restriction: 'parent',
                        endOnly: true
                    })
                ] : [],
                inertia: {
                    enabled: true,
                    resistance: 15,
                    minSpeed: 50,
                    endSpeed: 10
                }
            })
            .resizable(this.options.allowResize ? {
                edges: {
                    top: '.resize-handle.n, .resize-handle.nw, .resize-handle.ne',
                    left: '.resize-handle.w, .resize-handle.nw, .resize-handle.sw',
                    bottom: '.resize-handle.s, .resize-handle.sw, .resize-handle.se',
                    right: '.resize-handle.e, .resize-handle.ne, .resize-handle.se'
                },
                listeners: {
                    start: (event) => this.onResizeStart(event),
                    move: (event) => this.onResizeMove(event),
                    end: (event) => this.onResizeEnd(event)
                },
                modifiers: [
                    interact.modifiers.restrictSize({
                        min: { width: 100, height: 100 },
                        max: { width: 800, height: 600 }
                    })
                ],
                inertia: true
            } : false)
            .on('tap', (event) => this.onWidgetTap(event));

        this.interact = interact;
        console.log('[DragDrop] Interact.js configured');
    }

    onDragStart(event) {
        const widgetEl = event.target;
        const widgetId = widgetEl.dataset.widgetId;

        if (!widgetId) {
            console.warn('[DragDrop] Widget has no ID');
            return;
        }

        // Drag-State speichern
        this.dragState = {
            activeWidget: widgetId,
            startX: event.pageX,
            startY: event.pageY,
            initialX: parseFloat(widgetEl.dataset.x || 0),
            initialY: parseFloat(widgetEl.dataset.y || 0)
        };

        // Widget zur History hinzufügen (für Undo)
        this.addToUndoStack(widgetId);

        // Visuelles Feedback
        widgetEl.classList.add('dragging');
        this.showPositionIndicator(widgetEl, this.dragState.initialX, this.dragState.initialY);

        console.log(`[DragDrop] Drag started: ${widgetId}`);
    }

    onDragMove(event) {
        const widgetEl = event.target;
        const widgetId = widgetEl.dataset.widgetId;

        if (!widgetId || !this.dragState.activeWidget) return;

        // Neue Position berechnen
        const x = this.dragState.initialX + event.dx;
        const y = this.dragState.initialY + event.dy;

        // Position anwenden
        widgetEl.style.transform = `translate(${x}px, ${y}px)`;

        // Dataset aktualisieren
        widgetEl.dataset.x = x;
        widgetEl.dataset.y = y;

        // Position-Indicator aktualisieren
        this.showPositionIndicator(widgetEl, Math.round(x), Math.round(y));

        // Snap-to-Grid visuelles Feedback
        if (this.options.snapToGrid) {
            this.showSnapLines(widgetEl, x, y);
        }
    }

    onDragEnd(event) {
        const widgetEl = event.target;
        const widgetId = widgetEl.dataset.widgetId;

        if (!widgetId) return;

        // Finale Position berechnen
        const x = parseFloat(widgetEl.dataset.x || 0);
        const y = parseFloat(widgetEl.dataset.y || 0);

        // Grid-Snap (falls aktiviert)
        const snappedX = this.options.snapToGrid 
            ? Math.round(x / this.options.gridSnap) * this.options.gridSnap 
            : x;
        const snappedY = this.options.snapToGrid 
            ? Math.round(y / this.options.gridSnap) * this.options.gridSnap 
            : y;

        // Endgültige Position anwenden
        widgetEl.style.transform = `translate(${snappedX}px, ${snappedY}px)`;
        widgetEl.dataset.x = snappedX;
        widgetEl.dataset.y = snappedY;

        // Visuelles Feedback entfernen
        widgetEl.classList.remove('dragging');
        this.hidePositionIndicator(widgetEl);
        this.hideSnapLines();

        // Position speichern
        this.saveWidgetPosition(widgetId, snappedX, snappedY);

        console.log(`[DragDrop] Drag ended: ${widgetId} at (${snappedX}, ${snappedY})`);

        // Drag-State zurücksetzen
        this.dragState = {
            activeWidget: null,
            startX: 0,
            startY: 0,
            initialX: 0,
            initialY: 0
        };
    }

    onResizeStart(event) {
        const widgetEl = event.target;
        const widgetId = widgetEl.dataset.widgetId;

        if (!widgetId) return;

        // Resize-State speichern
        widgetEl.dataset.originalWidth = widgetEl.offsetWidth;
        widgetEl.dataset.originalHeight = widgetEl.offsetHeight;

        // Zur History hinzufügen
        this.addToUndoStack(widgetId);

        widgetEl.classList.add('resizing');
        console.log(`[DragDrop] Resize started: ${widgetId}`);
    }

    onResizeMove(event) {
        const widgetEl = event.target;
        const widgetId = widgetEl.dataset.widgetId;

        if (!widgetId) return;

        // Neue Größe anwenden
        widgetEl.style.width = `${event.rect.width}px`;
        widgetEl.style.height = `${event.rect.height}px`;

        // Transform beibehalten
        const x = parseFloat(widgetEl.dataset.x || 0);
        const y = parseFloat(widgetEl.dataset.y || 0);
        widgetEl.style.transform = `translate(${x}px, ${y}px)`;
    }

    onResizeEnd(event) {
        const widgetEl = event.target;
        const widgetId = widgetEl.dataset.widgetId;

        if (!widgetId) return;

        widgetEl.classList.remove('resizing');

        // Größe speichern
        const width = event.rect.width;
        const height = event.rect.height;

        this.saveWidgetPosition(widgetId, null, null, width, height);
        console.log(`[DragDrop] Resize ended: ${widgetId} (${width}x${height})`);
    }

    onWidgetTap(event) {
        const widgetEl = event.target;
        const widgetId = widgetEl.dataset.widgetId;

        if (!widgetId) return;

        // Toggle Resize-Handles
        this.toggleResizeHandles(widgetEl);

        console.log(`[DragDrop] Widget tapped: ${widgetId}`);
    }

    toggleResizeHandles(widgetEl) {
        const existingHandles = widgetEl.querySelectorAll('.resize-handle');
        
        if (existingHandles.length > 0) {
            // Handles entfernen
            existingHandles.forEach(handle => handle.remove());
        } else {
            // Handles hinzufügen
            if (this.options.allowResize) {
                const positions = ['nw', 'n', 'ne', 'e', 'se', 's', 'sw', 'w'];
                positions.forEach(pos => {
                    const handle = document.createElement('div');
                    handle.className = `resize-handle ${pos}`;
                    widgetEl.appendChild(handle);
                });
            }
        }
    }

    showPositionIndicator(widgetEl, x, y) {
        let indicator = widgetEl.querySelector('.position-indicator');
        
        if (!indicator) {
            indicator = document.createElement('div');
            indicator.className = 'position-indicator';
            widgetEl.appendChild(indicator);
        }

        indicator.textContent = `X: ${Math.round(x)}, Y: ${Math.round(y)}`;
    }

    hidePositionIndicator(widgetEl) {
        const indicator = widgetEl.querySelector('.position-indicator');
        if (indicator) {
            indicator.remove();
        }
    }

    showSnapLines(widgetEl, x, y) {
        this.hideSnapLines();

        const container = widgetEl.parentElement;
        if (!container) return;

        // Horizontale Snap-Line
        const hLine = document.createElement('div');
        hLine.className = 'snap-line horizontal';
        hLine.style.top = `${y}px`;
        container.appendChild(hLine);

        // Vertikale Snap-Line
        const vLine = document.createElement('div');
        vLine.className = 'snap-line vertical';
        vLine.style.left = `${x}px`;
        container.appendChild(vLine);
    }

    hideSnapLines() {
        const lines = document.querySelectorAll('.snap-line');
        lines.forEach(line => line.remove());
    }

    addToUndoStack(widgetId) {
        const widgetEl = document.querySelector(`[data-widget-id="${widgetId}"]`);
        if (!widgetEl) return;

        const state = {
            widgetId,
            x: parseFloat(widgetEl.dataset.x || 0),
            y: parseFloat(widgetEl.dataset.y || 0),
            width: widgetEl.offsetWidth,
            height: widgetEl.offsetHeight,
            timestamp: Date.now()
        };

        this.undoStack.push(state);
        this.redoStack = []; // Redo-Stack leeren bei neuer Aktion

        // Stack auf max. 50 Einträge begrenzen
        if (this.undoStack.length > 50) {
            this.undoStack.shift();
        }

        console.log(`[DragDrop] Added to undo stack: ${widgetId} (stack size: ${this.undoStack.length})`);
    }

    async undo() {
        if (this.undoStack.length === 0) {
            console.log('[DragDrop] Nothing to undo');
            return false;
        }

        const state = this.undoStack.pop();
        const widgetEl = document.querySelector(`[data-widget-id="${state.widgetId}"]`);

        if (!widgetEl) return false;

        // Aktuelle Position zum Redo-Stack hinzufügen
        this.redoStack.push({
            widgetId: state.widgetId,
            x: parseFloat(widgetEl.dataset.x || 0),
            y: parseFloat(widgetEl.dataset.y || 0),
            width: widgetEl.offsetWidth,
            height: widgetEl.offsetHeight,
            timestamp: Date.now()
        });

        // Position wiederherstellen
        widgetEl.style.transform = `translate(${state.x}px, ${state.y}px)`;
        widgetEl.dataset.x = state.x;
        widgetEl.dataset.y = state.y;

        if (state.width && state.height) {
            widgetEl.style.width = `${state.width}px`;
            widgetEl.style.height = `${state.height}px`;
        }

        // Backend benachrichtigen
        await this.saveWidgetPosition(state.widgetId, state.x, state.y, state.width, state.height);

        console.log(`[DragDrop] Undo: ${state.widgetId}`);
        return true;
    }

    async redo() {
        if (this.redoStack.length === 0) {
            console.log('[DragDrop] Nothing to redo');
            return false;
        }

        const state = this.redoStack.pop();
        const widgetEl = document.querySelector(`[data-widget-id="${state.widgetId}"]`);

        if (!widgetEl) return false;

        // Aktuelle Position zum Undo-Stack hinzufügen
        this.undoStack.push({
            widgetId: state.widgetId,
            x: parseFloat(widgetEl.dataset.x || 0),
            y: parseFloat(widgetEl.dataset.y || 0),
            width: widgetEl.offsetWidth,
            height: widgetEl.offsetHeight,
            timestamp: Date.now()
        });

        // Position wiederherstellen
        widgetEl.style.transform = `translate(${state.x}px, ${state.y}px)`;
        widgetEl.dataset.x = state.x;
        widgetEl.dataset.y = state.y;

        if (state.width && state.height) {
            widgetEl.style.width = `${state.width}px`;
            widgetEl.style.height = `${state.height}px`;
        }

        // Backend benachrichtigen
        await this.saveWidgetPosition(state.widgetId, state.x, state.y, state.width, state.height);

        console.log(`[DragDrop] Redo: ${state.widgetId}`);
        return true;
    }

    setupKeyboardShortcuts() {
        document.addEventListener('keydown', (event) => {
            // Strg/Cmd + Z für Undo
            if ((event.ctrlKey || event.metaKey) && event.key === 'z' && !event.shiftKey) {
                event.preventDefault();
                this.undo();
            }

            // Strg/Cmd + Shift + Z oder Strg/Cmd + Y für Redo
            if ((event.ctrlKey || event.metaKey) && (event.key === 'y' || (event.key === 'z' && event.shiftKey))) {
                event.preventDefault();
                this.redo();
            }

            // Escape für Drag-Abbruch
            if (event.key === 'Escape' && this.dragState.activeWidget) {
                event.preventDefault();
                this.cancelDrag();
            }
        });
    }

    async cancelDrag() {
        if (!this.dragState.activeWidget) return;

        const widgetEl = document.querySelector(`[data-widget-id="${this.dragState.activeWidget}"]`);
        if (!widgetEl) return;

        // Zurück zur ursprünglichen Position
        widgetEl.style.transform = `translate(${this.dragState.initialX}px, ${this.dragState.initialY}px)`;
        widgetEl.dataset.x = this.dragState.initialX;
        widgetEl.dataset.y = this.dragState.initialY;

        // Visuelles Feedback entfernen
        widgetEl.classList.remove('dragging');
        this.hidePositionIndicator(widgetEl);
        this.hideSnapLines();

        // Undo-Stack zurücksetzen (letzte Eintrag entfernen)
        this.undoStack.pop();

        console.log(`[DragDrop] Drag cancelled: ${this.dragState.activeWidget}`);

        this.dragState = {
            activeWidget: null,
            startX: 0,
            startY: 0,
            initialX: 0,
            initialY: 0
        };
    }

    setupTouchGestures() {
        // Touch-Optimierungen für Mobile
        let touchStartX = 0;
        let touchStartY = 0;
        let touchStartTime = 0;

        document.addEventListener('touchstart', (event) => {
            if (event.target.closest('.widget-container')) {
                touchStartX = event.touches[0].clientX;
                touchStartY = event.touches[0].clientY;
                touchStartTime = Date.now();
            }
        }, { passive: true });

        document.addEventListener('touchend', (event) => {
            if (!event.target.closest('.widget-container')) return;

            const touchEndX = event.changedTouches[0].clientX;
            const touchEndY = event.changedTouches[0].clientY;
            const duration = Date.now() - touchStartTime;

            const deltaX = touchEndX - touchStartX;
            const deltaY = touchEndY - touchStartY;

            // Swipe erkennen (mehr als 50px, weniger als 300ms)
            if (Math.abs(deltaX) > 50 || Math.abs(deltaY) > 50) {
                if (duration < 300) {
                    // Swipe-Geste erkannt
                    this.handleSwipe(event.target.closest('.widget-container'), deltaX, deltaY);
                }
            }
        }, { passive: true });
    }

    handleSwipe(widgetEl, deltaX, deltaY) {
        const widgetId = widgetEl.dataset.widgetId;
        if (!widgetId) return;

        // Swipe-Richtung bestimmen
        const direction = Math.abs(deltaX) > Math.abs(deltaY)
            ? (deltaX > 0 ? 'right' : 'left')
            : (deltaY > 0 ? 'down' : 'up');

        console.log(`[DragDrop] Swipe detected: ${direction}`);

        // Swipe-Aktion (kann angepasst werden)
        // Z.B.: Widget zur nächsten Zone verschieben
        this.showSwipeHint(widgetEl, direction);
    }

    showSwipeHint(widgetEl, direction) {
        const hint = document.createElement('div');
        hint.className = 'swipe-hint visible';
        hint.textContent = `Swipe ${direction}`;
        widgetEl.appendChild(hint);

        setTimeout(() => hint.remove(), 2000);
    }

    async loadWidgetPositions() {
        try {
            const response = await fetch(`${this.options.apiBaseUrl}/positions`);
            if (!response.ok) throw new Error('Failed to load positions');

            const data = await response.json();
            console.log(`[DragDrop] Loaded ${data.total} widget positions`);

            // Positionen auf Widgets anwenden
            Object.values(data.positions).forEach(pos => {
                const widgetEl = document.querySelector(`[data-widget-id="${pos.widget_id}"]`);
                if (widgetEl) {
                    widgetEl.style.transform = `translate(${pos.x}px, ${pos.y}px)`;
                    widgetEl.dataset.x = pos.x;
                    widgetEl.dataset.y = pos.y;

                    if (pos.width && pos.height) {
                        widgetEl.style.width = `${pos.width}px`;
                        widgetEl.style.height = `${pos.height}px`;
                    }
                }
            });
        } catch (error) {
            console.error('[DragDrop] Error loading positions:', error);
        }
    }

    async saveWidgetPosition(widgetId, x, y, width, height) {
        try {
            const payload = {
                widget_id: widgetId,
                x: Math.round(x),
                y: Math.round(y)
            };

            if (width) payload.width = Math.round(width);
            if (height) payload.height = Math.round(height);
            if (this.options.snapToGrid) payload.snap_to_grid = true;

            const response = await fetch(`${this.options.apiBaseUrl}/positions`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            if (!response.ok) throw new Error('Failed to save position');

            const data = await response.json();
            console.log(`[DragDrop] Saved position: ${widgetId} at (${data.position.x}, ${data.position.y})`);

            return data;
        } catch (error) {
            console.error('[DragDrop] Error saving position:', error);
            return null;
        }
    }

    setupWebSocket() {
        // WebSocket für Echtzeit-Updates (falls Socket.IO verfügbar)
        if (window.io) {
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${protocol}//${window.location.host}`;

            this.socket = io(wsUrl, {
                transports: ['websocket', 'polling']
            });

            this.socket.on('connect', () => {
                console.log('[DragDrop] WebSocket connected');
            });

            this.socket.on('widget_position_update', (data) => {
                console.log('[DragDrop] Position update received:', data);
                // Widget-Position aktualisieren
                const widgetEl = document.querySelector(`[data-widget-id="${data.widget_id}"]`);
                if (widgetEl && data.position) {
                    widgetEl.style.transform = `translate(${data.position.x}px, ${data.position.y}px)`;
                    widgetEl.dataset.x = data.position.x;
                    widgetEl.dataset.y = data.position.y;
                }
            });

            this.socket.on('widget_position_deleted', (data) => {
                console.log('[DragDrop] Position deleted:', data);
                // Widget zurücksetzen
                const widgetEl = document.querySelector(`[data-widget-id="${data.widget_id}"]`);
                if (widgetEl) {
                    widgetEl.style.transform = 'translate(0px, 0px)';
                    widgetEl.dataset.x = 0;
                    widgetEl.dataset.y = 0;
                }
            });
        }
    }

    showGridIfEnabled() {
        if (this.options.showGrid) {
            const containers = document.querySelectorAll('.zone-grid, .main-content');
            containers.forEach(container => {
                container.classList.add('grid-container', 'snap-active');
                
                // Snap-Indicator hinzufügen
                const indicator = document.createElement('div');
                indicator.className = 'snap-indicator visible';
                indicator.textContent = `${this.options.gridSnap}px Grid`;
                container.appendChild(indicator);
            });
        }
    }

    // Öffentliche API-Methoden
    enableDrag(widgetSelector) {
        const widgets = document.querySelectorAll(widgetSelector);
        widgets.forEach(widget => {
            widget.classList.add('draggable');
            if (!widget.hasAttribute('data-widget-id')) {
                widget.setAttribute('data-widget-id', `widget_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`);
            }
        });
        console.log(`[DragDrop] Enabled drag for ${widgets.length} widgets`);
    }

    disableDrag(widgetSelector) {
        const widgets = document.querySelectorAll(widgetSelector);
        widgets.forEach(widget => {
            widget.classList.remove('draggable');
        });
        console.log(`[DragDrop] Disabled drag for ${widgets.length} widgets`);
    }

    resetPositions() {
        this.undoStack = [];
        this.redoStack = [];
        
        const widgets = document.querySelectorAll('.widget-container, .zone-card, .dashboard-widget');
        widgets.forEach(widget => {
            widget.style.transform = 'translate(0px, 0px)';
            widget.dataset.x = 0;
            widget.dataset.y = 0;
        });

        console.log('[DragDrop] All positions reset');
    }

    getWidgetPositions() {
        const positions = {};
        const widgets = document.querySelectorAll('.widget-container, .zone-card, .dashboard-widget');
        
        widgets.forEach(widget => {
            const widgetId = widget.dataset.widgetId;
            if (widgetId) {
                positions[widgetId] = {
                    x: parseFloat(widget.dataset.x || 0),
                    y: parseFloat(widget.dataset.y || 0),
                    width: widget.offsetWidth,
                    height: widget.offsetHeight
                };
            }
        });

        return positions;
    }
}

// Drag & Drop Manager initialisieren
let dragDropManager;
document.addEventListener('DOMContentLoaded', () => {
    dragDropManager = new DragDropManager({
        gridSnap: 20,
        snapToGrid: true,
        showGrid: false,
        allowResize: true,
        apiBaseUrl: '/api/v1/widgets'
    });
});

// Export für globalen Zugriff
window.dragDropManager = dragDropManager;
