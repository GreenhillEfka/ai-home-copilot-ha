# API-Referenz: Phase 5 & 6 Endpoints

**Version:** 12.0.0  
**Datum:** 2026-03-01  
**Status:** ✅ Complete

Diese Referenz dokumentiert alle neuen API-Endpoints aus Phase 5 (Cross-Home Sharing) und Phase 6 (Type Hints & Test Coverage).

---

## Inhaltsverzeichnis

1. [Notifications API](#notifications-api) -- 21 Endpoints
2. [Sharing API](#sharing-api) -- 16 Endpoints
3. [Collective Intelligence API](#collective-intelligence-api) -- 15 Endpoints

---

## Notifications API

**Basis-Pfad:** `/api/v1/notifications`  
**Authentifizierung:** Bearer Token  
**Modul:** `copilot_core/api/v1/notifications.py`

### Core Endpoints

#### `POST /send`

Benachrichtigung senden.

**Request Body:**
```json
{
  "title": "Stimmung geändert",
  "message": "Von relax zu focus",
  "priority": "normal",
  "type": "mood_change",
  "action_data": {"mood": "focus"},
  "target_devices": ["device-123"],
  "tags": ["mood", "automation"]
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "notification_id": "uuid-123",
    "timestamp": "2026-03-01T17:00:00Z"
  }
}
```

---

#### `GET /`

Benachrichtigungen auflisten.

**Query Parameters:**
| Parameter | Typ | Default | Beschreibung |
|-----------|-----|---------|--------------|
| `unread_only` | boolean | false | Nur ungelesene |
| `type` | string | - | Filter nach Typ |
| `limit` | integer | 20 | Max. Ergebnisse (max 100) |

**Response:**
```json
{
  "success": true,
  "data": {
    "notifications": [...],
    "unread_count": 5,
    "total_count": 42
  }
}
```

---

#### `POST /<notification_id>/read`

Benachrichtigung als gelesen markieren.

**Response:**
```json
{
  "success": true,
  "data": {"notification_id": "uuid-123"}
}
```

---

#### `DELETE /<notification_id>`

Benachrichtigung verwerfen/dismissen.

**Response:**
```json
{
  "success": true,
  "data": {"notification_id": "uuid-123"}
}
```

---

#### `POST /clear`

Alle Benachrichtigungen löschen.

**Request Body (optional):**
```json
{"type": "alert"}
```

**Response:**
```json
{
  "success": true,
  "data": {"cleared_count": 15}
}
```

---

### Device Subscriptions

#### `POST /subscribe`

Device für Push-Benachrichtigungen registrieren.

**Request Body:**
```json
{
  "device_id": "device-123",
  "device_name": "Andreas iPhone",
  "device_type": "mobile",
  "push_token": "apns-token-xyz",
  "ha_entity_id": "notify.mobile_app_iphone",
  "preferences": {
    "notify_mood": true,
    "notify_alerts": true,
    "notify_suggestions": true,
    "notify_system": false
  }
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "sub-uuid",
    "device_id": "device-123",
    "device_name": "Andreas iPhone",
    "device_type": "mobile",
    "push_token": "apns-to...",
    "enabled": true,
    "preferences": {...},
    "ha_entity_id": "notify.mobile_app_iphone",
    "last_seen": "2026-03-01T17:00:00Z",
    "created_at": "2026-03-01T17:00:00Z"
  }
}
```

---

#### `POST /unsubscribe`

Device abmelden.

**Request Body:**
```json
{"device_id": "device-123"}
```

**Response:**
```json
{
  "success": true,
  "data": {"device_id": "device-123"}
}
```

---

#### `GET /subscriptions`

Alle Device-Subscriptions anzeigen.

**Response:**
```json
{
  "success": true,
  "data": {
    "subscriptions": [...],
    "count": 3
  }
}
```

---

#### `PUT /subscriptions/<device_id>`

Subscription-Einstellungen aktualisieren.

**Request Body:**
```json
{
  "enabled": true,
  "preferences": {
    "notify_mood": false,
    "notify_alerts": true
  }
}
```

---

### Home Assistant Integration

#### `POST /ha/register`

HA-Gerät für Benachrichtigungen registrieren.

---

#### `GET /ha/devices`

Alle registrierten HA-Geräte auflisten.

---

#### `DELETE /ha/devices/<id>`

HA-Gerät abmelden.

---

#### `POST /ha/devices/<id>/enable`

HA-Gerät aktivieren.

---

#### `POST /ha/devices/<id>/disable`

HA-Gerät deaktivieren.

---

#### `POST /send/ha`

Benachrichtigung über HA Notify Service senden.

---

#### `GET /ha/test`

HA-Verbindung testen.

**Response:**
```json
{
  "success": true,
  "data": {
    "connected": true,
    "service": "notify.mobile_app"
  }
}
```

---

#### `GET /ha/services`

Verfügbare HA Notify Services auflisten.

---

### Analytics

#### `GET /stats`

Statistiken nach Quelle, Priorität und Typ.

**Response:**
```json
{
  "success": true,
  "data": {
    "by_priority": {"low": 10, "normal": 50, "high": 5},
    "by_type": {"mood_change": 20, "alert": 10, "suggestion": 35},
    "by_source": {"mood_engine": 20, "automation": 45}
  }
}
```

---

#### `GET /pending`

Ausstehende Benachrichtigungen anzeigen.

---

#### `GET /digest`

Zusammenfassung der Benachrichtigungen.

**Query Parameters:**
| Parameter | Typ | Default | Beschreibung |
|-----------|-----|---------|--------------|
| `hours` | integer | 24 | Zeitraum in Stunden |

---

## Sharing API

**Basis-Pfad:** `/api/v1/sharing`  
**Authentifizierung:** API Key (`X-API-Key` Header)  
**Modul:** `copilot_core/sharing/api.py`

### Entity Registry

#### `GET /entities`

Alle registrierten Entities abrufen.

**Response:**
```json
{
  "count": 10,
  "entities": {
    "light.wohnzimmer": {...},
    "sensor.temperatur": {...}
  }
}
```

---

#### `GET /entities/shared`

Nur geteilte Entities (gefiltert).

---

#### `GET /entities/<entity_id>`

Einzelne Entity abrufen.

**Response:**
```json
{
  "entity_id": "light.wohnzimmer",
  "shared": true,
  "home_id": "home-123",
  "metadata": {...},
  "shared_with": ["home-456"]
}
```

---

#### `POST /entities`

Entity für Sharing registrieren.

**Request Body:**
```json
{
  "entity_id": "light.wohnzimmer",
  "shared": true,
  "home_id": "home-123",
  "metadata": {
    "name": "Wohnzimmer Licht",
    "domain": "light"
  }
}
```

**Response:**
```json
{
  "ok": true,
  "entity": {...}
}
```

---

#### `PUT /entities/<entity_id>`

Entity-Konfiguration aktualisieren.

**Request Body:**
```json
{
  "shared": false,
  "metadata": {"name": "Neuer Name"}
}
```

---

#### `DELETE /entities/<entity_id>`

Entity aus Sharing entfernen.

**Response:**
```json
{
  "ok": true,
  "entity_id": "light.wohnzimmer"
}
```

---

### Sharing Workflow

#### `POST /entities/<entity_id>/share-with`

Entity mit anderem Haushalt teilen.

**Request Body:**
```json
{"home_id": "home-456"}
```

**Response:**
```json
{
  "ok": true,
  "entity_id": "light.wohnzimmer",
  "home_id": "home-456"
}
```

---

#### `POST /entities/<entity_id>/stop-sharing/<home_id>`

Teilen mit spezifischem Haushalt beenden.

**Response:**
```json
{
  "ok": true,
  "entity_id": "light.wohnzimmer",
  "home_id": "home-456"
}
```

---

#### `GET /entities/<entity_id>/shared-with`

Liste der Haushalte anzeigen, mit denen geteilt wird.

**Response:**
```json
{
  "entity_id": "light.wohnzimmer",
  "shared_with": ["home-456", "home-789"],
  "count": 2
}
```

---

### Sync & Discovery

#### `GET /sync/status`

Sync-Service Status abrufen.

**Response:**
```json
{
  "active": true,
  "peer_id": "peer-123",
  "connected_peers": 2,
  "synchronized_peers": ["peer-456", "peer-789"],
  "entity_count": 15
}
```

---

#### `GET /sync/entities`

Alle synchronisierten Entities.

---

#### `GET /sync/entities/<entity_id>`

Einzelne synchronisierte Entity.

---

#### `GET /sync/peers`

Liste der synchronisierten Peers.

**Response:**
```json
{
  "synchronized_peers": ["peer-456", "peer-789"],
  "count": 2
}
```

---

#### `GET /discovery/peers`

Entdeckte CoPilot Peers im lokalen Netzwerk.

**Response:**
```json
{
  "count": 3,
  "peers": [
    {"peer_id": "peer-456", "host": "192.168.1.50", "port": 8909},
    {"peer_id": "peer-789", "host": "192.168.1.51", "port": 8909}
  ]
}
```

---

#### `GET /discovery/local`

Lokale Peer-Information (Selbstdarstellung).

**Response:**
```json
{
  "peer_id": "peer-123",
  "host": "192.168.1.100",
  "port": 8909,
  "home_id": "home-123",
  "version": "12.0.0"
}
```

---

#### `GET /`

Gesamtstatus des Sharing-Systems.

**Response:**
```json
{
  "registry": {
    "initialized": true,
    "entity_count": 10,
    "shared_count": 5
  },
  "sync": {
    "initialized": true,
    "active": true,
    "peer_count": 2
  },
  "discovery": {
    "initialized": true,
    "peer_count": 3
  }
}
```

---

## Collective Intelligence API

**Basis-Pfad:** `/api/v1/federated`  
**Authentifizierung:** API Key (`X-API-Key` Header)  
**Modul:** `copilot_core/collective_intelligence/api.py`

### Service Control

#### `GET /`

Federated Learning Service-Status.

**Response:**
```json
{
  "active": true,
  "node_id": "node-123",
  "round_id": "round-456",
  "participants": 5,
  "privacy_loss": 0.5,
  "model_version": "v1.2.0"
}
```

---

#### `POST /start`

Federated Learning Service starten.

**Response:**
```json
{
  "ok": true,
  "message": "Federated service started"
}
```

---

#### `POST /stop`

Federated Learning Service stoppen.

**Response:**
```json
{
  "ok": true,
  "message": "Federated service stopped"
}
```

---

### Federated Learning Lifecycle

#### `POST /register`

Home Node für Federated Learning registrieren.

**Request Body:**
```json
{
  "node_id": "node-123",
  "max_epsilon": 1.0
}
```

**Response:**
```json
{
  "ok": true,
  "node_id": "node-123",
  "message": "Node registered"
}
```

---

#### `POST /update`

Lokales Model-Update einreichen.

**Request Body:**
```json
{
  "node_id": "node-123",
  "weights": {"layer1": [...], "layer2": [...]},
  "metrics": {"accuracy": 0.95, "loss": 0.05}
}
```

**Response:**
```json
{
  "ok": true,
  "update_id": "update-789",
  "timestamp": "2026-03-01T17:00:00Z"
}
```

---

#### `POST /round`

Neue Federated Learning Runde starten.

**Response:**
```json
{
  "ok": true,
  "round_id": "round-456"
}
```

---

#### `POST /aggregate`

Aggregation für eine Runde ausführen.

**Request Body:**
```json
{"round_id": "round-456"}
```

**Response:**
```json
{
  "ok": true,
  "model_version": "v1.2.0",
  "participants": 5,
  "metrics": {"accuracy": 0.96},
  "privacy_loss": 0.5
}
```

---

### Knowledge Management

#### `POST /knowledge`

Wissen von einem Node extrahieren.

**Request Body:**
```json
{
  "node_id": "node-123",
  "knowledge_type": "automation_pattern",
  "payload": {"pattern": "light_on_at_sunset"},
  "confidence": 0.9
}
```

**Response:**
```json
{
  "ok": true,
  "knowledge_id": "know-abc",
  "knowledge_hash": "sha256-xyz"
}
```

---

#### `POST /knowledge/<knowledge_id>/transfer`

Wissen zu anderem Node transferieren.

**Request Body:**
```json
{"target_node_id": "node-456"}
```

**Response:**
```json
{
  "ok": true,
  "knowledge_id": "know-abc",
  "target_node_id": "node-456"
}
```

---

#### `GET /knowledge-base`

Gesamte Wissensbasis anzeigen.

**Response:**
```json
{
  "count": 50,
  "items": {
    "know-abc": {
      "knowledge_id": "know-abc",
      "knowledge_type": "automation_pattern",
      "payload": {...},
      "confidence": 0.9,
      "source_node": "node-123"
    }
  }
}
```

---

### History & Models

#### `GET /rounds`

Historie aller Federated Learning Runden.

**Response:**
```json
{
  "count": 10,
  "rounds": [
    {
      "round_id": "round-456",
      "timestamp": "2026-03-01T17:00:00Z",
      "participants": 5,
      "metrics": {...}
    }
  ]
}
```

---

#### `GET /models`

Alle aggregierten Modelle.

**Response:**
```json
{
  "count": 3,
  "models": {
    "v1.2.0": {
      "model_version": "v1.2.0",
      "created_at": "2026-03-01T17:00:00Z",
      "participants": 5,
      "metrics": {...}
    }
  }
}
```

---

#### `GET /statistics`

Umfassende Federated Learning Statistiken.

**Response:**
```json
{
  "total_rounds": 10,
  "total_updates": 50,
  "total_knowledge_items": 25,
  "active_nodes": 5,
  "average_privacy_loss": 0.45,
  "model_versions": ["v1.0.0", "v1.1.0", "v1.2.0"]
}
```

---

### State Persistence

#### `POST /save`

Systemzustand in Datei speichern.

**Request Body:**
```json
{"path": "/config/.copilot/federated_state.json"}
```

**Response:**
```json
{
  "ok": true,
  "path": "/config/.copilot/federated_state.json"
}
```

---

#### `POST /load`

Systemzustand aus Datei laden.

**Request Body:**
```json
{"path": "/config/.copilot/federated_state.json"}
```

**Response:**
```json
{
  "ok": true,
  "path": "/config/.copilot/federated_state.json"
}
```

---

## Authentication

### Bearer Token (Notifications API)

```
Authorization: Bearer <token>
```

### API Key (Sharing & Federated Learning)

```
X-API-Key: <api-key>
```

---

## Error Responses

### 400 Bad Request
```json
{
  "success": false,
  "error": "Missing required field: device_id"
}
```

### 401 Unauthorized
```json
{
  "success": false,
  "error": "Invalid or missing authentication token"
}
```

### 404 Not Found
```json
{
  "success": false,
  "error": "Notification not found"
}
```

### 500 Internal Server Error
```json
{
  "success": false,
  "error": "Failed to submit update"
}
```

### 503 Service Unavailable
```json
{
  "error": "Sharing registry not initialized"
}
```

---

## Rate Limiting

- **Notifications:** 100 requests/minute pro Device
- **Sharing:** 50 requests/minute pro Home
- **Federated Learning:** 10 requests/minute pro Node

---

## OpenAPI-Spezifikation

Die vollständige OpenAPI 3.0-Spezifikation ist verfügbar unter:
- `docs/openapi-phase5-6.yaml`

---

**PilotSuite v12.0.0** -- Phase 5 & 6 Complete ✅
