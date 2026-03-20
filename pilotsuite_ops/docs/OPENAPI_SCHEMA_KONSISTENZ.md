# OpenAPI Schema Konsistenz — PilotSuite HA vs Core

**Task:** PS-057  
**Verglichen:**  
- HA: `team/repos/pilotsuite-styx-ha/docs/openapi.yaml` (v14.7.3)  
- Core: `team/repos/pilotsuite-styx-core/docs/openapi.yaml` (v13.9.0)

**Zusammenfassung:**

| Metrik | Wert |
|---|---|
| HA Endpunkte | 570 |
| Core Endpunkte | 571 |
| Gemeinsame Endpunkte | 570 |
| **Komplett identisch** | 479 (84%) |
| **Tatsächliche Unterschiede** | 91 (16%) |
| Auth-Mismatches | 18 |
| Stub-vs-Real-Schema (HA fehlt) | 39 |
| Beschreibung/Summary-Diff | 34 |
| Nur in Core vorhanden | 1 (`/api/v1/zones/assign`) |

---

## 1. Kritisch: Auth-Mismatches (18 Endpunkte)

> **Impact:** Falsche Auth-Mechanismen → 401/403 bei echten Requests

| Endpunkt | HA Auth | Core Auth | Risiko |
|---|---|---|---|
| `/api/v1/mood/aggregated` | **bearerAuth** | apiKeyAuth | ⚠️ HA-Client nutzt Bearer, Core erwartet API-Key |
| `/api/v1/notifications/digest` | apiKeyAuth | **bearerAuth** | ⚠️ HA nutzt API-Key, Core erwartet Bearer |
| `/api/v1/notifications/pending` | apiKeyAuth | **bearerAuth** | ⚠️ s.o. |
| `/api/v1/notifications/stats` | apiKeyAuth | **bearerAuth** | ⚠️ s.o. |
| `/api/v1/zone-automation/*` (14 Endpunkte) | apiKeyAuth | **bearerAuth** | ⚠️ Ganze Sub-Ressource betroffen |

**Details Zone-Automation:**

```
GET /api/v1/zone-automation/zones/{zone_id}
  HA:  security: [apiKeyAuth: []]
  Core: security: [bearerAuth: []]
```

Alle 14 Zone-Automation-Endpunkte sind betroffen:
- `zone-automation/dashboard`
- `zone-automation/entities/search`
- `zone-automation/import`
- `zone-automation/roles`
- `zone-automation/tags`
- `zone-automation/zones/{zone_id}`
- `zone-automation/zones/{zone_id}/brightness`
- `zone-automation/zones/{zone_id}/config`
- `zone-automation/zones/{zone_id}/entities`
- `zone-automation/zones/{zone_id}/entities/{entity_id}`
- `zone-automation/zones/{zone_id}/entities/{entity_id}/role`
- `zone-automation/zones/{zone_id}/entities/{entity_id}/tags`
- `zone-automation/zones/{zone_id}/override`
- `zone-automation/zones/{zone_id}/presence`

---

## 2. Stub-vs-Real-Schema: HA hat leere Schemas (39 Endpunkte)

> **Impact:** HA-Client hat keine Typinformation → kein TypeScript/Editor-Support, keine Validierung

Beispiel: `/api/v1/habitus/mine`

**HA (Stub):**
```yaml
post:
  summary: 'Habitus: Mine rules from provided Home Assistant events.'
  description: Auto-generated Habitus stub for `mine_rules`
  requestBody:
    required: true
    content:
      application/json:
        schema:
          type: object          # ← Keine Properties, keine Beschreibung
  responses:
    '200':
      description: Successful response
      content:
        application/json:
          schema:
            type: object         # ← Keine Response-Schema
```

**Core (Real):**
```yaml
post:
  summary: Trigger habitus pattern mining
  description: Initiates pattern mining to discover automation candidates...
  requestBody:
    required: false
    content:
      application/json:
        schema:
          type: object
          properties:
            lookback_hours:
              type: integer
              default: 72
              description: How far back to analyze
            force:
              type: boolean
              default: false
            zone:
              type: string
              description: Zone ID to filter patterns
  responses:
    '200':
      description: Mining triggered successfully
      content:
        application/json:
          schema:
            type: object
            properties:
              status:
                type: string
                example: started
              job_id:
                type: string
              estimated_duration:
                type: string
```

**Betroffene Endpunkte (39):**

| Endpunkt | Core hat Schema | HA hat Schema |
|---|---|---|
| `/api/v1/federated/knowledge` | ✅ Real | ❌ Stub |
| `/api/v1/federated/knowledge-base` | ✅ Real | ❌ Stub |
| `/api/v1/federated/knowledge/{knowledge_id}/transfer` | ✅ Real | ❌ Stub |
| `/api/v1/federated/load` | ✅ Real | ❌ Stub |
| `/api/v1/federated/models` | ✅ Real | ❌ Stub |
| `/api/v1/federated/save` | ✅ Real | ❌ Stub |
| `/api/v1/habitus/mine` | ✅ Real | ❌ Stub |
| `/api/v1/media/musikwolke/start` | ✅ Real | ❌ Stub |
| `/api/v1/media/musikwolke/{session_id}/update` | ✅ Real | ❌ Stub |
| `/api/v1/media/proactive/deliver` | ✅ Real | ❌ Stub |
| `/api/v1/media/proactive/dismiss` | ✅ Real | ❌ Stub |
| `/api/v1/media/proactive/reset-dismissals` | ✅ Real | ❌ Stub |
| `/api/v1/media/proactive/zone-entry` | ✅ Real | ❌ Stub |
| `/api/v1/media/zones` | ✅ Real | ❌ Stub |
| `/api/v1/media/zones/group` | ✅ Real | ❌ Stub |
| *(+24 weitere)* | | |

---

## 3. Beschreibung/Summary-Diffs (34 Endpunkte)

> **Impact:** Dokumentation inkonsistent, aber funktional kein Breaking Change

| Endpunkt | Art der Diff |
|---|---|
| `/api/v1/hub/integration/dispatch` | Summary/Description |
| `/api/v1/integration/bus/stats` | Summary/Description |
| `/api/v1/integration/feedback` | Summary/Description |
| `/api/v1/media/musikwolke` | Summary/Description |
| `/api/v1/media/musikwolke/{session_id}/stop` | Summary/Description |
| `/api/v1/media/zones/group-all` | Summary/Description |
| `/api/v1/media/zones/ungroup-all` | Summary/Description |
| `/api/v1/media/zones/{zone_id}` | Summary/Description |
| `/api/v1/media/zones/{zone_id}/favorites` | Summary/Description |
| `/api/v1/media/zones/{zone_id}/pause` | Summary/Description |
| *(+24 weitere)* | |

**Beispiel:** `/api/v1/notifications/digest`
- HA: `summary: 'Notifications-Extra: Get notification digest summary.'` + Auto-generated stub-Description
- Core: `summary: Get notification digest` + Custom Description

---

## 4. Core-exklusiver Endpunkt

| Endpunkt | Bemerkung |
|---|---|
| `/api/v1/zones/assign` | Nur in Core vorhanden, nicht in HA |

---

## 5. Tag-Namensinkonsistenzen

| HA Tag | Core Tag |
|---|---|
| `Knowledge Graph` | *(fehlt in Core)* |
| `Sonos` | *(fehlt in Core)* |
| `Neurons` | *(fehlt in Core)* |
| `Media` | `Media Zones` |
| `Multihome` | *(fehlt in Core)* |
| `Notifications-Extra` | `Notifications` |
| `Chat` | *(fehlt in Core)* |
| `Zone Automation` | *(identisch in beiden)* |

---

## 6. Server/Version-Inkonsistenz

| Feld | HA | Core |
|---|---|---|
| Spec Version | `14.7.3` | `13.9.0` |
| info.version | `14.7.3` | `13.9.0` |

→ HA Spec ist **neuer** als Core Spec.

---

## Fazit & Handlungsbedarf

### 🔴 Hohe Priorität (Breaking)

1. **Auth-Mismatches beheben** — 18 Endpunkte, insbesondere:
   - `/api/v1/mood/aggregated` (bearer↔apiKey)
   - 14× Zone-Automation (alle apiKey in HA, alle bearer in Core)
   - 3× Notifications-Extra (apiKey in HA, bearer in Core)

### 🟡 Mittlere Priorität

2. **39 Stub-Schemas in HA auflösen** — HA-Dokumentation unvollständig
   - Am kritischsten: `habitus/mine`, `federated/*`, `media/*`
   
3. **Core-only Endpunkt** `/api/v1/zones/assign` — Fehlt in HA, möglicherweise ein Drift-Problem

### 🟢 Niedrige Priorität

4. **34 Description-Diffs** — Dokumentationsreinigung, kein funktionaler Impact

5. **Tag-Namen vereinheitlichen** — `Notifications-Extra` vs `Notifications`, `Media` vs `Media Zones`

---

## Tasklog PS-057

```
Date:      2026-03-20
Duration:  ~25min
Agent:     pilotclaw-subagent (depth 1/1)
Method:    Grep/diff + Python-Analyse beider YAML-Files

Files analyzed:
  - /config/clawd/team/repos/pilotsuite-styx-ha/docs/openapi.yaml  (v14.7.3)
  - /config/clawd/team/repos/pilotsuite-styx-core/docs/openapi.yaml (v13.9.0)

Output:
  - /config/clawd/pilotsuite_ops/docs/OPENAPI_SCHEMA_KONSISTENZ.md

Findings:
  - 570 shared paths, 1 Core-only, 0 HA-only
  - 479 identical (84%)
  - 91 with real differences (16%)
    - 18 auth mismatches (CRITICAL)
    - 39 stub-vs-real schemas (MEDIUM)
    - 34 description/summary diffs (LOW)
```
