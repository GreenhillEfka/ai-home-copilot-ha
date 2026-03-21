# PilotSuite HA Add-on — Release Notes v15.0.0

**Datum:** 2026-03-21
**Version:** 15.0.0
**Minimale Home Assistant Version:** 2024.4.0
**Gepaart mit:** Core v15.0.0

---

## In Kuerze

v15.0.0 bringt PilotSuite auf Phase-7-Niveau: Production-Ready. Core-Connection jetzt transparent in HA Diagnostics. Confidence-Scores fuer Suggestions. Presence-Hold funktioniert in Lovelace. Keine UI-Illusionen — jede Aktion ist erklaerbar.

**Andreas kann jetzt auf einen Blick sehen:**
- Ist Core erreichbar? → `sensor.pilotsuite_core_connection`
- Wie oft hat API gefehlt? → `sensor.pilotsuite_api_failures`
- Wie aktuell sind die Daten? → `sensor.pilotsuite_poll_interval`

**Das Haus passt sich an — nicht umgekehrt.**

---

## Was ist neu

### Production Readiness — Endlich sichtbar

4 neue Sensoren in HA Developer Tools (EntityCategory.DIAGNOSTIC):

| Sensor | Zeigt |
|--------|-------|
| `sensor.pilotsuite_core_connection` | connected / degraded / disconnected |
| `sensor.pilotsuite_poll_interval` | Sekunden seit letztem Poll |
| `sensor.pilotsuite_api_failures` | Consecutive failures Richtung Core |
| `sensor.pilotsuite_modules_ready` | N/M Module geladen |

### Phase 7 — Tiered Module Lazy-Loading

- **TIER_EAGER** (3): legacy, brain_graph_sync, habitus_miner — immediate load
- **TIER_DEFERRED** (4): background load nach 5s HA Startup
- **TIER_ON_DEMAND** (26): load only on first access
- **Schema TTL Cache**: 1h refresh statt Single-Fetch

### UX — Human-in-the-loop

- **Suggestions:** Confidence % jetzt als farbcodiertes Badge sichtbar. Details-Expander zeigt Pattern + Lift.
- **Presence-Hold:** 3-State Pill in styx-zone-card.js — Auto (System) / An (Nutzer) / Aus (Ignorieren)
- **Zone Cards:** Hold-Pill-Row in Lovelace. Optimistic UI — sofort反映, kein Warten auf Server.

### CI — Sauber und schnell

- 500+ Tests green in < 20s
- Kein fake pytest-homeassistant package mehr
- pytest-asyncio Mode auto aktiviert

---

## Fuer wen ist dieses Release

| Rolle | Nutzen |
|-------|--------|
| **Andreas (Betreiber)** | Core-Connection transparent. API-Fehler zaehlbar. Poll-Intervall sichtbar. |
| **Tester** | Smoke + Live Test koennen starten. Alle Blocker aus v14.x behoben. |
| **Entwickler** | Saubere CI. Production-Grade Monitoring. |

---

## Upgrade-Hinweise

- **Home Assistant 2024.4.0+ erforderlich.**
- Presence-Hold: Toggle `show_presence_hold: true` in styx-zone-card.js Card-Config.
- Nach Update: Developer Tools → Sensoren → `pilotsuite_*` filtern.

---

## Kompatibilitaet

| Komponente | Version |
|---|---|
| PilotSuite HA Add-on | **15.0.0** |
| PilotSuite Core | **15.0.0** (Paired) |
| Home Assistant | **2024.4.0+** |
| Python | **3.11+** |

---

## VISION-Bezug

PilotSuite Vision (v14.6.5):

> "Das Haus soll sich Ihnen anpassen — nicht Sie sich Ihrem Zuhause."

v15.0.0 Operationalisiert:

- **Lebenslanger Begleiter:** Zone-Matching versteht deutsche Raeume (kinderzimmer, kueche, balkon)
- **Governance-first:** Presence-Hold = Nutzer entscheidet. Suggestions mit Confidence.
- **Privacy-first:** Alles lokal. Kein Cloud-Call.
- **Erklaerbar:** Jeder Suggestion hat Confidence. Core-Connection ist transparent.

---

## Getestet

| Check | Ergebnis |
|-------|----------|
| Python Syntax | ✅ alle .py kompilieren |
| pytest | ✅ 500+ passed |
| GitHub Actions CI | ✅ green in < 20s |

---

*PilotSuite HA v15.0.0 — Lokal. Lernend. Lebenslang.*
