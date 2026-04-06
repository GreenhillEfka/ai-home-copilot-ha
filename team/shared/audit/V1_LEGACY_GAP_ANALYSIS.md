# V1 Legacy Gap Analysis – Alte API vs. PilotSuite v1.0.0 Styx Core

**Zeitstempel:** 2026-04-06T23:47+02:00  
**Scope:** Vergleich der Legacy-Dokumentation (vor 2026-04-01, Backup/Archive) gegen neue Styx-Core-API-Referenz.

## Datenbasis

- **Legacy-Doku:**
  `/config/clawd/archive/openclaw_import_2026-03-05_050408/inbox-openclaw/agents/styx/agent/pilotsuite-styx-core/docs/API_REFERENCE.md`
- **Legacy-Code (Abgleich):** dieselbe Archivkopie unter `copilot_core/rootfs/usr/src/app`
- **Neue Doku:**
  `/config/clawd/team/repos/pilotsuite-styx-core/copilot_core/docs/API_REFERENCE.md`
- **Neue Runtime-Routen (Code-Scan):**
  `/config/clawd/team/repos/pilotsuite-styx-core/copilot_core/rootfs/usr/src/app`

## Methodik

1. Endpunkte aus beiden API_REFERENCES per Regex aus Markdown-Überschriften `###.. #### METHOD /path` extrahiert.
2. Platzhalter normalisiert (`:id`, `<id>` → `{id}`).
3. Differenz `Legacy – Neuer Core` gebildet.
4. Zusätzlich geprüft, ob Legacy-Endpunkte noch im neuen Runtime-Code existieren, aber nicht mehr in der neuen API-Referenz dokumentiert sind.

## Ergebnisübersicht

- **Legacy-Endpoints (Dokumentation):** 107
- **Neue Styx-Core-API-Referenz:** 53
- **Fehlend in neuer API-Referenz:** **98**
- **davon 25 in neuer Runtime noch implementiert (nur nicht dokumentiert)**
- **davon 73 weder in neuer API-Doku noch in Runtime-Code sichtbar**

## Alte Endpunkte, die in neuer API nicht mehr sichtbar sind

### MIGRIERT (Funktion in anderem Endpoint bereits vorhanden)

- `GET /api/v1/candidates/:candidate_id` → ersetzt durch `GET /api/v1/candidates/{id}`
- `GET /api/v1/graph/patterns` → ersetzt durch `GET /api/v1/graph/state` bzw. `POST /api/v1/graph/query|/render`
- `GET /api/v1/graph/snapshot.svg` → ersetzt durch neue Graph-Surfaces
- `GET /api/v1/graph/stats` → ersetzt durch Graph-Graph-/State-Surface
- `GET /api/v1/habitus/config` → ersetzt durch Habitusrichtwerte in `/api/v1/habitus/stats` und `/api/v1/habitus/patterns`
- `GET /api/v1/habitus/rules` → ersetzt durch `/api/v1/habitus/patterns`
- `GET /api/v1/habitus/rules/summary` → ersetzt durch `/api/v1/habitus/patterns`
- `GET /api/v1/habitus/rules/:rule_key/explain` → ersetzt durch Regel-/Pattern-Explainer in neuer Habitus-Logik
- `GET /api/v1/habitus/status` → ersetzt durch `/api/v1/habitus/stats`
- `GET /api/v1/kg/edges` → ersetzt durch neue Graph-Query/State-Modelle
- `GET /api/v1/kg/entity/:entity_id/related` → ersetzt durch Graph-Query-State
- `GET /api/v1/kg/mood/:mood/patterns` → ersetzt durch Graph-Pipeline
- `GET /api/v1/kg/nodes` → ersetzt durch Graph-Query/State
- `GET /api/v1/kg/nodes/:node_id` → ersetzt durch Graph-Query/State
- `GET /api/v1/kg/pattern/:pattern_id` → ersetzt durch Graph-Query/State
- `GET /api/v1/kg/stats` → ersetzt durch Graph-Stats in neuer Graph-API
- `GET /api/v1/kg/zone/:zone_id/entities` → ersetzt durch Graph-Query/State
- `GET /api/v1/mood/state` → ersetzt durch `GET /api/v1/mood` bzw. `GET /api/v1/mood/{zone_id}`
- `GET /api/v1/mood/zones/:zone_name/status` → ersetzt durch neue Mood-Surface
- `GET /api/v1/mood/zones/status` → ersetzt durch neue Mood-Surface
- `GET /api/v1/neurons` → ersetzt durch neue Habituss/Mood-Layer
- `GET /api/v1/neurons/:neuron_id` → ersetzt durch neue Habituss/Mood-Layer
- `GET /api/v1/neurons/mood` → ersetzt durch neue Mood/Labs-Layer
- `GET /api/v1/neurons/mood/history` → ersetzt durch neue Mood-Auswertung
- `GET /api/v1/neurons/suggestions` → ersetzt durch neue Mood-Hints/Proposal-Surfaces
- `GET /health` → ersetzt durch `GET /api/v1/system_health`
- `GET /ready` → ersetzt durch `GET /api/v1/system_health`
- `GET /v1/models` → ersetzt durch `/chat/models/*`
- `GET /version` → ersetzt durch neue System-Health/Manifest-Quellen
- `POST /api/v1/habitus/config` → ersetzt durch zentrale Habitus-Config-Nutzung im neuen Core
- `POST /api/v1/habitus/reset` → ersetzt durch neue Habitus-Initialisierungslogik
- `POST /api/v1/kg/edges` → ersetzt durch Graph-Ingest/Query-API
- `POST /api/v1/kg/entities` → ersetzt durch Graph-Ingest/Query-API
- `POST /api/v1/kg/import/entities` → ersetzt durch Graph-Ingest/Query-API
- `POST /api/v1/kg/import/patterns` → ersetzt durch Graph-Ingest/Query-API
- `POST /api/v1/kg/moods` → ersetzt durch Graph/Habitus-Klassen
- `POST /api/v1/kg/nodes` → ersetzt durch Graph-Ingest/Query-API
- `POST /api/v1/kg/zones` → ersetzt durch Graph-Ingest/Query-API
- `POST /api/v1/kg/query` → ersetzt durch `POST /api/v1/graph/query`
- `POST /api/v1/mood/score` → ersetzt durch `/api/v1/mood/update-*`-Flows
- `POST /api/v1/mood/zones/:zone_name/orchestrate` → ersetzt durch `/api/v1/mood/update-*`
- `POST /api/v1/neurons/configure` → ersetzt durch neue Habitus/Mood-Konfig-Pfade
- `POST /api/v1/neurons/evaluate` → ersetzt durch neue Neurom-/Mood-Evaluations-Pfade
- `POST /api/v1/neurons/mood/evaluate` → ersetzt durch neue Mood-Evaluations-Pfade
- `POST /api/v1/neurons/update` → ersetzt durch neue Habituss/Mood-Update-Pfade

### VERALTET (durch neue LLM/RAG-Architektur ersetzt)

- `DELETE /api/v1/vector/vectors`
- `DELETE /api/v1/vector/vectors/:entry_id`
- `GET /api/v1/search/entities`
- `GET /api/v1/search/stats`
- `GET /api/v1/vector/similar/:entry_id`
- `GET /api/v1/vector/stats`
- `GET /api/v1/vector/vectors`
- `GET /api/v1/vector/vectors/:entry_id`
- `POST /api/v1/search/index`
- `POST /api/v1/vector/embeddings`
- `POST /api/v1/vector/embeddings/bulk`
- `POST /api/v1/vector/similarity`

### FEHLEND (nach aktuellem Stand kein klarer Ersatz in neuer Core-API)

- `DELETE /api/v1/candidates/:candidate_id`
- `DELETE /api/v1/notifications/:notification_id`
- `GET /api/v1/agent/status`
- `GET /api/v1/candidates/graph_candidates`
- `GET /api/v1/energy/baselines`
- `GET /api/v1/energy/explain/:suggestion_id`
- `GET /api/v1/energy/health`
- `GET /api/v1/energy/shifting`
- `GET /api/v1/energy/suppress`
- `GET /api/v1/events`
- `GET /api/v1/habitus/dashboard_cards`
- `GET /api/v1/habitus/dashboard_cards/health`
- `GET /api/v1/habitus/dashboard_cards/rules`
- `GET /api/v1/habitus/dashboard_cards/zone/:zone_id`
- `GET /api/v1/habitus/dashboard_cards/zones`
- `GET /api/v1/health/deep`
- `GET /api/v1/health/metrics`
- `GET /api/v1/notifications/subscriptions`
- `GET /api/v1/onyx/status`
- `GET /api/v1/search`
- `GET /api/v1/weather/`
- `GET /api/v1/weather/forecast`
- `GET /api/v1/weather/health`
- `GET /api/v1/weather/pv-recommendations`
- `GET /v1/models/:model_id`
- `POST /api/v1/agent/self-heal`
- `POST /api/v1/agent/verify`
- `POST /api/v1/dev/logs`
- `POST /api/v1/echo`
- `POST /api/v1/events`
- `POST /api/v1/graph/cache/clear`
- `POST /api/v1/graph/ops`
- `POST /api/v1/mood/zones/:zone_name/force_mood`
- `POST /api/v1/notifications/:notification_id/read`
- `POST /api/v1/notifications/clear`
- `POST /api/v1/notifications/send`
- `POST /api/v1/notifications/subscribe`
- `POST /api/v1/notifications/unsubscribe`
- `POST /api/v1/onyx/ha/service-call`
- `POST /v1/chat/completions`
- `PUT /api/v1/notifications/subscriptions/:device_id`

## Legacy-Endpunkte, die **im neuen Runtime-Code noch existieren, aber nicht in API-Referenz dokumentiert sind**

`25` Endpunkte (nicht öffentlich sichtbar in Doku):

- `GET /api/v1/agent/status`
- `GET /api/v1/candidates/graph_candidates`
- `GET /api/v1/energy/shifting`
- `GET /api/v1/events`
- `GET /api/v1/graph/patterns`
- `GET /api/v1/graph/snapshot.svg`
- `GET /api/v1/graph/stats`
- `GET /api/v1/health/deep`
- `GET /api/v1/health/metrics`
- `GET /api/v1/neurons`
- `GET /api/v1/neurons/mood`
- `GET /api/v1/onyx/status`
- `GET /health`
- `GET /ready`
- `GET /v1/models`
- `GET /version`
- `POST /api/v1/agent/self-heal`
- `POST /api/v1/agent/verify`
- `POST /api/v1/dev/logs`
- `POST /api/v1/echo`
- `POST /api/v1/events`
- `POST /api/v1/graph/cache/clear`
- `POST /api/v1/neurons/evaluate`
- `POST /api/v1/onyx/ha/service-call`
- `POST /v1/chat/completions`

## Endpunkte, die derzeit **weder in neuer API-Doku noch im Runtime-Code** sind (echte Lücken)

`73` Endpunkte fehlen:

- `DELETE /api/v1/candidates/:candidate_id`
- `DELETE /api/v1/notifications/:notification_id`
- `DELETE /api/v1/vector/vectors`
- `DELETE /api/v1/vector/vectors/:entry_id`
- `GET /api/v1/candidates/:candidate_id`
- `GET /api/v1/energy/baselines`
- `GET /api/v1/energy/explain/:suggestion_id`
- `GET /api/v1/energy/health`
- `GET /api/v1/energy/suppress`
- `GET /api/v1/habitus/config`
- `GET /api/v1/habitus/dashboard_cards`
- `GET /api/v1/habitus/dashboard_cards/health`
- `GET /api/v1/habitus/dashboard_cards/rules`
- `GET /api/v1/habitus/dashboard_cards/zone/:zone_id`
- `GET /api/v1/habitus/dashboard_cards/zones`
- `GET /api/v1/habitus/rules`
- `GET /api/v1/habitus/rules/summary`
- `GET /api/v1/habitus/rules/:rule_key/explain`
- `GET /api/v1/habitus/status`
- `GET /api/v1/kg/edges`
- `GET /api/v1/kg/entity/:entity_id/related`
- `GET /api/v1/kg/mood/:mood/patterns`
- `GET /api/v1/kg/nodes`
- `GET /api/v1/kg/nodes/:node_id`
- `GET /api/v1/kg/pattern/:pattern_id`
- `GET /api/v1/kg/stats`
- `GET /api/v1/kg/zone/:zone_id/entities`
- `GET /api/v1/mood/state`
- `GET /api/v1/mood/zones/status`
- `GET /api/v1/mood/zones/:zone_name/status`
- `GET /api/v1/neurons/mood/history`
- `GET /api/v1/neurons/suggestions`
- `GET /api/v1/neurons/:neuron_id`
- `GET /api/v1/notifications/subscriptions`
- `GET /api/v1/search`
- `GET /api/v1/search/entities`
- `GET /api/v1/search/stats`
- `GET /api/v1/vector/similar/:entry_id`
- `GET /api/v1/vector/stats`
- `GET /api/v1/vector/vectors`
- `GET /api/v1/vector/vectors/:entry_id`
- `GET /api/v1/weather/`
- `GET /api/v1/weather/forecast`
- `GET /api/v1/weather/health`
- `GET /api/v1/weather/pv-recommendations`
- `GET /v1/models/:model_id`
- `POST /api/v1/graph/ops`
- `POST /api/v1/habitus/config`
- `POST /api/v1/habitus/reset`
- `POST /api/v1/kg/edges`
- `POST /api/v1/kg/entities`
- `POST /api/v1/kg/import/entities`
- `POST /api/v1/kg/import/patterns`
- `POST /api/v1/kg/moods`
- `POST /api/v1/kg/nodes`
- `POST /api/v1/kg/query`
- `POST /api/v1/kg/zones`
- `POST /api/v1/mood/score`
- `POST /api/v1/mood/zones/:zone_name/force_mood`
- `POST /api/v1/mood/zones/:zone_name/orchestrate`
- `POST /api/v1/neurons/configure`
- `POST /api/v1/neurons/mood/evaluate`
- `POST /api/v1/neurons/update`
- `POST /api/v1/notifications/clear`
- `POST /api/v1/notifications/send`
- `POST /api/v1/notifications/subscribe`
- `POST /api/v1/notifications/unsubscribe`
- `POST /api/v1/notifications/:notification_id/read`
- `POST /api/v1/search/index`
- `POST /api/v1/vector/embeddings`
- `POST /api/v1/vector/embeddings/bulk`
- `POST /api/v1/vector/similarity`
- `PUT /api/v1/notifications/subscriptions/:device_id`

## Kurzantwort

**Haben wir alles?**

**Nein.**

Es gibt echte Funktionslücken (73), dazu kommen 25 alte Endpunkte, die intern noch existieren, aber in der aktuellen öffentlichen API-Dokumentation nicht sichtbar sind. Ohne diese Abgleichung sind Integrationen, die auf alte Routen vertrauen (z. B. Kandidaten-Löschung, Notification-Subscriptions, Weather-, Energy- und Knowledge-Graph-/Vector-Management-Endpoints), nicht mehr stabil nutzbar.
