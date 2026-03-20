# OpenAPI Count Reconciliation Report

**Datum:** 2026-03-20
**Spec:** `docs/openapi.yaml` (pilotsuite-styx-ha-current)
**CHANGELOG dokumentiert:** 572/572 paths

## Ergebnis

| Metrik | Wert |
|--------|------|
| Paths (Endpunkte) | 572 |
| Operations total (path+method) | 615 |
| Single-method paths | 531 |
| Multi-method paths | 41 |

**Status: ✅ 572/572 MATCH — Keine Lücken**

## Vollständige Mapping-Tabelle: Path → Method(s)

| # | Endpoint | Method(s) | Status |
|---|----------|----------|--------|
| 1 | `/api/styx/chat` | post | ✅ existiert |
| 2 | `/api/styx/health` | get | ✅ existiert |
| 3 | `/api/styx/health/backend` | get | ✅ existiert |
| 4 | `/api/v1/alarm/alarms` | get, post | ✅ existiert |
| 5 | `/api/v1/alarm/alarms/{alarm_id}` | delete, get, put | ✅ existiert |
| 6 | `/api/v1/alarm/alarms/{alarm_id}/cancel` | post | ✅ existiert |
| 7 | `/api/v1/alarm/alarms/{alarm_id}/snooze` | post | ✅ existiert |
| 8 | `/api/v1/alarm/alarms/{alarm_id}/trigger` | post | ✅ existiert |
| 9 | `/api/v1/alarm/curves` | get | ✅ existiert |
| 10 | `/api/v1/alarm/dashboard` | get | ✅ existiert |
| 11 | `/api/v1/alarm/presets` | get | ✅ existiert |
| 12 | `/api/v1/alarm/presets/{preset_id}` | delete, get | ✅ existiert |
| 13 | `/api/v1/alarm/presets/{preset_id}/create-alarm` | post | ✅ existiert |
| 14 | `/api/v1/alarm/zones/{zone_id}/alarms` | get | ✅ existiert |
| 15 | `/api/v1/anomaly/compare` | post | ✅ existiert |
| 16 | `/api/v1/anomaly/detect` | post | ✅ existiert |
| 17 | `/api/v1/anomaly/history` | get | ✅ existiert |
| 18 | `/api/v1/anomaly/model/load` | post | ✅ existiert |
| 19 | `/api/v1/anomaly/model/save` | post | ✅ existiert |
| 20 | `/api/v1/anomaly/model/status` | get | ✅ existiert |
| 21 | `/api/v1/anomaly/model/versions` | get | ✅ existiert |
| 22 | `/api/v1/anomaly/sensor/{sensor_id}/health` | get | ✅ existiert |
| 23 | `/api/v1/anomaly/store/stats` | get | ✅ existiert |
| 24 | `/api/v1/anomaly/train` | post | ✅ existiert |
| 25 | `/api/v1/calendar` | get | ✅ existiert |
| 26 | `/api/v1/calendar/events/today` | get | ✅ existiert |
| 27 | `/api/v1/calendar/events/upcoming` | get | ✅ existiert |
| 28 | `/api/v1/candidates` | get, post | ✅ existiert |
| 29 | `/api/v1/candidates/graph_candidates` | get | ✅ existiert |
| 30 | `/api/v1/candidates/stats` | get | ✅ existiert |
| 31 | `/api/v1/candidates/{candidate_id}` | get, put | ✅ existiert |
| 32 | `/api/v1/capabilities` | get | ✅ existiert |
| 33 | `/api/v1/chat/characters` | get | ✅ existiert |
| 34 | `/api/v1/chat/completions` | post | ✅ existiert |
| 35 | `/api/v1/chat/memory` | get | ✅ existiert |
| 36 | `/api/v1/chat/memory/preferences` | get | ✅ existiert |
| 37 | `/api/v1/chat/models/catalog` | get | ✅ existiert |
| 38 | `/api/v1/chat/models/delete` | post | ✅ existiert |
| 39 | `/api/v1/chat/models/pull` | post | ✅ existiert |
| 40 | `/api/v1/chat/models/pull/status` | post | ✅ existiert |
| 41 | `/api/v1/chat/models/recommended` | get | ✅ existiert |
| 42 | `/api/v1/chat/routing` | get, post | ✅ existiert |
| 43 | `/api/v1/chat/status` | get | ✅ existiert |
| 44 | `/api/v1/chat/tools` | get | ✅ existiert |
| 45 | `/api/v1/conversation/history` | get | ✅ existiert |
| 46 | `/api/v1/conversation/history/{conversation_id}` | get | ✅ existiert |
| 47 | `/api/v1/conversation/preferences` | get | ✅ existiert |
| 48 | `/api/v1/conversation/stats` | get | ✅ existiert |
| 49 | `/api/v1/dashboard/brain-summary` | get | ✅ existiert |
| 50 | `/api/v1/dashboard/health` | get | ✅ existiert |
| 51 | `/api/v1/dev/errors` | get | ✅ existiert |
| 52 | `/api/v1/dev/logs` | get | ✅ existiert |
| 53 | `/api/v1/dev/status` | get | ✅ existiert |
| 54 | `/api/v1/dev/support_bundle` | get | ✅ existiert |
| 55 | `/api/v1/docs` | get | ✅ existiert |
| 56 | `/api/v1/docs/openapi.json` | get | ✅ existiert |
| 57 | `/api/v1/docs/openapi.yaml` | get | ✅ existiert |
| 58 | `/api/v1/docs/validate` | get | ✅ existiert |
| 59 | `/api/v1/energy` | get | ✅ existiert |
| 60 | `/api/v1/energy/anomalies` | get | ✅ existiert |
| 61 | `/api/v1/energy/forecast/combined` | get | ✅ existiert |
| 62 | `/api/v1/energy/forecast/consumption` | get | ✅ existiert |
| 63 | `/api/v1/energy/forecast/pv` | get | ✅ existiert |
| 64 | `/api/v1/energy/load-shifting/devices` | post | ✅ existiert |
| 65 | `/api/v1/energy/load-shifting/recommendations` | get | ✅ existiert |
| 66 | `/api/v1/energy/load-shifting/windows` | get | ✅ existiert |
| 67 | `/api/v1/energy/sankey` | get | ✅ existiert |
| 68 | `/api/v1/energy/summary` | get | ✅ existiert |
| 69 | `/api/v1/errors/digest` | get | ✅ existiert |
| 70 | `/api/v1/errors/digest/categories` | get | ✅ existiert |
| 71 | `/api/v1/errors/repair-suggestions` | post | ✅ existiert |
| 72 | `/api/v1/events` | get, post | ✅ existiert |
| 73 | `/api/v1/events/stats` | get | ✅ existiert |
| 74 | `/api/v1/federated` | get | ✅ existiert |
| 75 | `/api/v1/federated/aggregate` | post | ✅ existiert |
| 76 | `/api/v1/federated/knowledge` | post | ✅ existiert |
| 77 | `/api/v1/federated/knowledge-base` | get | ✅ existiert |
| 78 | `/api/v1/federated/knowledge/{knowledge_id}/transfer` | post | ✅ existiert |
| 79 | `/api/v1/federated/load` | post | ✅ existiert |
| 80 | `/api/v1/federated/models` | get | ✅ existiert |
| 81 | `/api/v1/federated/register` | post | ✅ existiert |
| 82 | `/api/v1/federated/round` | post | ✅ existiert |
| 83 | `/api/v1/federated/rounds` | get | ✅ existiert |
| 84 | `/api/v1/federated/save` | post | ✅ existiert |
| 85 | `/api/v1/federated/start` | post | ✅ existiert |
| 86 | `/api/v1/federated/statistics` | get | ✅ existiert |
| 87 | `/api/v1/federated/stop` | post | ✅ existiert |
| 88 | `/api/v1/federated/update` | post | ✅ existiert |
| 89 | `/api/v1/graph/cache/clear` | post | ✅ existiert |
| 90 | `/api/v1/graph/ops` | post | ✅ existiert |
| 91 | `/api/v1/graph/patterns` | get | ✅ existiert |
| 92 | `/api/v1/graph/query` | post | ✅ existiert |
| 93 | `/api/v1/graph/render` | post | ✅ existiert |
| 94 | `/api/v1/graph/snapshot.svg` | get | ✅ existiert |
| 95 | `/api/v1/graph/state` | get | ✅ existiert |
| 96 | `/api/v1/graph/stats` | get | ✅ existiert |
| 97 | `/api/v1/ha/areas` | get | ✅ existiert |
| 98 | `/api/v1/ha/connect` | post | ✅ existiert |
| 99 | `/api/v1/ha/disconnect` | post | ✅ existiert |
| 100 | `/api/v1/ha/discover` | post | ✅ existiert |
| 101 | `/api/v1/ha/entities` | get | ✅ existiert |
| 102 | `/api/v1/ha/entity/{entity_id}` | get | ✅ existiert |
| 103 | `/api/v1/ha/status` | get | ✅ existiert |
| 104 | `/api/v1/habitus/config` | get, post | ✅ existiert |
| 105 | `/api/v1/habitus/dashboard_cards` | get | ✅ existiert |
| 106 | `/api/v1/habitus/dashboard_cards/health` | get | ✅ existiert |
| 107 | `/api/v1/habitus/dashboard_cards/rules` | get | ✅ existiert |
| 108 | `/api/v1/habitus/dashboard_cards/zone/{zone_id}` | get | ✅ existiert |
| 109 | `/api/v1/habitus/dashboard_cards/zones` | get | ✅ existiert |
| 110 | `/api/v1/habitus/health` | get | ✅ existiert |
| 111 | `/api/v1/habitus/mine` | post | ✅ existiert |
| 112 | `/api/v1/habitus/patterns` | get | ✅ existiert |
| 113 | `/api/v1/habitus/reset` | post | ✅ existiert |
| 114 | `/api/v1/habitus/rules` | get | ✅ existiert |
| 115 | `/api/v1/habitus/rules/summary` | get | ✅ existiert |
| 116 | `/api/v1/habitus/rules/{rule_key}/explain` | get | ✅ existiert |
| 117 | `/api/v1/habitus/stats` | get | ✅ existiert |
| 118 | `/api/v1/habitus/status` | get | ✅ existiert |
| 119 | `/api/v1/habitus/zones` | get | ✅ existiert |
| 120 | `/api/v1/habitus/zones/match` | post | ✅ existiert |
| 121 | `/api/v1/habitus/zones/review` | get | ✅ existiert |
| 122 | `/api/v1/habitus/zones/{zone_id}` | post | ✅ existiert |
| 123 | `/api/v1/habitus/zones/{zone_id}/metrics` | get | ✅ existiert |
| 124 | `/api/v1/health` | get | ✅ existiert |
| 125 | `/api/v1/hints` | get, post | ✅ existiert |
| 126 | `/api/v1/hints/suggestions` | get | ✅ existiert |
| 127 | `/api/v1/hints/types` | get | ✅ existiert |
| 128 | `/api/v1/hints/{hint_id}` | get | ✅ existiert |
| 129 | `/api/v1/hints/{hint_id}/accept` | post | ✅ existiert |
| 130 | `/api/v1/hints/{hint_id}/reject` | post | ✅ existiert |
| 131 | `/api/v1/homekit/all-zones-info` | get | ✅ existiert |
| 132 | `/api/v1/homekit/qr/{zone_id}.png` | get | ✅ existiert |
| 133 | `/api/v1/homekit/qr/{zone_id}.svg` | get | ✅ existiert |
| 134 | `/api/v1/homekit/setup-info/{zone_id}` | get | ✅ existiert |
| 135 | `/api/v1/homekit/status` | get | ✅ existiert |
| 136 | `/api/v1/homekit/toggle` | post | ✅ existiert |
| 137 | `/api/v1/homekit/update` | post | ✅ existiert |
| 138 | `/api/v1/hub/anomalies` | get | ✅ existiert |
| 139 | `/api/v1/hub/anomalies/clear` | post | ✅ existiert |
| 140 | `/api/v1/hub/anomalies/correlations` | get | ✅ existiert |
| 141 | `/api/v1/hub/anomalies/detect` | post | ✅ existiert |
| 142 | `/api/v1/hub/anomalies/ingest` | post | ✅ existiert |
| 143 | `/api/v1/hub/anomalies/learn` | post | ✅ existiert |
| 144 | `/api/v1/hub/anomalies/list` | get | ✅ existiert |
| 145 | `/api/v1/hub/brain` | get | ✅ existiert |
| 146 | `/api/v1/hub/brain/activity` | get | ✅ existiert |
| 147 | `/api/v1/hub/brain/activity/chat` | get, post | ✅ existiert |
| 148 | `/api/v1/hub/brain/activity/chat/clear` | post | ✅ existiert |
| 149 | `/api/v1/hub/brain/activity/config` | post | ✅ existiert |
| 150 | `/api/v1/hub/brain/activity/pulse` | post | ✅ existiert |
| 151 | `/api/v1/hub/brain/activity/pulse/end` | post | ✅ existiert |
| 152 | `/api/v1/hub/brain/activity/sleep` | post | ✅ existiert |
| 153 | `/api/v1/hub/brain/activity/state` | get | ✅ existiert |
| 154 | `/api/v1/hub/brain/activity/wake` | post | ✅ existiert |
| 155 | `/api/v1/hub/brain/graph` | get | ✅ existiert |
| 156 | `/api/v1/hub/brain/regions` | get | ✅ existiert |
| 157 | `/api/v1/hub/brain/regions/{region_id}` | get | ✅ existiert |
| 158 | `/api/v1/hub/brain/synapses` | get, post | ✅ existiert |
| 159 | `/api/v1/hub/brain/synapses/{synapse_id}` | delete | ✅ existiert |
| 160 | `/api/v1/hub/brain/synapses/{synapse_id}/fire` | post | ✅ existiert |
| 161 | `/api/v1/hub/brain/synapses/{synapse_id}/state` | post | ✅ existiert |
| 162 | `/api/v1/hub/brain/sync` | post | ✅ existiert |
| 163 | `/api/v1/hub/dashboard` | get | ✅ existiert |
| 164 | `/api/v1/hub/dashboard/layout` | post | ✅ existiert |
| 165 | `/api/v1/hub/dashboard/widget` | post | ✅ existiert |
| 166 | `/api/v1/hub/dashboard/widget/{widget_type}` | delete, get | ✅ existiert |
| 167 | `/api/v1/hub/energy` | get | ✅ existiert |
| 168 | `/api/v1/hub/energy/breakdown` | get | ✅ existiert |
| 169 | `/api/v1/hub/energy/consumption` | post | ✅ existiert |
| 170 | `/api/v1/hub/energy/devices` | post | ✅ existiert |
| 171 | `/api/v1/hub/energy/eco-score` | get | ✅ existiert |
| 172 | `/api/v1/hub/energy/price` | post | ✅ existiert |
| 173 | `/api/v1/hub/energy/recommendations` | get | ✅ existiert |
| 174 | `/api/v1/hub/energy/recommendations/{rec_id}/apply` | post | ✅ existiert |
| 175 | `/api/v1/hub/energy/top` | get | ✅ existiert |
| 176 | `/api/v1/hub/homes` | get, post | ✅ existiert |
| 177 | `/api/v1/hub/homes/{home_id}` | delete, get | ✅ existiert |
| 178 | `/api/v1/hub/homes/{home_id}/activate` | post | ✅ existiert |
| 179 | `/api/v1/hub/homes/{home_id}/status` | post | ✅ existiert |
| 180 | `/api/v1/hub/integration` | get | ✅ existiert |
| 181 | `/api/v1/hub/integration/auto-wire` | post | ✅ existiert |
| 182 | `/api/v1/hub/integration/dispatch` | post | ✅ existiert |
| 183 | `/api/v1/hub/integration/status` | get | ✅ existiert |
| 184 | `/api/v1/hub/integration/wiring` | get | ✅ existiert |
| 185 | `/api/v1/hub/light` | get | ✅ existiert |
| 186 | `/api/v1/hub/light/brightness` | post | ✅ existiert |
| 187 | `/api/v1/hub/light/scene` | post | ✅ existiert |
| 188 | `/api/v1/hub/light/scenes` | get | ✅ existiert |
| 189 | `/api/v1/hub/light/suggest` | get | ✅ existiert |
| 190 | `/api/v1/hub/light/sun` | post | ✅ existiert |
| 191 | `/api/v1/hub/light/zone/{zone_id}` | get | ✅ existiert |
| 192 | `/api/v1/hub/maintenance` | get | ✅ existiert |
| 193 | `/api/v1/hub/maintenance/device/{device_id}` | get | ✅ existiert |
| 194 | `/api/v1/hub/maintenance/evaluate` | post | ✅ existiert |
| 195 | `/api/v1/hub/maintenance/ingest` | post | ✅ existiert |
| 196 | `/api/v1/hub/maintenance/register` | post | ✅ existiert |
| 197 | `/api/v1/hub/media` | get | ✅ existiert |
| 198 | `/api/v1/hub/media/follow` | post | ✅ existiert |
| 199 | `/api/v1/hub/media/playback` | post | ✅ existiert |
| 200 | `/api/v1/hub/media/sessions` | get | ✅ existiert |
| 201 | `/api/v1/hub/media/sources` | get, post | ✅ existiert |
| 202 | `/api/v1/hub/media/sources/{entity_id}` | delete | ✅ existiert |
| 203 | `/api/v1/hub/media/transfer` | post | ✅ existiert |
| 204 | `/api/v1/hub/media/zone/{zone_id}` | get | ✅ existiert |
| 205 | `/api/v1/hub/media/zone_enter` | post | ✅ existiert |
| 206 | `/api/v1/hub/modes` | get | ✅ existiert |
| 207 | `/api/v1/hub/modes/activate` | post | ✅ existiert |
| 208 | `/api/v1/hub/modes/available` | get | ✅ existiert |
| 209 | `/api/v1/hub/modes/custom` | post | ✅ existiert |
| 210 | `/api/v1/hub/modes/deactivate` | post | ✅ existiert |
| 211 | `/api/v1/hub/modes/expire` | post | ✅ existiert |
| 212 | `/api/v1/hub/modes/zone/{zone_id}` | get | ✅ existiert |
| 213 | `/api/v1/hub/notifications` | get | ✅ existiert |
| 214 | `/api/v1/hub/notifications/batch` | post | ✅ existiert |
| 215 | `/api/v1/hub/notifications/batch/flush` | post | ✅ existiert |
| 216 | `/api/v1/hub/notifications/dnd` | post | ✅ existiert |
| 217 | `/api/v1/hub/notifications/dnd/status` | get | ✅ existiert |
| 218 | `/api/v1/hub/notifications/history` | get | ✅ existiert |
| 219 | `/api/v1/hub/notifications/read-all` | post | ✅ existiert |
| 220 | `/api/v1/hub/notifications/rules` | get, post | ✅ existiert |
| 221 | `/api/v1/hub/notifications/rules/{rule_id}` | delete | ✅ existiert |
| 222 | `/api/v1/hub/notifications/send` | post | ✅ existiert |
| 223 | `/api/v1/hub/notifications/stats` | get | ✅ existiert |
| 224 | `/api/v1/hub/notifications/{notification_id}/read` | post | ✅ existiert |
| 225 | `/api/v1/hub/plugins` | get | ✅ existiert |
| 226 | `/api/v1/hub/plugins/{plugin_id}` | get | ✅ existiert |
| 227 | `/api/v1/hub/plugins/{plugin_id}/activate` | post | ✅ existiert |
| 228 | `/api/v1/hub/plugins/{plugin_id}/config` | post | ✅ existiert |
| 229 | `/api/v1/hub/plugins/{plugin_id}/disable` | post | ✅ existiert |
| 230 | `/api/v1/hub/presence` | get | ✅ existiert |
| 231 | `/api/v1/hub/presence/heatmap` | get | ✅ existiert |
| 232 | `/api/v1/hub/presence/household` | get | ✅ existiert |
| 233 | `/api/v1/hub/presence/idle` | post | ✅ existiert |
| 234 | `/api/v1/hub/presence/persons` | post | ✅ existiert |
| 235 | `/api/v1/hub/presence/persons/{person_id}` | delete, get | ✅ existiert |
| 236 | `/api/v1/hub/presence/room/{room_id}/occupancy` | get | ✅ existiert |
| 237 | `/api/v1/hub/presence/rooms` | get, post | ✅ existiert |
| 238 | `/api/v1/hub/presence/transitions` | get | ✅ existiert |
| 239 | `/api/v1/hub/presence/triggers` | get, post | ✅ existiert |
| 240 | `/api/v1/hub/presence/triggers/{trigger_id}` | delete | ✅ existiert |
| 241 | `/api/v1/hub/presence/update` | post | ✅ existiert |
| 242 | `/api/v1/hub/scenes` | get | ✅ existiert |
| 243 | `/api/v1/hub/scenes/activate` | post | ✅ existiert |
| 244 | `/api/v1/hub/scenes/active` | get | ✅ existiert |
| 245 | `/api/v1/hub/scenes/cloud` | post | ✅ existiert |
| 246 | `/api/v1/hub/scenes/cloud/share` | post | ✅ existiert |
| 247 | `/api/v1/hub/scenes/cloud/status` | get | ✅ existiert |
| 248 | `/api/v1/hub/scenes/custom` | post | ✅ existiert |
| 249 | `/api/v1/hub/scenes/deactivate` | post | ✅ existiert |
| 250 | `/api/v1/hub/scenes/learn` | post | ✅ existiert |
| 251 | `/api/v1/hub/scenes/list` | get | ✅ existiert |
| 252 | `/api/v1/hub/scenes/suggest` | post | ✅ existiert |
| 253 | `/api/v1/hub/scenes/{scene_id}/rate` | post | ✅ existiert |
| 254 | `/api/v1/hub/status` | get | ✅ existiert |
| 255 | `/api/v1/hub/templates` | get | ✅ existiert |
| 256 | `/api/v1/hub/templates/categories` | get | ✅ existiert |
| 257 | `/api/v1/hub/templates/custom` | post | ✅ existiert |
| 258 | `/api/v1/hub/templates/generate` | post | ✅ existiert |
| 259 | `/api/v1/hub/templates/summary` | get | ✅ existiert |
| 260 | `/api/v1/hub/templates/{template_id}` | get | ✅ existiert |
| 261 | `/api/v1/hub/templates/{template_id}/rate` | post | ✅ existiert |
| 262 | `/api/v1/hub/zones` | get | ✅ existiert |
| 263 | `/api/v1/hub/zones/modes` | get | ✅ existiert |
| 264 | `/api/v1/hub/zones/rooms` | get, post | ✅ existiert |
| 265 | `/api/v1/hub/zones/template/{template_id}` | post | ✅ existiert |
| 266 | `/api/v1/hub/zones/templates` | get | ✅ existiert |
| 267 | `/api/v1/hub/zones/{zone_id}` | delete, get | ✅ existiert |
| 268 | `/api/v1/hub/zones/{zone_id}/mode` | post | ✅ existiert |
| 269 | `/api/v1/hub/zones/{zone_id}/room` | post | ✅ existiert |
| 270 | `/api/v1/hub/zones/{zone_id}/room/{room_id}` | delete | ✅ existiert |
| 271 | `/api/v1/integration/bus/stats` | get | ✅ existiert |
| 272 | `/api/v1/integration/feedback` | post | ✅ existiert |
| 273 | `/api/v1/kg/edges` | get, post | ✅ existiert |
| 274 | `/api/v1/kg/entities` | post | ✅ existiert |
| 275 | `/api/v1/kg/entity/{entity_id}/related` | get | ✅ existiert |
| 276 | `/api/v1/kg/import/entities` | post | ✅ existiert |
| 277 | `/api/v1/kg/import/patterns` | post | ✅ existiert |
| 278 | `/api/v1/kg/mood/{mood}/patterns` | get | ✅ existiert |
| 279 | `/api/v1/kg/moods` | post | ✅ existiert |
| 280 | `/api/v1/kg/nodes` | get, post | ✅ existiert |
| 281 | `/api/v1/kg/nodes/{node_id}` | get | ✅ existiert |
| 282 | `/api/v1/kg/pattern/{pattern_id}` | get | ✅ existiert |
| 283 | `/api/v1/kg/query` | post | ✅ existiert |
| 284 | `/api/v1/kg/stats` | get | ✅ existiert |
| 285 | `/api/v1/kg/zone/{zone_id}/entities` | get | ✅ existiert |
| 286 | `/api/v1/kg/zones` | post | ✅ existiert |
| 287 | `/api/v1/legacy/health` | get | ✅ existiert |
| 288 | `/api/v1/live` | get | ✅ existiert |
| 289 | `/api/v1/log_fixer_tx/recover` | post | ✅ existiert |
| 290 | `/api/v1/log_fixer_tx/status` | get | ✅ existiert |
| 291 | `/api/v1/log_fixer_tx/transactions` | get, post | ✅ existiert |
| 292 | `/api/v1/log_fixer_tx/transactions/{tx_id}` | get | ✅ existiert |
| 293 | `/api/v1/log_fixer_tx/transactions/{tx_id}/rollback` | post | ✅ existiert |
| 294 | `/api/v1/mcp/connect` | post | ✅ existiert |
| 295 | `/api/v1/mcp/query` | post | ✅ existiert |
| 296 | `/api/v1/mcp/resources` | get | ✅ existiert |
| 297 | `/api/v1/mcp/status` | get | ✅ existiert |
| 298 | `/api/v1/mcp/tools` | get | ✅ existiert |
| 299 | `/api/v1/mcp/tools/call` | post | ✅ existiert |
| 300 | `/api/v1/media/musikwolke` | get | ✅ existiert |
| 301 | `/api/v1/media/musikwolke/start` | post | ✅ existiert |
| 302 | `/api/v1/media/musikwolke/{session_id}/stop` | post | ✅ existiert |
| 303 | `/api/v1/media/musikwolke/{session_id}/update` | post | ✅ existiert |
| 304 | `/api/v1/media/proactive/deliver` | post | ✅ existiert |
| 305 | `/api/v1/media/proactive/dismiss` | post | ✅ existiert |
| 306 | `/api/v1/media/proactive/reset-dismissals` | post | ✅ existiert |
| 307 | `/api/v1/media/proactive/zone-entry` | post | ✅ existiert |
| 308 | `/api/v1/media/zones` | get | ✅ existiert |
| 309 | `/api/v1/media/zones/group` | post | ✅ existiert |
| 310 | `/api/v1/media/zones/group-all` | post | ✅ existiert |
| 311 | `/api/v1/media/zones/ungroup` | post | ✅ existiert |
| 312 | `/api/v1/media/zones/ungroup-all` | post | ✅ existiert |
| 313 | `/api/v1/media/zones/{zone_id}` | get | ✅ existiert |
| 314 | `/api/v1/media/zones/{zone_id}/assign` | post | ✅ existiert |
| 315 | `/api/v1/media/zones/{zone_id}/favorites` | get | ✅ existiert |
| 316 | `/api/v1/media/zones/{zone_id}/pause` | post | ✅ existiert |
| 317 | `/api/v1/media/zones/{zone_id}/play` | post | ✅ existiert |
| 318 | `/api/v1/media/zones/{zone_id}/play-media` | post | ✅ existiert |
| 319 | `/api/v1/media/zones/{zone_id}/select-source` | post | ✅ existiert |
| 320 | `/api/v1/media/zones/{zone_id}/state` | get | ✅ existiert |
| 321 | `/api/v1/media/zones/{zone_id}/volume` | post | ✅ existiert |
| 322 | `/api/v1/media/zones/{zone_id}/{entity_id}` | delete | ✅ existiert |
| 323 | `/api/v1/metrics` | get | ✅ existiert |
| 324 | `/api/v1/metrics/summary` | get | ✅ existiert |
| 325 | `/api/v1/modules` | get | ✅ existiert |
| 326 | `/api/v1/modules/health/dashboard` | get | ✅ existiert |
| 327 | `/api/v1/modules/health/learning` | get | ✅ existiert |
| 328 | `/api/v1/modules/health/patterns` | get | ✅ existiert |
| 329 | `/api/v1/modules/{module_id}` | get | ✅ existiert |
| 330 | `/api/v1/modules/{module_id}/configure` | get | ✅ existiert |
| 331 | `/api/v1/mood` | get | ✅ existiert |
| 332 | `/api/v1/mood/aggregated` | get | ✅ existiert |
| 333 | `/api/v1/mood/score` | post | ✅ existiert |
| 334 | `/api/v1/mood/state` | get | ✅ existiert |
| 335 | `/api/v1/mood/summary` | get | ✅ existiert |
| 336 | `/api/v1/mood/update-habitus` | post | ✅ existiert |
| 337 | `/api/v1/mood/update-media` | post | ✅ existiert |
| 338 | `/api/v1/mood/zones/status` | get | ✅ existiert |
| 339 | `/api/v1/mood/zones/{zone_name}/force_mood` | post | ✅ existiert |
| 340 | `/api/v1/mood/zones/{zone_name}/orchestrate` | post | ✅ existiert |
| 341 | `/api/v1/mood/zones/{zone_name}/status` | get | ✅ existiert |
| 342 | `/api/v1/mood/{zone_id}` | get | ✅ existiert |
| 343 | `/api/v1/mood/{zone_id}/suppress-energy-saving` | get | ✅ existiert |
| 344 | `/api/v1/multihome/climate/preheat` | post | ✅ existiert |
| 345 | `/api/v1/multihome/config/diff/{source_home_id}/{target_home_id}` | get | ✅ existiert |
| 346 | `/api/v1/multihome/config/sync` | post | ✅ existiert |
| 347 | `/api/v1/multihome/config/sync/{operation_id}/apply` | post | ✅ existiert |
| 348 | `/api/v1/multihome/conflicts` | get | ✅ existiert |
| 349 | `/api/v1/multihome/conflicts/{conflict_id}/resolve` | post | ✅ existiert |
| 350 | `/api/v1/multihome/homes` | get, post | ✅ existiert |
| 351 | `/api/v1/multihome/homes/{home_id}` | delete, get | ✅ existiert |
| 352 | `/api/v1/multihome/location/sync` | post | ✅ existiert |
| 353 | `/api/v1/multihome/operations` | get | ✅ existiert |
| 354 | `/api/v1/multihome/operations/cleanup` | delete | ✅ existiert |
| 355 | `/api/v1/multihome/operations/{operation_id}/execute` | post | ✅ existiert |
| 356 | `/api/v1/multihome/settings` | get, put | ✅ existiert |
| 357 | `/api/v1/multihome/state/diff/{home_id_1}/{home_id_2}` | get | ✅ existiert |
| 358 | `/api/v1/multihome/state/sync` | post | ✅ existiert |
| 359 | `/api/v1/multihome/state/sync/{operation_id}/apply` | post | ✅ existiert |
| 360 | `/api/v1/multihome/status` | get | ✅ existiert |
| 361 | `/api/v1/neurons` | get | ✅ existiert |
| 362 | `/api/v1/neurons/batch-configure` | post | ✅ existiert |
| 363 | `/api/v1/neurons/brain/pipeline` | get | ✅ existiert |
| 364 | `/api/v1/neurons/configure` | post | ✅ existiert |
| 365 | `/api/v1/neurons/connections` | get | ✅ existiert |
| 366 | `/api/v1/neurons/evaluate` | post | ✅ existiert |
| 367 | `/api/v1/neurons/graph` | get | ✅ existiert |
| 368 | `/api/v1/neurons/graph/stats` | get | ✅ existiert |
| 369 | `/api/v1/neurons/layers/heatmap` | get | ✅ existiert |
| 370 | `/api/v1/neurons/layers/snapshot.svg` | get | ✅ existiert |
| 371 | `/api/v1/neurons/layers/synapses` | get | ✅ existiert |
| 372 | `/api/v1/neurons/layers/synapses/reset` | post | ✅ existiert |
| 373 | `/api/v1/neurons/layers/synapses/update` | post | ✅ existiert |
| 374 | `/api/v1/neurons/layers/visualization` | get | ✅ existiert |
| 375 | `/api/v1/neurons/mood` | get | ✅ existiert |
| 376 | `/api/v1/neurons/mood/evaluate` | post | ✅ existiert |
| 377 | `/api/v1/neurons/mood/history` | get | ✅ existiert |
| 378 | `/api/v1/neurons/paths` | get | ✅ existiert |
| 379 | `/api/v1/neurons/state` | get | ✅ existiert |
| 380 | `/api/v1/neurons/suggestions` | get | ✅ existiert |
| 381 | `/api/v1/neurons/update` | post | ✅ existiert |
| 382 | `/api/v1/neurons/{neuron_id}` | get | ✅ existiert |
| 383 | `/api/v1/neurons/{neuron_id}/config` | patch | ✅ existiert |
| 384 | `/api/v1/neurons/{neuron_id}/disable` | post | ✅ existiert |
| 385 | `/api/v1/neurons/{neuron_id}/enable` | post | ✅ existiert |
| 386 | `/api/v1/neurons/{neuron_id}/fire` | get | ✅ existiert |
| 387 | `/api/v1/neurons/{neuron_id}/stats` | get | ✅ existiert |
| 388 | `/api/v1/notifications` | get, post | ✅ existiert |
| 389 | `/api/v1/notifications/clear` | post | ✅ existiert |
| 390 | `/api/v1/notifications/digest` | get | ✅ existiert |
| 391 | `/api/v1/notifications/ha/devices` | get | ✅ existiert |
| 392 | `/api/v1/notifications/ha/devices/{device_id}` | delete | ✅ existiert |
| 393 | `/api/v1/notifications/ha/devices/{device_id}/disable` | post | ✅ existiert |
| 394 | `/api/v1/notifications/ha/devices/{device_id}/enable` | post | ✅ existiert |
| 395 | `/api/v1/notifications/ha/register` | post | ✅ existiert |
| 396 | `/api/v1/notifications/ha/services` | get | ✅ existiert |
| 397 | `/api/v1/notifications/ha/test` | get | ✅ existiert |
| 398 | `/api/v1/notifications/pending` | get | ✅ existiert |
| 399 | `/api/v1/notifications/send` | post | ✅ existiert |
| 400 | `/api/v1/notifications/send/ha` | post | ✅ existiert |
| 401 | `/api/v1/notifications/stats` | get | ✅ existiert |
| 402 | `/api/v1/notifications/subscribe` | post | ✅ existiert |
| 403 | `/api/v1/notifications/subscriptions` | get | ✅ existiert |
| 404 | `/api/v1/notifications/subscriptions/{device_id}` | put | ✅ existiert |
| 405 | `/api/v1/notifications/unsubscribe` | post | ✅ existiert |
| 406 | `/api/v1/notifications/{notification_id}` | delete | ✅ existiert |
| 407 | `/api/v1/notifications/{notification_id}/read` | post | ✅ existiert |
| 408 | `/api/v1/openapi.json` | get | ✅ existiert |
| 409 | `/api/v1/openapi.yaml` | get | ✅ existiert |
| 410 | `/api/v1/rag/cache/clear` | post | ✅ existiert |
| 411 | `/api/v1/rag/index` | post | ✅ existiert |
| 412 | `/api/v1/rag/rerank` | post | ✅ existiert |
| 413 | `/api/v1/rag/search` | post | ✅ existiert |
| 414 | `/api/v1/rag/search/bm25` | post | ✅ existiert |
| 415 | `/api/v1/rag/search/enhanced` | post | ✅ existiert |
| 416 | `/api/v1/rag/search/semantic` | post | ✅ existiert |
| 417 | `/api/v1/rag/stats` | get | ✅ existiert |
| 418 | `/api/v1/rate-limit/cleanup` | post | ✅ existiert |
| 419 | `/api/v1/rate-limit/config` | get, put | ✅ existiert |
| 420 | `/api/v1/rate-limit/config/{client_id}` | delete | ✅ existiert |
| 421 | `/api/v1/rate-limit/defaults` | get | ✅ existiert |
| 422 | `/api/v1/rate-limit/reset-all` | post | ✅ existiert |
| 423 | `/api/v1/rate-limit/status` | get | ✅ existiert |
| 424 | `/api/v1/rate-limit/status/{client_id}` | get | ✅ existiert |
| 425 | `/api/v1/ready` | get | ✅ existiert |
| 426 | `/api/v1/search` | get | ✅ existiert |
| 427 | `/api/v1/search/entities` | get | ✅ existiert |
| 428 | `/api/v1/search/index` | post | ✅ existiert |
| 429 | `/api/v1/search/stats` | get | ✅ existiert |
| 430 | `/api/v1/sensors` | get | ✅ existiert |
| 431 | `/api/v1/sensors/cache/clear` | post | ✅ existiert |
| 432 | `/api/v1/sensors/cache/stats` | get | ✅ existiert |
| 433 | `/api/v1/sensors/rooms` | get | ✅ existiert |
| 434 | `/api/v1/sensors/types` | get | ✅ existiert |
| 435 | `/api/v1/sensors/{entity_id}` | get | ✅ existiert |
| 436 | `/api/v1/sharing` | get | ✅ existiert |
| 437 | `/api/v1/sharing/discovery/local` | get | ✅ existiert |
| 438 | `/api/v1/sharing/discovery/peers` | get | ✅ existiert |
| 439 | `/api/v1/sharing/entities` | get, post | ✅ existiert |
| 440 | `/api/v1/sharing/entities/shared` | get | ✅ existiert |
| 441 | `/api/v1/sharing/entities/{entity_id}` | delete, get, put | ✅ existiert |
| 442 | `/api/v1/sharing/entities/{entity_id}/share-with` | post | ✅ existiert |
| 443 | `/api/v1/sharing/entities/{entity_id}/shared-with` | get | ✅ existiert |
| 444 | `/api/v1/sharing/entities/{entity_id}/stop-sharing/{home_id}` | post | ✅ existiert |
| 445 | `/api/v1/sharing/sync/entities` | get | ✅ existiert |
| 446 | `/api/v1/sharing/sync/entities/{entity_id}` | get | ✅ existiert |
| 447 | `/api/v1/sharing/sync/peers` | get | ✅ existiert |
| 448 | `/api/v1/sharing/sync/status` | get | ✅ existiert |
| 449 | `/api/v1/sonos/health` | get | ✅ existiert |
| 450 | `/api/v1/sonos/intelligence/presence` | post | ✅ existiert |
| 451 | `/api/v1/sonos/intelligence/zones` | get, post | ✅ existiert |
| 452 | `/api/v1/sonos/intelligence/zones/{zone_id}/fallback` | get, post | ✅ existiert |
| 453 | `/api/v1/sonos/pauseall` | post | ✅ existiert |
| 454 | `/api/v1/sonos/presets` | get, post | ✅ existiert |
| 455 | `/api/v1/sonos/presets/{preset_id}` | delete, get | ✅ existiert |
| 456 | `/api/v1/sonos/presets/{preset_id}/apply` | post | ✅ existiert |
| 457 | `/api/v1/sonos/resumeall` | post | ✅ existiert |
| 458 | `/api/v1/sonos/rooms` | get | ✅ existiert |
| 459 | `/api/v1/sonos/rooms/{room}/favorite` | post | ✅ existiert |
| 460 | `/api/v1/sonos/rooms/{room}/favorites` | get | ✅ existiert |
| 461 | `/api/v1/sonos/rooms/{room}/join` | post | ✅ existiert |
| 462 | `/api/v1/sonos/rooms/{room}/leave` | post | ✅ existiert |
| 463 | `/api/v1/sonos/rooms/{room}/mute` | post | ✅ existiert |
| 464 | `/api/v1/sonos/rooms/{room}/next` | post | ✅ existiert |
| 465 | `/api/v1/sonos/rooms/{room}/pause` | post | ✅ existiert |
| 466 | `/api/v1/sonos/rooms/{room}/play` | post | ✅ existiert |
| 467 | `/api/v1/sonos/rooms/{room}/playlist` | post | ✅ existiert |
| 468 | `/api/v1/sonos/rooms/{room}/playlists` | get | ✅ existiert |
| 469 | `/api/v1/sonos/rooms/{room}/previous` | post | ✅ existiert |
| 470 | `/api/v1/sonos/rooms/{room}/queue` | get | ✅ existiert |
| 471 | `/api/v1/sonos/rooms/{room}/queue/clear` | post | ✅ existiert |
| 472 | `/api/v1/sonos/rooms/{room}/say` | post | ✅ existiert |
| 473 | `/api/v1/sonos/rooms/{room}/shuffle` | post | ✅ existiert |
| 474 | `/api/v1/sonos/rooms/{room}/sleep` | post | ✅ existiert |
| 475 | `/api/v1/sonos/rooms/{room}/state` | get | ✅ existiert |
| 476 | `/api/v1/sonos/rooms/{room}/stop` | post | ✅ existiert |
| 477 | `/api/v1/sonos/rooms/{room}/toggle` | post | ✅ existiert |
| 478 | `/api/v1/sonos/rooms/{room}/volume` | post | ✅ existiert |
| 479 | `/api/v1/sonos/rooms/{room}/volume/adjust` | post | ✅ existiert |
| 480 | `/api/v1/sonos/sayall` | post | ✅ existiert |
| 481 | `/api/v1/sonos/volume-profiles` | get | ✅ existiert |
| 482 | `/api/v1/sonos/volume-profiles/{name}` | put | ✅ existiert |
| 483 | `/api/v1/sonos/zones` | get | ✅ existiert |
| 484 | `/api/v1/styx/config` | get | ✅ existiert |
| 485 | `/api/v1/styx/dashboard` | get | ✅ existiert |
| 486 | `/api/v1/styx/dashboard/compact` | get | ✅ existiert |
| 487 | `/api/v1/styx/stt` | post | ✅ existiert |
| 488 | `/api/v1/styx/tts` | post | ✅ existiert |
| 489 | `/api/v1/styx/voice/status` | get | ✅ existiert |
| 490 | `/api/v1/suggestions` | get | ✅ existiert |
| 491 | `/api/v1/suggestions/accept` | get | ✅ existiert |
| 492 | `/api/v1/suggestions/reject` | get | ✅ existiert |
| 493 | `/api/v1/suggestions/snooze` | get | ✅ existiert |
| 494 | `/api/v1/system_health` | get | ✅ existiert |
| 495 | `/api/v1/system_health/zigbee` | get | ✅ existiert |
| 496 | `/api/v1/system_health/zwave` | get | ✅ existiert |
| 497 | `/api/v1/tag-system/assignments` | get, post | ✅ existiert |
| 498 | `/api/v1/tag-system/tags` | get | ✅ existiert |
| 499 | `/api/v1/tag-system/tags/{tag_id}` | get | ✅ existiert |
| 500 | `/api/v1/unifi` | get | ✅ existiert |
| 501 | `/api/v1/user/active` | get | ✅ existiert |
| 502 | `/api/v1/user/all` | get | ✅ existiert |
| 503 | `/api/v1/user/conflicts/evaluate` | post | ✅ existiert |
| 504 | `/api/v1/user/delegations` | get | ✅ existiert |
| 505 | `/api/v1/user/mood/aggregated` | get | ✅ existiert |
| 506 | `/api/v1/user/roles` | get | ✅ existiert |
| 507 | `/api/v1/user/{user_id}` | delete | ✅ existiert |
| 508 | `/api/v1/user/{user_id}/access/{device_id}` | get | ✅ existiert |
| 509 | `/api/v1/user/{user_id}/delegate` | delete, post | ✅ existiert |
| 510 | `/api/v1/user/{user_id}/device/{device_id}` | post | ✅ existiert |
| 511 | `/api/v1/user/{user_id}/export` | get | ✅ existiert |
| 512 | `/api/v1/user/{user_id}/preference` | post | ✅ existiert |
| 513 | `/api/v1/user/{user_id}/preferences` | get | ✅ existiert |
| 514 | `/api/v1/user/{user_id}/priority` | post | ✅ existiert |
| 515 | `/api/v1/user/{user_id}/role` | get | ✅ existiert |
| 516 | `/api/v1/user/{user_id}/zone/{zone_id}/preference` | get | ✅ existiert |
| 517 | `/api/v1/vector/embeddings` | post | ✅ existiert |
| 518 | `/api/v1/vector/embeddings/bulk` | post | ✅ existiert |
| 519 | `/api/v1/vector/similar/{entry_id}` | get | ✅ existiert |
| 520 | `/api/v1/vector/similarity` | post | ✅ existiert |
| 521 | `/api/v1/vector/stats` | get | ✅ existiert |
| 522 | `/api/v1/vector/vectors` | delete, get | ✅ existiert |
| 523 | `/api/v1/vector/vectors/{entry_id}` | delete, get | ✅ existiert |
| 524 | `/api/v1/voice/context` | get, post | ✅ existiert |
| 525 | `/api/v1/voice/hints` | get | ✅ existiert |
| 526 | `/api/v1/voice/intent` | post | ✅ existiert |
| 527 | `/api/v1/voice/intents` | get | ✅ existiert |
| 528 | `/api/v1/voice/mood_history` | get | ✅ existiert |
| 529 | `/api/v1/voice/prompt` | get | ✅ existiert |
| 530 | `/api/v1/voice/speak` | post | ✅ existiert |
| 531 | `/api/v1/voice/status` | get | ✅ existiert |
| 532 | `/api/v1/voice/suggestions` | get | ✅ existiert |
| 533 | `/api/v1/voice/zones` | get | ✅ existiert |
| 534 | `/api/v1/weather` | get | ✅ existiert |
| 535 | `/api/v1/weather/forecast` | get | ✅ existiert |
| 536 | `/api/v1/weather/health` | get | ✅ existiert |
| 537 | `/api/v1/weather/pv-recommendations` | get | ✅ existiert |
| 538 | `/api/v1/zone-automation/dashboard` | get | ✅ existiert |
| 539 | `/api/v1/zone-automation/entities/search` | get | ✅ existiert |
| 540 | `/api/v1/zone-automation/import` | post | ✅ existiert |
| 541 | `/api/v1/zone-automation/roles` | get | ✅ existiert |
| 542 | `/api/v1/zone-automation/tags` | get | ✅ existiert |
| 543 | `/api/v1/zone-automation/zones/{zone_id}` | get | ✅ existiert |
| 544 | `/api/v1/zone-automation/zones/{zone_id}/brightness` | post | ✅ existiert |
| 545 | `/api/v1/zone-automation/zones/{zone_id}/config` | post | ✅ existiert |
| 546 | `/api/v1/zone-automation/zones/{zone_id}/entities` | get, post | ✅ existiert |
| 547 | `/api/v1/zone-automation/zones/{zone_id}/entities/{entity_id}` | delete | ✅ existiert |
| 548 | `/api/v1/zone-automation/zones/{zone_id}/entities/{entity_id}/role` | post | ✅ existiert |
| 549 | `/api/v1/zone-automation/zones/{zone_id}/entities/{entity_id}/tags` | post | ✅ existiert |
| 550 | `/api/v1/zone-automation/zones/{zone_id}/override` | post | ✅ existiert |
| 551 | `/api/v1/zone-automation/zones/{zone_id}/presence` | post | ✅ existiert |
| 552 | `/api/v1/zone-editor/modes` | get | ✅ existiert |
| 553 | `/api/v1/zone-editor/overview` | get | ✅ existiert |
| 554 | `/api/v1/zone-editor/rooms` | get | ✅ existiert |
| 555 | `/api/v1/zone-editor/rooms/{room_id}` | get | ✅ existiert |
| 556 | `/api/v1/zone-editor/templates` | get | ✅ existiert |
| 557 | `/api/v1/zone-editor/zones` | get | ✅ existiert |
| 558 | `/api/v1/zone-editor/zones/{zone_id}` | get | ✅ existiert |
| 559 | `/api/v1/zone-editor/zones/{zone_id}/state` | get | ✅ existiert |
| 560 | `/api/v1/zone/create` | post | ✅ existiert |
| 561 | `/api/v1/zone/dashboard` | get | ✅ existiert |
| 562 | `/api/v1/zone/dashboard/mood` | get | ✅ existiert |
| 563 | `/api/v1/zone/dashboard/mood/{zone_id}` | put | ✅ existiert |
| 564 | `/api/v1/zone/dashboard/quick-action` | post | ✅ existiert |
| 565 | `/api/v1/zone/dashboard/summary` | get | ✅ existiert |
| 566 | `/api/v1/zone/dashboard/{zone_id}` | get | ✅ existiert |
| 567 | `/api/v1/zone/delete/{zone_id}` | delete | ✅ existiert |
| 568 | `/api/v1/zone/update` | put | ✅ existiert |
| 569 | `/api/v1/zone/{zone_id}` | get | ✅ existiert |
| 570 | `/api/webhook/{webhook_id}` | post | ✅ existiert |
| 571 | `/telegram/send` | post | ✅ existiert |
| 572 | `/telegram/status` | get | ✅ existiert |

_Generated: 2026-03-20 20:47:38_