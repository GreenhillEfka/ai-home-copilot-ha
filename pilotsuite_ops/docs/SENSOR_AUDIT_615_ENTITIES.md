# SENSOR AUDIT — PilotSuite HA — v14.7.3 (running)

> **Audit:** 2026-03-21 15:20 GMT+1
> **HA:** `192.168.30.18:8123`, Token: Available
> **Entities found:** 615 total
> **Scope:** Alle `pilotsuite_*` + `copilot_ha_*` Entities

---

## ZUSAMMENFASSING

| Status | Anzahl | % |
|--------|--------|---|
| ✅ Active | 611 | 99.3% |
| ❌ Inactive | 4 | 0.7% |

---

## INAKTIVE ENTITIES (4)

| Entity | State | Ursache |
|--------|-------|---------|
| `number.pilotsuite_media_volume` | unavailable | Media-Stack nicht installiert |
| `select.pilotsuite_media_zone_select` | unknown | Media-Stack nicht installiert |
| `stt.pilotsuite_stt` | unknown | Speech-to-Text nicht installiert |
| `tts.pilotsuite_tts` | unknown | Text-to-Speech nicht installiert |

**Empfehlung:** In v14.9.x als "optional" markieren (Media-Addon) ODER mit Mock-Values versehen damit UI nicht "unavailable" zeigt.

---

## ACTIVE ENTITIES — DETAIL

### Zone-Based Entities (pro Zone, alle 10 Zonen aktiv)

**Zones:**
- `aussenbereich` (Außenbereich)
- `badbereich` (Badezimmer)
- `burobereich` (Büro)
- `elternhaus` (Elternhaus)
- `gangbereich` (Gang)
- `kellerbereich` (Keller)
- `kinderzimmer` (Kinderzimmer)
- `kochbereich` (Küche)
- `schlafbereich` (Schlafzimmer)
- `terrassenbereich` (Terrasse)
- `wohnbereich` (Wohnbereich)
- `zimmer_mira` (Zimmer Mira)

**Pro Zone — 21 number entities:**
`abschaltverzogerung`, `dampfungsband`, `einschaltverzogerung`, `farbtemperatur`, `min_helligkeit`, `musik_einschaltverzogerung`, `musik_pausenverzogerung`, `musiklautstarke`, `nachtabsenkung`, `soll_lux_innen`, `sonnenschutz_ab_lux`, `standard_position`, `standby_schwelle`, `tagesbudget`, `uberblendung`, `ubergangszeit`, `verriegelung_nach`, `ziel_helligkeit`, `zieltemperatur` + 2x `_2` suffixed variants

**Pro Zone — 7 select entities:**
`automationsmodus`, `bewegung`, `klima`, `licht`, `musik`, `rollladen`, `stimmung`

**Pro Zone — 21 switch entities:**
Alle Automationen + Settings

### Neuron Feed Switches (10 Zonen × 3 Typen = 30)
- `switch.pilotsuite_neuron_feed_neuron_context_{zone}`
- `switch.pilotsuite_neuron_feed_neuron_mood_{zone}`
- `switch.pilotsuite_neuron_feed_neuron_state_{zone}`

### Dashboard Switches (10)
`switch.pilotsuite_dashboard_{automation,chat,energie,haushalt,ki,musik,netzwerk,styx,system,zonen}`

### Buttons (8)
`button.pilotsuite_{check_core_update,check_ha_update,download_habitus_dashboard,download_pilotsuite_dashboard,generate_habitus_dashboard,generate_pilotsuite_dashboard,reload,validate_habitus_zones_v2}`

### Sensors (8)
```
sensor.pilotsuite_core_api_v1:          supported ✅
sensor.pilotsuite_habitus_zones:        12/12 active ✅
sensor.pilotsuite_habitus_zones_count:  12 ✅
sensor.pilotsuite_habitus_zones_v2_health: healthy ✅
sensor.pilotsuite_habitus_zones_v2_states: active ✅
sensor.pilotsuite_mood:                 relax ✅
sensor.pilotsuite_mood_confidence:      0 ✅
sensor.pilotsuite_styx_pipeline_health: healthy ✅
sensor.pilotsuite_styx_styx_agent_status: Styx: ready ✅
sensor.pilotsuite_styx_version:         14.7.3 ⚠️ (sollte 14.9.0 sein)
```

### Binary Sensor (1)
`binary_sensor.pilotsuite_styx_online: on` ✅

### Update Entity (1)
`update.pilotsuite_core_update: off` ✅

---

## VERSION DRIFT BEFUND

`sensor.pilotsuite_styx_version: 14.7.3`

aber addon soll auf `v14.9.0` sein. Container läuft noch auf alter Version → **Addon-Restart erforderlich**.

---

## PHASE 2 CLEANUP VORSCHLAG

1. **Media-Entities (4):** Als optional markieren ODER mit Mock-Werten versehen
2. **Version-Drift:** Addon-Restart für v14.9.0/v15.0.0
3. **61 Sensoren wie von PilotClaw erwähnt:** Nicht 61 Sensoren sondern 615 Entities — die meisten sind Zone-Entities (number/select/switch) die alle aktiv sind. Kein Blocker.

---

*Audit durchgeführt: HomeClaw Lane, 2026-03-21 15:20*
