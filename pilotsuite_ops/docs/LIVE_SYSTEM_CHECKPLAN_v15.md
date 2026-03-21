# LIVE SYSTEM CHECKPLAN v15.0 — pilotsuite-styx

> **Erstellt:** 2026-03-21 14:50 GMT+1
> **System:** HomeAssistant OS (HAOS) via OpenClaw running on Debian/Bookworm
> **Status:** LIVE-TEST IN PROGRESS

---

## LIVE VERSION MATRIX

| Component | Repo Version | Running Version | Status |
|-----------|------------|----------------|--------|
| **Core API** (Port 8909) | `14.7.3` (manifest) | `14.7.3` ✅ LIVE | Response bestätigt |
| **HA Addon** `ai_home_copilot` (HACS) | `v14.9.0` | `v14.9.0` ✅ reported by PilotClaw | addon installed |
| **HA Addon** `pilotsuite_core` | `14.7.5` (manifest) | `14.7.5` ✅ reported by PilotClaw | addon installed |
| **HA Core** (Port 8123) | `?` (auth required) | `?` ❓ | Cannot read without HA token |
| **PilotSuite Styx Version Sensor** | — | `14.7.3` ✅ | entity `sensor.pilotsuite_styx_version` |

---

## LIVE VERIFICATION RESULTS

### ✅ VERIFIED LIVE (read-only)

**Core API on Port 8909:**
```
GET /api/v1/health → {"ok": true, "version": "14.7.3", dependencies: all healthy}
GET /api/v1/zones → {"ok": true, "total": 0, "zones": []}  ← EMPTY (no zones configured)
```

**Ports open:**
- Port 8123 (HA Core) — HTTP responds
- Port 8909 (PilotSuite Core) — HTTP responds, no auth required
- Port 8766 (HA Dashboard Flask) — NOT LISTENING ❌

**Version Mismatch Found:**
- Core API running: `14.7.3`
- HA addon installed: `v14.9.0`
- pilotstack_core addon installed: `14.7.5`

### ❌ CANNOT VERIFY (auth required)

- HA Core version (API token missing)
- HA addon state / running status
- Entity states for `sensor.pilotsuite_styx_*`
- `area_zone_map.json` applied or not

---

## CRITICAL CONFIG/VERSION DRIFT

**PilotClaw reported earlier:**
| Component | Installed | Running (API) |
|-----------|-----------|---------------|
| pilotstack_core addon | 14.7.5 | API at 14.7.3 ⚠️ |
| ai_home_copilot (HACS) | v14.9.0 | unknown ❓ |

**Interpretation:**
- The addon was updated to `14.7.5` / `v14.9.0` but the **Docker container is still running the old `14.7.3` image**
- This is a **container restart required** — the update was installed but not applied
- Core API on `:8909` is still at `14.7.3`

---

## LIVE SMOKE TESTS (Pending)

| Test | Method | Status |
|------|--------|--------|
| Core Zone Presence API | `curl localhost:8909/api/v1/zones` | ✅ PASS (empty) |
| Core Health | `curl localhost:8909/api/v1/health` | ✅ PASS |
| HA Core reachable | `curl localhost:8123/manifest.json` | ✅ PASS |
| HA API with token | needs HA token | ❌ MISSING TOKEN |
| Zone Cards Lovelace | browser check | ❌ NOT DONE |
| Webhook Delivery | smoke test | ❌ NOT DONE |
| Dashboard Flask (8766) | `curl localhost:8766` | ❌ NOT LISTENING |
| addon_restart needed | needs Supervisor API | ❌ NO TOKEN |

---

## ACTION ITEMS

### Must Have for v15.0 Live Test:
1. **HA API Token** — um Live-Entity-States zu lesen
2. **Addon Restart** — um `14.7.5` / `v14.9.0` tatsächlich zu aktivieren (Docker-Container läuft noch auf `14.7.3`)
3. **`area_zone_map.json` verify** — sind die 10 Mappings in HA Entities übersetzt?

### Questions to resolve:
- **PilotClaw**: Was ist die genaue HA Core Version? (Input: sensor readings)
- **Andreas**: HA Token verfügbar?

---

## SMOKE TEST COMMAND REFERENCE

```bash
# Core Health
curl -s http://localhost:8909/api/v1/health | python3 -m json.tool

# Core Zones
curl -s http://localhost:8909/api/v1/zones | python3 -m json.tool

# HA Core reachable
curl -s http://localhost:8123/manifest.json | python3 -m json.tool

# HA addon versions (if Supervisor API available)
curl -s -H "Authorization: Bearer $HA_TOKEN" http://localhost:8123/api/hassio/addons

# Dashboard Flask
curl -s http://localhost:8766/  # should NOT respond (not running)
```

---

*Liveness-Check durchgeführt: HomeClaw Lane, 2026-03-21 14:50*
