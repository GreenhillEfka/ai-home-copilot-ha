# PilotSuite Core – API v1 (Draft)

Auth: `X-Auth-Token: <token>`
Content-Type: application/json

## Health
- `GET /health` → `{ ok: true, time: ISO }`
- `GET /version` → `{ version: "0.1.0" }`

## Ingest (HA events)
### `POST /api/v1/ingest/events`
Body:
```json
{ "source": "homeassistant", "events": [
  {"t":"...","type":"state_changed","entity_id":"switch.coffee_machine","from":"off","to":"on","area_id":"kitchen","context":{"user_id":"...","parent_id":"..."}}
]}
```
Response: `{ ok: true }`

## Mood
- `GET /api/v1/moods/snapshot?scope=area:kitchen`
Response: `MoodSnapshot`

## Habitus
- `GET /api/v1/habitus/candidates?scope=area:kitchen&status=new`
- `POST /api/v1/habitus/candidates/{id}/accept`
- `POST /api/v1/habitus/candidates/{id}/reject`
- `POST /api/v1/habitus/candidates/{id}/defer`

Accept response (blueprint mapping):
```json
{
  "ok": true,
  "recommended_blueprint": {
    "name": "copilot_habitus_sequence_v1",
    "inputs": {
      "trigger_entity": "switch.coffee_machine",
      "trigger_to": "on",
      "action_service": "switch.turn_on",
      "action_entity": "switch.grinder",
      "delay_s": 10
    }
  }
}
```

## Brain Graph
- `GET /api/v1/graph/state`
- `GET /api/v1/graph/snapshot.svg`

## Synapses
- `GET /api/v1/synapses?status=active|candidate`

## Audit / Explain
- `GET /api/v1/audit/evidence?ref=candidate:{id}`

