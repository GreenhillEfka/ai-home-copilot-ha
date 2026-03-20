# PS-108 Tasklog: Zone-Editor-API-Integration (HA Dashboard)

**Datum:** 2026-03-20  
**Agent:** PilotClaw (HA/UI-Spur)  
**Status:** ✅ Abgeschlossen (CRUD-Proxy), 🟡 UI-Integration ausstehend

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

### 2. Änderungen (Stand 2026-03-20)

#### A) `dashboard/api/v1/dashboard.py` — CRUD-Proxy-Endpunkte ✅

Proxy-Routen hinzugefügt (Forward to Core zone-editor API):

| HA-Dashboard-Endpoint | Core-zone-editor-API | Methode |
|---|---|---|
| `POST /api/v1/dashboard/zone-editor/zones` | `/api/v1/zone-editor/zones` | Create |
| `PUT /api/v1/dashboard/zone-editor/zones/<zone_id>` | `/api/v1/zone-editor/zones/<zone_id>` | Update |
| `DELETE /api/v1/dashboard/zone-editor/zones/<zone_id>` | `/api/v1/zone-editor/zones/<zone_id>` | Delete |
| `POST /api/v1/dashboard/zone-editor/zones/<zone_id>/rooms` | `/api/v1/zone-editor/zones/<zone_id>/rooms` | Add Room |
| `DELETE /api/v1/dashboard/zone-editor/zones/<zone_id>/rooms/<room_id>` | `/api/v1/zone-editor/zones/<zone_id>/rooms/<room_id>` | Remove Room |
| `GET /api/v1/dashboard/zone-editor/rooms` | `/api/v1/zone-editor/rooms` | List Rooms |
| `GET /api/v1/dashboard/zone-editor/templates` | `/api/v1/zone-editor/templates` | List Templates |

Jeweils Cache-Invalidierung (`_invalidate_cache()`) nach Mutation. Helper `_core_post()`, `_core_put()`, `_core_delete()` analog zu bestehendem `_core_get()`.

#### B) Core `zone_editor.ts` — Modernisierung ✅ (separate Core-Branch)

- **API-Default** auf `/api/v1/zone-editor/zones` gesetzt
- **Type-Safety**: `ZoneRoom`-Type hinzugefügt, `ZoneApiResponse` erweitert (`ok`, `zones`, `zone`, `rooms`)
- **Payload-Normalisierung**: `buildCreatePayload()`, `buildUpdatePayload()` mappen auf Core-Contract (`rooms` statt `entities`)
- **Room-basierte Entity-Zuordnung**: `loadAvailableEntities()` ruft `/api/v1/zone-editor/rooms` und filtert nach Zuordenbarkeit
- **URL-Param-Support**: `?zone_id=...` lädt initiale Zone beim Start
- **Tests aktualisiert**: TypeScript-Tests auf neuen API-Contract umgestellt

### 3. Nicht benötigt / Kein Eingriff

- **`styx-zone-creator-card.ts`**: Card-Definition unverändert (PS-199 ist schema-only)
- **`dashboard.js`**: WebSocket-Datenfluß für Live-Updates unverändert
- **`card-form-helper.ts`**: Basis unverändert (kein Core-Eingriff)
- **Core `zone_editor.py`**: Unverändert (API existiert bereits)

### 4. Verifikation

```bash
# HA Dashboard: Python compile check
python3 -m py_compile dashboard/api/v1/dashboard.py  # → OK

# Core: TypeScript strict check (in worktree)
tsc --noEmit --strict --target ES2020 \
    --moduleResolution node --skipLibCheck \
    static/zone/zone_editor.ts  # → no output (clean)
```

### 5. Git-Status

| Repo | Branch | Commit | Status |
|---|---|---|---|
| pilotsuite-styx-core | `feature/zone-editor-modern-crud` | `db2e3d45` | ✅ Gepusht |
| pilotsuite-styx-ha | `feature/habitus-zone-creator-card` | `263afbcc` | ✅ Gepusht |

---

## Nächste Schritte (Folgetasks)

1. **`styx-zone-creator-card.ts`**: Integration des `ZoneEditorApiClient` in den Card-Renderer, sodass Save/DELETE-Buttons im UI die API-Endpunkte aufrufen (Card-seitiger Eingriff, PS-199-Erweiterung)
2. **`dashboard.js`**: CRUD-Aktionen (Zone erstellen/löschen) in die Tab-Actions einbauen (Button-Handler → `zoneEditorApi.createZone()` / `deleteZone()`)
3. **Cache-Invalidierung**: Prüfen ob `dashboard/app.py` den SocketIO-Broadcast nach Zone-Mutation triggert (evtl. `socketio.emit('zone_update', ...)` nach Create/Update/Delete)
4. **PR-Merge**: Core-Branch und HA-Branch zusammenführen, End-to-End-Test im laufenden System

---

## Archiv

- Neuer File: `dashboard/static/utils/zone-editor-api-client.ts` (PS-108) — *bereits vorhanden*
- Geänderter File: `dashboard/api/v1/dashboard.py` (CRUD-Proxies) — ✅
- Core: `static/zone/zone_editor.ts` modernisiert — ✅
- Core: `tests/typescript/test_zone_editor.test.ts` aktualisiert — ✅
