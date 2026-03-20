# PS-108 Tasklog: Zone-Editor-API-Integration (HA Dashboard)

**Datum:** 2026-03-20  
**Agent:** PilotClaw (HA/UI-Spur)  
**Status:** ✅ Abgeschlossen

---

## Was wurde getan

### 1. Bestandsaufnahme

- **`styx-zone-creator-card.ts`** (PS-199): Reine Schema-Karte — `static getConfigForm()` + `validateConfig()`, kein API-Traffic, kein Backend-Export. Card-Definitionen für Zone-Module (LIGHT, AUDIO, CLIMATE, COVER, ENERGY, SCENE, SECURITY).
- **`dashboard.js`** (HabitusDashboard): Lädt Zone-Daten per **WebSocket** (`socketio.emit('request_zone_data')`) und REST `PUT /zones/<zone_id>/data` für Alerts. **Keine Zone-CRUD-Operationen** (Create/Update/Delete) vorhanden.
- **`dashboard/api/v1/dashboard.py`**: Liest Zonen-Konfiguration via `_core_get('/api/v1/zone-editor/zones')` (GET, read-only). **Keine Create/Update/Delete-Proxies** vorhanden.
- **Core `zone_editor.py`** (styx-core): Exponiert am Core-Port (8909):
  - `POST   /api/v1/zone-editor/zones`
  - `PUT    /api/v1/zone-editor/zones/<zone_id>`
  - `DELETE /api/v1/zone-editor/zones/<zone_id>`
  - `GET    /api/v1/zone-editor/zones`

### 2. Änderungen

#### A) `dashboard/api/v1/dashboard.py` — CRUD-Proxy-Endpunkte

Proxy-Routen hinzugefügt (Forward to Core zone-editor API):

| HA-Dashboard-Endpoint | Core-zone-editor-API | Methode |
|---|---|---|
| `POST /api/v1/dashboard/zone-editor/zones` | `/api/v1/zone-editor/zones` | Create |
| `PUT /api/v1/dashboard/zone-editor/zones/<zone_id>` | `/api/v1/zone-editor/zones/<zone_id>` | Update |
| `DELETE /api/v1/dashboard/zone-editor/zones/<zone_id>` | `/api/v1/zone-editor/zones/<zone_id>` | Delete |

Jeweils Cache-Invalidierung (`_invalidate_cache()`) nach Mutation. Helper `_core_post()`, `_core_put()`, `_core_delete()` analog zu bestehendem `_core_get()`.

#### B) `dashboard/static/utils/zone-editor-api-client.ts` — NEU

TypeScript-API-Client (PS-108), nutzt `card-form-helper.ts` als Basis:

- **`ZoneEditorApiClient`** mit: `listZones()`, `getZone()`, `createZone()`, `updateZone()`, `deleteZone()`, `listRooms()`, `listTemplates()`
- **`resolveZoneEditorUrl()`**: Universelle URL-Auflösung (Dashboard-Proxy vs. Core-Direct)
- **`ZoneEditorApiError`**: Typsicheres Error-Handling
- **`cardConfigToCreatePayload()`** / **`cardConfigToUpdatePayload()`**: Mapper von StyxZoneCreatorCardConfig → API-Payload
- **Python `py_compile`**: ✅ Kompiliert sauber
- **TypeScript `tsc --strict`**: ✅ Keine Fehler

### 3. Nicht benötigt / Kein Eingriff

- **`styx-zone-creator-card.ts`**: Card-Definition unverändert (PS-199 ist schema-only)
- **`dashboard.js`**: WebSocket-Datenfluß für Live-Updates unverändert
- **`card-form-helper.ts`**: Basis unverändert (kein Core-Eingriff)
- **Core `zone_editor.py`**: Unverändert (API existiert bereits)

### 4. Verifikation

```bash
# Python compile check
python3 -m py_compile dashboard/api/v1/dashboard.py  # → OK

# TypeScript strict check
tsc --noEmit --strict --target ES2020 \
    --moduleResolution node --skipLibCheck \
    zone-editor-api-client.ts  # → no output (clean)
```

---

## Nächste Schritte (Folgetasks)

1. **`styx-zone-creator-card.ts`**: Integration des `ZoneEditorApiClient` in den Card-Renderer, sodass Save/DELETE-Buttons im UI die API-Endpunkte aufrufen (Card-seitiger Eingriff, PS-199-Erweiterung)
2. **`dashboard.js`**: CRUD-Aktionen (Zone erstellen/löschen) in die Tab-Actions einbauen (Button-Handler → `zoneEditorApi.createZone()` / `deleteZone()`)
3. **Cache-Invalidierung**: Prüfen ob `dashboard/app.py` den SocketIO-Broadcast nach Zone-Mutation triggert (evtl. `socketio.emit('zone_update', ...)` nach Create/Update/Delete)

---

## Archiv

- Neuer File: `dashboard/static/utils/zone-editor-api-client.ts` (PS-108)
- Geänderter File: `dashboard/api/v1/dashboard.py` (CRUD-Proxies)
