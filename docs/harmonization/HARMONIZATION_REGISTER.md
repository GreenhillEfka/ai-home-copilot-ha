# Deep Harmonization Register — Cross-Module Logic

**Created:** 2026-04-06 22:20 Europe/Berlin
**Owner:** openclaw-main (Orakel)
**Purpose:** Zentrale Dokumentation aller Cross-Module-Integrationen

---

## 📋 HARMONIZATION MATRIX

| Module A | Module B | Integration | Status | Priority |
|----------|----------|-------------|--------|----------|
| Licht | Klima | Adaptive CCT basierend auf Heizstatus | 🔄 In Arbeit | P0 |
| Präsenz | Alarm | Dynamic Thresholds bei low confidence | 🔄 In Arbeit | P0 |
| Musik | Notification | Ducking-Effekt bei Sprachansagen | 🔄 In Arbeit | P0 |
| Musikwolke | Sonnenwecker | Auto-Pause/Resume (Sleep-Mode) | ✅ COMPLETE | P1 |
| Sonos | Habituszonen | Zone-based Favorites + Follow | ✅ COMPLETE | P1 |
| Presence | HVAC | Occupancy-based Climate Control | ⏳ Pending | P2 |
| Alarm | Lighting | Sunrise-Sync mit Wecker | ⏳ Pending | P2 |

---

## 🔧 IMPLEMENTATION STATUS

### P0 — Kritische Integrationen

#### 1. Licht/Klima — Adaptive CCT
**Ziel:** Farbtemperatur passt sich Heizstatus an
- **Heizt:** Warmes Licht (2700K-3000K) für Komfort-Gefühl
- **Kühlt:** Kühles Licht (4000K-5000K) für Frische-Gefühl
- **Neutral:** Standard (3500K)

**Implementation:**
- File: `copilot_core/modules/cross_module/light_climate_sync.py`
- Trigger: HVAC state change
- Action: Light CCT adjustment via `light.turn_on`

#### 2. Präsenz/Alarm — Dynamic Thresholds
**Ziel:** Sensiblere Alarm-Schwellen bei niedriger Präsenz-Confidence

**Logic:**
```
if presence_confidence < 0.5:
    alarm_sensitivity += 20%
    motion_threshold -= 15%
elif presence_confidence > 0.8:
    alarm_sensitivity = baseline
    motion_threshold = baseline
```

**Implementation:**
- File: `copilot_core/modules/cross_module/presence_alarm_sync.py`
- Trigger: Presence confidence update
- Action: Alarm threshold adjustment

#### 3. Musik/Notification — Ducking
**Ziel:** Automatische Lautstärke-Reduktion bei Sprachansagen

**Logic:**
```
on_notification_start:
    current_volume = get_music_volume()
    set_music_volume(current_volume * 0.3)  # 70% reduction
    play_notification()
on_notification_end:
    restore_music_volume()  # Fade-in over 2s
```

**Implementation:**
- File: `copilot_core/modules/cross_module/music_notification_duck.py`
- Trigger: TTS/Notification start
- Action: Volume ducking + restore

---

## 📊 BACKLOG QUESTIONS (AUTONOMOUS RESOLUTION)

| ID | Question | Decision | Rationale |
|----|----------|----------|-----------|
| HQ1 | UI-Sichtbarkeit für Harmonization-Rules? | ✅ JA, im Admin-UI | Transparenz + Debugging |
| HQ2 | Welche HVAC-Entities für Heizstatus? | ⏳ Pending HomeClaw | Entity-List benötigt |
| HQ3 | Presence-Confidence-Entities vorhanden? | ⏳ Pending HomeClaw | Entity-List benötigt |
| HQ4 | Notification-Channels mit Ducking? | ⏳ Pending HomeClaw | TTS-Entities benötigt |
| HQ5 | Cross-Module-Config zentral oder dezentral? | ✅ ZENTRAL | `cross_module_config.yaml` |

---

## 🚀 NEXT STEPS

1. **HomeClaw Response abwarten** — Entity-Lists für alle 3 Bereiche
2. **DesignClaw UI-Spec** — Admin-UI Komponenten für Harmonization
3. **Implementation abschließen** — Alle 3 P0-Integrationen
4. **Testing** — Integrationstests für Cross-Module-Logic
5. **Documentation** — User Guide für Harmonization-Features

---

*Last Updated: 2026-04-06 22:20 Europe/Berlin*
*Next Review: 2026-04-06 22:30 Europe/Berlin (10min)*
