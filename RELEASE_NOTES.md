# Release Notes v12.0.0 -- Phase 5 & 6 Complete

**Datum:** 2026-03-01
**Branch:** main
**Tag:** `v12.0.0`
**HA hassfest:** ✓ compliant

---

## Ueberblick

PilotSuite v12.0.0 ist ein **MAJOR Release**, das zwei grosse Entwicklungsphasen abschliesst:

- **Phase 5 -- Cross-Home Sharing**: 52+ neue API-Endpoints fuer Notifications, Entity Sharing und Federated Learning
- **Phase 6 -- Type Hints & Test Coverage**: Durchgaengige Typisierung, 2526 Tests mit 98% Pass-Rate

Dieses Release erweitert PilotSuite von einem einzelnen Smart-Home-Backend zu einer Plattform, die Haushalte sicher miteinander vernetzen kann -- ohne Kompromisse bei Privacy oder lokaler Kontrolle.

---

## Highlights

### 52+ neue API-Endpoints

| Modul | Endpoints | Beschreibung |
|-------|-----------|-------------|
| Notifications | 21 | Benachrichtigungen, Subscriptions, HA Integration |
| Sharing | 16 | Entity Registry, Sync, Discovery |
| Federated Learning | 15 | Rounds, Aggregation, Knowledge Transfer |

### 2526 Tests -- 98% Pass-Rate

- **2476 passed**, 20 failed, 30 skipped
- Flask v3.1.3, NumPy v2.4.2 voll integriert
- Alle Integrationstests aktiviert

### Security Fixes (P1)

- WebSocket Authentication fuer `handle_connect()`
- Neuron State Override Protection mit Admin-Token
- Neuer `require_admin` Decorator in `api/security.py`

---

## Phase 5: Cross-Home Sharing

### Notifications API (`/api/v1/notifications`)

Ein vollstaendiges Benachrichtigungssystem mit 21 Endpoints:

**Core Notifications**
- `POST /send` -- Benachrichtigung senden
- `GET /` -- Benachrichtigungen auflisten (Filter: unread_only, type, limit)
- `POST /<id>/read` -- Als gelesen markieren
- `DELETE /<id>` -- Benachrichtigung verwerfen
- `POST /clear` -- Alle Benachrichtigungen loeschen

**Device Subscriptions**
- `POST /subscribe` -- Geraet registrieren (Push-Token, Preferences)
- `POST /unsubscribe` -- Geraet abmelden
- `GET /subscriptions` -- Alle Subscriptions anzeigen
- `PUT /subscriptions/<device_id>` -- Subscription aktualisieren

**Home Assistant Integration**
- `POST /ha/register` -- HA-Geraet registrieren
- `GET /ha/devices` -- HA-Geraete auflisten
- `DELETE /ha/devices/<id>` -- HA-Geraet abmelden
- `POST /ha/devices/<id>/enable` -- Geraet aktivieren
- `POST /ha/devices/<id>/disable` -- Geraet deaktivieren
- `POST /send/ha` -- Ueber HA Notify Service senden
- `GET /ha/test` -- HA-Verbindung testen
- `GET /ha/services` -- Verfuegbare HA Notify Services

**Analytics**
- `GET /stats` -- Statistiken (nach Quelle, Prioritaet, Typ)
- `GET /pending` -- Ausstehende Benachrichtigungen
- `GET /digest` -- Zusammenfassung (konfigurierbar: Stunden)

### Sharing API (`/api/v1/sharing`)

Cross-Home Entity Sharing mit 16 Endpoints:

**Entity Registry**
- `GET /entities` -- Alle Entities
- `GET /entities/shared` -- Geteilte Entities
- `GET /entities/<id>` -- Einzelne Entity
- `POST /entities` -- Entity registrieren
- `PUT /entities/<id>` -- Entity aktualisieren
- `DELETE /entities/<id>` -- Entity abmelden

**Sharing Workflow**
- `POST /entities/<id>/share-with` -- Mit anderem Haushalt teilen
- `POST /entities/<id>/stop-sharing/<home_id>` -- Teilen beenden
- `GET /entities/<id>/shared-with` -- Geteilte Haushalte anzeigen

**Sync & Discovery**
- `GET /sync/status` -- Sync-Status
- `GET /sync/entities` -- Synchronisierte Entities
- `GET /sync/entities/<id>` -- Einzelne synchronisierte Entity
- `GET /sync/peers` -- Sync-Peers
- `GET /discovery/peers` -- Entdeckte Peers
- `GET /discovery/local` -- Lokale Peer-Information
- `GET /` -- Gesamtstatus (Registry, Sync, Discovery)

### Collective Intelligence API (`/api/v1/federated`)

Federated Learning mit 15 Endpoints:

**Service Control**
- `GET /` -- Service-Status
- `POST /start` -- Service starten
- `POST /stop` -- Service stoppen

**Federated Learning Lifecycle**
- `POST /register` -- Node registrieren
- `POST /update` -- Update einreichen (Gewichte + Metriken)
- `POST /round` -- Neue Runde starten
- `POST /aggregate` -- Aggregation ausfuehren

**Knowledge Management**
- `POST /knowledge` -- Wissen extrahieren
- `POST /knowledge/<id>/transfer` -- Wissen transferieren
- `GET /knowledge-base` -- Wissensbasis anzeigen

**History & Models**
- `GET /rounds` -- Runden-Historie
- `GET /models` -- Aggregierte Modelle
- `GET /statistics` -- Statistiken

**State Persistence**
- `POST /save` -- Zustand speichern
- `POST /load` -- Zustand laden

---

## Phase 6: Type Hints & Test Coverage

### Type Hints

Alle Phase-5-Module haben jetzt durchgaengige Python Type Hints:

- `from __future__ import annotations` in allen Modulen
- Return Types: `Tuple[Response, int] | Response`
- Dataclass-Typisierung fuer alle Request/Response-Strukturen
- Einheitlicher Stil ueber Notifications, Sharing und Federated Learning

### Test-Ergebnisse

```
2526 Tests total
├── 2476 passed  (98.0%)
├── 20 failed    (0.8%)
└── 30 skipped   (1.2%)

Frameworks:
├── Flask v3.1.3
├── NumPy v2.4.2
└── pytest (alle Integration-Tests aktiviert)
```

---

## Security

### WebSocket Authentication
- Token-Validierung in `handle_connect()` fuer WebSocket-Verbindungen
- Unterstuetzt `auth.token`, Query-Parameter und Header
- Fehlende Tokens: Warning (Backward Compatibility)
- Ungueltige Tokens: Connection abgelehnt

### Neuron State Override Protection
- Admin-Token erforderlich fuer `/evaluate` mit State-Overrides
- Admin-Token erforderlich fuer `/update` Endpoint
- Neuer `require_admin_token()` in `api/security.py`

---

## Weitere Aenderungen

- **Zone Editor API**: CRUD-Operationen fuer Habitus-Zonen und Raeume
- **Neuron Dashboard**: D3.js Force-Directed Graph (14 Neuronen, 24 Verbindungen)
- **8 kritische Bugfixes** in Production-Readiness

---

## Upgrade-Hinweise

### Kompatibilitaet
- **Breaking Changes:** Keine -- bestehende APIs bleiben unveraendert
- **Neue Dependencies:** Keine zusaetzlichen Runtime-Dependencies
- **Konfiguration:** Neue Features sind opt-in und standardmaessig deaktiviert

### Migration
```bash
# Standard-Upgrade (Docker Pull)
ha addons update pilotsuite_core

# Manuell (fuer Entwickler)
git pull origin main
docker build -t pilotsuite-core .
```

### Bekannte Einschraenkungen
- 20 Tests schlagen fehl (Phase 7 adressiert dies)
- Federated Learning erfordert mindestens 2 Peers
- Cross-Home Sharing benoetigt lokales Netzwerk oder optionalen Rendezvous-Server

---

## Naechste Phase: Phase 7

- Production Readiness (Monitoring, Performance)
- Advanced ML (On-Device Inference, Anomaly Detection)
- Verbleibende Test-Fixes
- OpenAPI-Spec-Erweiterung

---

**PilotSuite v12.0.0** -- Local-first, Privacy-first, Governance-first.
