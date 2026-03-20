# PS-088 FACS — HA Kamera-Integration Spezifikation

## Context

FACS (Facial Analysis/Recognition Camera System) muss als optionales Core-Modul mit Home-Assistant-Kameraauswahl sauber angebunden werden.

## Architektur

```
HA (copilot_ha)          Core (Stxy)
────────────────────     ──────────────
Kamera-Entity-Auswahl    FACS Core-Modul
                          ↕ (Core API)
Frigate / generisch    ←  Recognition Engine
motion/presence Events  ←  person_id + embedding
```

## HA-Seite: Was gebaut werden muss

### 1. Camera Selection Flow

FACS benötigt eine UI in HA um Camera-Entities auszuwählen die für Gesichtserkennung genutzt werden sollen.

**Option A:** Über das existierende `zone_auto_setup` Flow — Cameras werden als entities erkannt und können Zone-spezifisch zugeordnet werden.

**Option B:** Eigenes ConfigFlow für FACS-Einrichtung mit Multi-Entity-Selektor.

### 2. ConfigFlow für FACS

```python
# custom_components/copilot_ha/config_facs_flow.py

class FACSConfigFlow(HubAccessFlowHandler, domain=DOMAIN):
    """ConfigFlow für FACS Kamera-Auswahl."""
    
    async def async_step_init(...):
        # Kamera-Entity-Multi-Select
        # Area-Zuordnung pro Kamera
        # Recognition sensitivity (low/medium/high)
```

### 3. Entity Naming Convention

| Kamera | Zone | FACS-Entity |
|---|---|---|
| camera.eingang | zone:wohnbereich | binary_sensor.facs_eingang_person |
| camera.terrasse | zone:aussenbereich | binary_sensor.facs_terrasse_person |

### 4. Events an Core

```python
# Wenn FACS eine Person erkennt:
{
    "event": "facial_recognition",
    "camera": "camera.eingang", 
    "person_id": "person.alice",  # oder "unknown"
    "confidence": 0.94,
    "timestamp": "2026-03-20T19:30:00Z"
}
```

### 5. Offene Fragen (für Stxy)

1. Welches Face-Recognition-Backend? (Frigate内置, face_recognition, orfien)
2. person_id Mapping — wie werden Gesichter zu Personen?
3. Core FACS-Modul Endpoint — welcher?

## Nächste Schritte

| Owner | Action |
|---|---|
| Stxy | FACS Core-Modul implementieren + Endpoint definieren |
| PilotClaw | HA ConfigFlow für Kamera-Auswahl |
| PilotClaw | Event-Pipeline HA → Core FACS Endpoint |
| PilotDesign | FACS Dashboard Card |
