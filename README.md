# PilotSuite Home Assistant Integration v1.0.0

Die offizielle Integration zur Anbindung des PilotSuite Core an Home Assistant.

## Features
- **UI-Konfiguration:** Host und Token bequem über den HA Config Flow einrichten.
- **Auto-Discovery (Core-Level):** Findet automatisch alle aktiven Module und Zonen.
- **Echtzeit-Sensoren:**
  - `sensor.pilotsuite_module_*`: Status (active/learning/off)
  - `sensor.pilotsuite_zone_*`: Zonen-Status & Modul-Belegung
  - `sensor.pilotsuite_system_health`: CPU, RAM, Disk, Uptime
- **Auth-Support:** Sicherer Zugriff via Bearer-Token.

## Installation via HACS
1. HACS öffnen → Integrationen.
2. Drei Punkte oben rechts → Benutzerdefinierte Repositories.
3. URL: `https://github.com/pilotsuite/homeassistant` hinzufügen.
4. "PilotSuite" suchen und installieren.

## Konfiguration
Nach der Installation unter **Einstellungen → Geräte & Dienste → Integration hinzufügen** nach "PilotSuite" suchen und die URL deines Cores (Standard: `http://localhost:5000`) sowie optional den Token eingeben.

---
**Status:** ✅ Production Ready
**API-Version:** v1
**HACS-Ready:** Yes
