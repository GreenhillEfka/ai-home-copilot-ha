# WebSocket Patterns Research Report

**Datum:** 2026-03-01  
**Ziel:** WebSocket-Integration für Neuronen-Dashboard (PilotSuite)  
**Fokus:** Real-time Updates, 10-15 FPS Throttling, Python Backend + JS Frontend

---

## 1. Socket.IO vs. Native WebSocket

### Native WebSocket

**Vorteile:**
- ✅ Leichtgewichtig, kein Overhead
- ✅ Standard-Protokoll (RFC 6455)
- ✅ Direkte Kontrolle über Binary/Data Frames
- ✅ Geringere Latenz (~1-2ms weniger als Socket.IO)
- ✅ Kein zusätzlicher Dependency

**Nachteile:**
- ❌ Kein automatisches Reconnection
- ❌ Kein Fallback auf Polling
- ❌ Room/Channel-Management manuell
- ❌ Heartbeat/Ping-Pong selbst implementieren

**Use Case:** Wenn volle Kontrolle benötigt wird und Infrastruktur stabil ist.

### Socket.IO

**Vorteile:**
- ✅ Automatisches Reconnection mit Backoff
- ✅ Fallback auf HTTP Long-Polling
- ✅ Built-in Room/Channel-System
- ✅ Auto-Heartbeat (ping/pong)
- ✅ Binary-Data Support
- ✅ Namespace-Isolation
- ✅ Broadcast-Room-Emit

**Nachteile:**
- ❌ Höherer Overhead (~2-3KB pro Paket)
- ❌ Proprietäres Protokoll (nicht direkt mit ws-Clients kompatibel)
- ❌ Slightly höhere Latenz

**Use Case:** Production-Apps mit instabilen Netzwerken, Mobile-Clients.

### Empfehlung für PilotSuite

**→ Socket.IO** wegen:
- Robuster bei Netzwerk-Problemen (HA-Integration)
- Einfacheres Room-Management pro Dashboard-Client
- Auto-Reconnection ohne Client-Code
- Broadcast an alle verbundenen Dashboards

---

## 2. Python: Flask-SocketIO vs. FastAPI WebSocket

### Flask-SocketIO

```python
from flask import Flask
from flask_socketio import SocketIO, emit

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

@socketio.on('connect')
def handle_connect():
    print('Client connected')

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

@socketio.on('join_room')
def handle_join(data):
    from flask_socketio import join_room
    join_room(data['room'])

# Broadcast an Room
socketio.emit('neuron_update', data, room='dashboard_1')

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000)
```

**Vorteile:**
- ✅ Einfache Integration in bestehende Flask-Apps
- ✅ Multiple Async-Modes (threading, eventlet, gevent)
- ✅ Mature, stabil seit Jahren
- ✅ Good Documentation

**Nachteile:**
- ❌ Flask ist synchron (außer mit Async-Extensions)
- ❌ Weniger performant bei vielen gleichzeitigen Connections
- ❌ Kein native async/await Support (in threading mode)

### FastAPI WebSocket

```python
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
import asyncio
import json

app = FastAPI()

class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []
        self.rooms: dict[str, list[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, room: str = None):
        await websocket.accept()
        self.active_connections.append(websocket)
        if room:
            if room not in self.rooms:
                self.rooms[room] = []
            self.rooms[room].append(websocket)

    def disconnect(self, websocket: WebSocket, room: str = None):
        self.active_connections.remove(websocket)
        if room and room in self.rooms:
            self.rooms[room].remove(websocket)

    async def broadcast_to_room(self, message: dict, room: str):
        if room in self.rooms:
            for connection in self.rooms[room]:
                await connection.send_json(message)

manager = ConnectionManager()

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str, room: str = "default"):
    await manager.connect(websocket, room)
    try:
        while True:
            data = await websocket.receive_text()
            # Echo oder verarbeiten
            await websocket.send_json({"status": "received", "data": data})
    except WebSocketDisconnect:
        manager.disconnect(websocket, room)
        await manager.broadcast_to_room(
            {"type": "client_left", "client_id": client_id},
            room
        )

# Broadcast von anywhere
@app.post("/broadcast/{room}")
async def broadcast(room: str, message: dict):
    await manager.broadcast_to_room(message, room)
    return {"status": "broadcasted"}
```

**Vorteile:**
- ✅ Native async/await (asyncio)
- ✅ Sehr performant (Starlette-basiert)
- ✅ Type Hints & Pydantic Validation
- ✅ Modern, aktiv entwickelt
- ✅ Einfache Integration mit FastAPI Endpoints

**Nachteile:**
- ❌ Kein automatisches Reconnection (muss im Client)
- ❌ Kein Fallback auf Polling
- ❌ Room-Management selbst bauen (oder Dependency wie `fastapi-websocket`)

### Empfehlung für PilotSuite

**→ FastAPI WebSocket** weil:
- PilotSuite ist bereits modern/async-fähig
- Bessere Performance bei vielen gleichzeitigen Dashboard-Clients
- Type Safety durch Pydantic
- Einfach zu testen
- Room-Management ist trivial selbst zu bauen

**ABER:** Wenn HA-Instanz bereits Flask nutzt → Flask-SocketIO für Konsistenz.

---

## 3. Frontend: JavaScript WebSocket Client

### Native WebSocket Client

```javascript
class WebSocketClient {
    constructor(url, options = {}) {
        this.url = url;
        this.reconnectInterval = options.reconnectInterval || 3000;
        this.maxReconnectAttempts = options.maxReconnectAttempts || 5;
        this.reconnectAttempts = 0;
        this.ws = null;
        this.messageHandlers = [];
        this.throttleFPS = options.throttleFPS || 15; // 10-15 FPS
        this.lastFrameTime = 0;
        this.frameInterval = 1000 / this.throttleFPS;
    }

    connect() {
        this.ws = new WebSocket(this.url);

        this.ws.onopen = () => {
            console.log('WebSocket connected');
            this.reconnectAttempts = 0;
        };

        this.ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            
            // Throttling für High-Frequency Updates
            const now = Date.now();
            if (now - this.lastFrameTime >= this.frameInterval) {
                this.messageHandlers.forEach(handler => handler(data));
                this.lastFrameTime = now;
            }
        };

        this.ws.onclose = () => {
            console.log('WebSocket closed');
            this.reconnect();
        };

        this.ws.onerror = (error) => {
            console.error('WebSocket error:', error);
        };
    }

    reconnect() {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            console.log(`Reconnecting... (${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
            setTimeout(() => this.connect(), this.reconnectInterval);
        } else {
            console.error('Max reconnect attempts reached');
        }
    }

    send(data) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify(data));
        }
    }

    onMessage(handler) {
        this.messageHandlers.push(handler);
    }

    disconnect() {
        if (this.ws) {
            this.ws.close();
        }
    }
}

// Usage
const ws = new WebSocketClient('ws://localhost:8000/ws/dashboard_1', {
    throttleFPS: 15,
    reconnectInterval: 3000
});

ws.connect();

ws.onMessage((data) => {
    // Update Dashboard UI
    updateNeuronVisualization(data);
});
```

### Socket.IO Client

```javascript
import { io } from 'socket.io-client';

class SocketIOClient {
    constructor(url, options = {}) {
        this.socket = io(url, {
            transports: ['websocket', 'polling'],
            reconnection: true,
            reconnectionDelay: 1000,
            reconnectionDelayMax: 5000,
            reconnectionAttempts: options.maxReconnectAttempts || 5,
            autoConnect: true
        });

        this.throttleFPS = options.throttleFPS || 15;
        this.lastFrameTime = 0;
        this.frameInterval = 1000 / this.throttleFPS;
        this.pendingData = null;
        this.throttleTimer = null;

        this.setupListeners();
    }

    setupListeners() {
        this.socket.on('connect', () => {
            console.log('Socket.IO connected');
        });

        this.socket.on('disconnect', () => {
            console.log('Socket.IO disconnected');
        });

        this.socket.on('neuron_update', (data) => {
            this.handleThrottledUpdate(data);
        });
    }

    handleThrottledUpdate(data) {
        const now = Date.now();
        
        // Immediate wenn genug Zeit vergangen
        if (now - this.lastFrameTime >= this.frameInterval) {
            this.processUpdate(data);
            this.lastFrameTime = now;
        } else {
            // Pending data für nächsten Frame
            this.pendingData = data;
            
            if (!this.throttleTimer) {
                const delay = this.frameInterval - (now - this.lastFrameTime);
                this.throttleTimer = setTimeout(() => {
                    if (this.pendingData) {
                        this.processUpdate(this.pendingData);
                        this.lastFrameTime = Date.now();
                        this.pendingData = null;
                    }
                    this.throttleTimer = null;
                }, delay);
            }
        }
    }

    processUpdate(data) {
        // Callbacks aufrufen
        this.updateCallbacks.forEach(cb => cb(data));
    }

    joinRoom(room) {
        this.socket.emit('join_room', { room });
    }

    leaveRoom(room) {
        this.socket.emit('leave_room', { room });
    }

    onUpdate(callback) {
        if (!this.updateCallbacks) {
            this.updateCallbacks = [];
        }
        this.updateCallbacks.push(callback);
    }

    disconnect() {
        this.socket.disconnect();
    }
}

// Usage
const socket = new SocketIOClient('http://localhost:5000', {
    throttleFPS: 15
});

socket.joinRoom('dashboard_1');

socket.onUpdate((data) => {
    updateNeuronVisualization(data);
});
```

---

## 4. Throttling Patterns (10-15 FPS)

### Pattern 1: Frame-Rate Limiting (Time-Based)

```python
import time
from functools import wraps

class Throttler:
    def __init__(self, fps=15):
        self.fps = fps
        self.interval = 1.0 / fps
        self.last_emit = 0
        self.pending_data = None

    def emit(self, data, send_func):
        now = time.time()
        elapsed = now - self.last_emit

        if elapsed >= self.interval:
            # Sofort senden
            send_func(self.pending_data or data)
            self.pending_data = None
            self.last_emit = now
        else:
            # Daten cachen für nächsten Frame
            self.pending_data = data
            delay = self.interval - elapsed
            # Timer für verzögertes Senden (asyncio.sleep oder threading.Timer)
            # Siehe Pattern 2

# Usage im Backend
throttler = Throttler(fps=15)

async def send_neuron_update(data):
    throttler.emit(data, lambda d: asyncio.create_task(
        manager.broadcast_to_room(d, 'dashboard_1')
    ))
```

### Pattern 2: Request Animation Frame (Frontend)

```javascript
class RAFThrottler {
    constructor(callback, fps = 15) {
        this.callback = callback;
        this.fps = fps;
        this.interval = 1000 / fps;
        this.lastTime = 0;
        this.pendingData = null;
        this.rafId = null;
    }

    queue(data) {
        this.pendingData = data;
        
        if (!this.rafId) {
            this.rafId = requestAnimationFrame((timestamp) => this.tick(timestamp));
        }
    }

    tick(timestamp) {
        if (timestamp - this.lastTime >= this.interval && this.pendingData) {
            this.callback(this.pendingData);
            this.lastTime = timestamp;
            this.pendingData = null;
        }

        if (this.pendingData) {
            this.rafId = requestAnimationFrame((ts) => this.tick(ts));
        } else {
            this.rafId = null;
        }
    }
}

// Usage
const throttler = new RAFThrottler((data) => {
    renderNeuronFrame(data);
}, 15);

// Bei jedem WebSocket-Event
socket.onMessage((data) => {
    throttler.queue(data);
});
```

### Pattern 3: asyncio Throttling (FastAPI)

```python
import asyncio
from collections import deque

class AsyncThrottler:
    def __init__(self, fps=15):
        self.fps = fps
        self.interval = 1.0 / fps
        self.last_emit = 0
        self.queue = deque()
        self.task = None
        self.running = False

    async def start(self, send_func):
        self.running = True
        self.send_func = send_func
        self.task = asyncio.create_task(self._run())

    async def _run(self):
        while self.running:
            if self.queue:
                data = self.queue.popleft()
                await self.send_func(data)
                self.last_emit = time.time()
            
            # Warte bis zum nächsten Frame
            elapsed = time.time() - self.last_emit
            sleep_time = max(0, self.interval - elapsed)
            await asyncio.sleep(sleep_time)

    def emit(self, data):
        # Nur neueste Daten behalten (Queue-Size = 1)
        self.queue.clear()
        self.queue.append(data)

    def stop(self):
        self.running = False
        if self.task:
            self.task.cancel()

# Usage im FastAPI Backend
throttler = AsyncThrottler(fps=15)

@app.on_event("startup")
async def startup_event():
    await throttler.start(lambda d: manager.broadcast_to_room(d, 'dashboard_1'))

@app.on_event("shutdown")
async def shutdown_event():
    throttler.stop()

# In der Neuron-Update-Loop
async def neuron_update_loop():
    while True:
        data = await get_neuron_data()
        throttler.emit(data)
        await asyncio.sleep(0.01)  # High-frequency sampling
```

---

## 5. Komplettes Beispiel: FastAPI + WebSocket + Throttling

### Backend (FastAPI)

```python
# app/websocket_server.py
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import time
import json
from typing import Dict, List
from dataclasses import dataclass

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@dataclass
class ClientConnection:
    websocket: WebSocket
    room: str
    last_heartbeat: float

class NeuronDashboardManager:
    def __init__(self):
        self.connections: Dict[str, ClientConnection] = {}
        self.rooms: Dict[str, List[str]] = {}
        self.throttle_fps = 15
        self.frame_interval = 1.0 / self.throttle_fps
        self.last_frame_time = 0
        self.pending_data = None
        self.neuron_data = {}

    async def connect(self, websocket: WebSocket, client_id: str, room: str):
        await websocket.accept()
        self.connections[client_id] = ClientConnection(
            websocket=websocket,
            room=room,
            last_heartbeat=time.time()
        )
        if room not in self.rooms:
            self.rooms[room] = []
        self.rooms[room].append(client_id)
        print(f"Client {client_id} joined room {room}")

    def disconnect(self, client_id: str):
        if client_id in self.connections:
            conn = self.connections[client_id]
            if conn.room in self.rooms:
                self.rooms[conn.room].remove(client_id)
            del self.connections[client_id]
            print(f"Client {client_id} disconnected")

    async def broadcast_to_room(self, room: str, data: dict):
        if room not in self.rooms:
            return
        
        # Throttling Logic
        now = time.time()
        self.pending_data = data

        if now - self.last_frame_time >= self.frame_interval:
            await self._send_pending_data()
            self.last_frame_time = now
        else:
            # Schedule delayed send
            delay = self.frame_interval - (now - self.last_frame_time)
            asyncio.create_task(self._delayed_send(delay))

    async def _send_pending_data(self):
        if not self.pending_data:
            return
        
        data = self.pending_data
        room_clients = self.rooms.get(data.get('room', 'default'), [])
        
        disconnected = []
        for client_id in room_clients:
            if client_id in self.connections:
                try:
                    await self.connections[client_id].websocket.send_json(data)
                except:
                    disconnected.append(client_id)
        
        # Cleanup disconnected
        for client_id in disconnected:
            self.disconnect(client_id)
        
        self.pending_data = None

    async def _delayed_send(self, delay: float):
        await asyncio.sleep(delay)
        if self.pending_data:
            await self._send_pending_data()
            self.last_frame_time = time.time()

    async def update_neuron_data(self, data: dict):
        """Called by neuron processing loop"""
        self.neuron_data = data
        await self.broadcast_to_room(data.get('room', 'default'), data)

manager = NeuronDashboardManager()

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str, room: str = "default"):
    await manager.connect(websocket, client_id, room)
    try:
        while True:
            # Heartbeat oder Commands vom Client
            data = await websocket.receive_text()
            # Optional: Command verarbeiten
            # await websocket.send_json({"status": "ack"})
    except WebSocketDisconnect:
        manager.disconnect(client_id)

# Simulierter Neuron-Data-Stream (ersetzen mit echter Logik)
@app.on_event("startup")
async def startup_event():
    asyncio.create_task(neuron_data_stream())

async def neuron_data_stream():
    """Simuliert High-Frequency Neuron Updates"""
    counter = 0
    while True:
        counter += 1
        data = {
            "type": "neuron_update",
            "room": "dashboard_1",
            "timestamp": time.time(),
            "neuron_id": counter % 100,
            "activation": round(np.random.random(), 4),
            "connections": [
                {"from": counter % 100, "to": (counter + 1) % 100, "weight": round(np.random.random(), 4)}
                for _ in range(5)
            ]
        }
        await manager.update_neuron_data(data)
        await asyncio.sleep(0.01)  # 100 Hz Sampling

if __name__ == "__main__":
    import uvicorn
    import numpy as np
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

### Frontend (JavaScript + Canvas Rendering)

```html
<!DOCTYPE html>
<html>
<head>
    <title>Neuron Dashboard</title>
    <style>
        body { margin: 0; background: #0a0a0a; color: #fff; font-family: monospace; }
        canvas { display: block; margin: 0 auto; }
        #stats { position: fixed; top: 10px; left: 10px; background: rgba(0,0,0,0.7); padding: 10px; }
    </style>
</head>
<body>
    <div id="stats">
        FPS: <span id="fps">0</span> | 
        Updates: <span id="updates">0</span> | 
        Neurons: <span id="neurons">0</span>
    </div>
    <canvas id="dashboard"></canvas>

    <script>
        class NeuronDashboard {
            constructor(canvasId) {
                this.canvas = document.getElementById(canvasId);
                this.ctx = this.canvas.getContext('2d');
                this.resize();
                
                this.neurons = new Map();
                this.connections = [];
                this.frameCount = 0;
                this.lastFpsTime = performance.now();
                this.updateCount = 0;

                this.throttleFPS = 15;
                this.frameInterval = 1000 / this.throttleFPS;
                this.lastFrameTime = 0;
                this.pendingData = null;

                this.setupWebSocket();
                this.renderLoop();
            }

            resize() {
                this.canvas.width = window.innerWidth;
                this.canvas.height = window.innerHeight;
            }

            setupWebSocket() {
                const wsUrl = `ws://${window.location.host}/ws/dashboard_client_1?room=dashboard_1`;
                this.ws = new WebSocket(wsUrl);

                this.ws.onopen = () => console.log('Connected to neuron stream');
                
                this.ws.onmessage = (event) => {
                    const data = JSON.parse(event.data);
                    this.queueFrame(data);
                };

                this.ws.onclose = () => {
                    console.log('Disconnected, reconnecting...');
                    setTimeout(() => this.setupWebSocket(), 3000);
                };
            }

            queueFrame(data) {
                const now = performance.now();
                this.pendingData = data;

                if (now - this.lastFrameTime >= this.frameInterval) {
                    this.processFrame();
                    this.lastFrameTime = now;
                } else {
                    // Throttle: warte auf nächsten Frame
                    const delay = this.frameInterval - (now - this.lastFrameTime);
                    setTimeout(() => this.processFrame(), delay);
                }
            }

            processFrame() {
                if (!this.pendingData) return;

                const data = this.pendingData;
                this.updateCount++;

                if (data.type === 'neuron_update') {
                    this.updateNeuron(data);
                }

                this.pendingData = null;
                this.updateStats();
            }

            updateNeuron(data) {
                const { neuron_id, activation, connections } = data;
                
                if (!this.neurons.has(neuron_id)) {
                    this.neurons.set(neuron_id, {
                        id: neuron_id,
                        x: Math.random() * this.canvas.width,
                        y: Math.random() * this.canvas.height,
                        activation: activation
                    });
                } else {
                    const neuron = this.neurons.get(neuron_id);
                    neuron.activation = activation;
                }

                this.connections = connections || [];
            }

            renderLoop() {
                this.frameCount++;
                
                // Clear
                this.ctx.fillStyle = 'rgba(10, 10, 10, 0.2)';
                this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);

                // Draw Connections
                this.ctx.strokeStyle = 'rgba(0, 255, 255, 0.3)';
                this.ctx.lineWidth = 1;
                this.connections.forEach(conn => {
                    const from = this.neurons.get(conn.from);
                    const to = this.neurons.get(conn.to);
                    if (from && to) {
                        this.ctx.beginPath();
                        this.ctx.moveTo(from.x, from.y);
                        this.ctx.lineTo(to.x, to.y);
                        this.ctx.stroke();
                    }
                });

                // Draw Neurons
                this.neurons.forEach(neuron => {
                    const radius = 5 + neuron.activation * 15;
                    const hue = 180 + neuron.activation * 60; // Cyan to Blue
                    
                    this.ctx.fillStyle = `hsl(${hue}, 100%, 50%)`;
                    this.ctx.beginPath();
                    this.ctx.arc(neuron.x, neuron.y, radius, 0, Math.PI * 2);
                    this.ctx.fill();
                    
                    // Glow
                    this.ctx.shadowBlur = 20;
                    this.ctx.shadowColor = `hsl(${hue}, 100%, 50%)`;
                    this.ctx.fill();
                    this.ctx.shadowBlur = 0;
                });

                requestAnimationFrame(() => this.renderLoop());
            }

            updateStats() {
                const now = performance.now();
                if (now - this.lastFpsTime >= 1000) {
                    document.getElementById('fps').textContent = this.frameCount;
                    document.getElementById('updates').textContent = this.updateCount;
                    document.getElementById('neurons').textContent = this.neurons.size;
                    
                    this.frameCount = 0;
                    this.updateCount = 0;
                    this.lastFpsTime = now;
                }
            }
        }

        // Start Dashboard
        const dashboard = new NeuronDashboard('dashboard');
        window.addEventListener('resize', () => dashboard.resize());
    </script>
</body>
</html>
```

---

## 6. Empfehlung für PilotSuite

### Architektur-Entscheidung

```
┌─────────────────────────────────────────────────────┐
│              PilotSuite Neuron Dashboard            │
├─────────────────────────────────────────────────────┤
│                                                     │
│  Backend: FastAPI + Native WebSocket                │
│  - Async/await für hohe Performance                 │
│  - Type Safety durch Pydantic                       │
│  - Einfache Integration in bestehende APIs          │
│                                                     │
│  Frontend: Vanilla JS + Canvas/WebGL                │
│  - Request Animation Frame für smooth Rendering     │
│  - Time-Based Throttling (15 FPS Ziel)              │
│  - Auto-Reconnection mit Backoff                    │
│                                                     │
│  Throttling Strategy:                               │
│  - Backend: AsyncThrottler (15 FPS Limit)           │
│  - Frontend: RAFThrottler (Frame-Sync)              │
│  - Fallback: Pending-Data Queue                     │
│                                                     │
└─────────────────────────────────────────────────────┘
```

### Konkrete Umsetzung

1. **WebSocket Endpoint:**
   - `/ws/{client_id}?room={room_name}`
   - Room-basierte Subscription pro Dashboard

2. **Throttling:**
   - Backend: 15 FPS Limit (66ms Interval)
   - Frontend: RAF-Sync für smooth Visuals
   - Pending-Data Queue für Latest-Value-Semantik

3. **Reconnection:**
   - Client: Exponential Backoff (1s, 2s, 4s, 8s, max 5 Attempts)
   - Server: Cleanup disconnected Clients nach 30s Timeout

4. **Monitoring:**
   - FPS-Counter im Frontend
   - Connection-Count im Backend
   - Alert bei >100 gleichzeitigen Clients

### Code-Struktur

```
pilotsuite-styx-core/
├── copilot_core/
│   └── rootfs/
│       └── usr/src/app/
│           ├── app/
│           │   ├── websocket_server.py    ← Neue WebSocket-Logik
│           │   ├── throttler.py           ← Throttling-Klassen
│           │   └── neuron_manager.py      ← Neuron Data Management
│           ├── templates/
│           │   └── neuron_dashboard.html  ← Frontend
│           └── static/
│               └── js/
│                   └── dashboard_client.js ← WS-Client + Rendering
```

### Nächste Schritte

1. **PoC erstellen:** Minimalbeispiel mit FastAPI + WebSocket
2. **Throttling testen:** 100 Hz Backend → 15 FPS Frontend
3. **Load-Testing:** 10+ gleichzeitige Dashboard-Clients
4. **Integration:** Einbinden in bestehende Neuron-Processing-Loop

---

**Fazit:** FastAPI + Native WebSocket bietet die beste Balance aus Performance, Kontrolle und Wartbarkeit für PilotSuite. Socket.IO nur wenn HA-Integration Fallback-Polling benötigt.

---

*Research Report erstellt am 2026-03-01 für PilotSuite Neuron Dashboard*
