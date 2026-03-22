# PilotAgent — HA Add-on

Dieses Add-on bringt einen OpenClaw-Agenten direkt auf den HA-Host.

## Installation

1. ZIP von diesem Repository herunterladen:  
   `https://github.com/GreenhillEfka/pilotsuite-styx-ha/tree/main/addons/pilot-agent`
2. In HA: Settings → Add-ons → + Add-on → "Lokale Add-ons" → ZIP laden
3. Add-on starten mit Token zum bestehenden Gateway

## Was es kann (auf dem HA-Host)

- `/config/custom_components/` lesen und schreiben
- HA API direkt aufrufen (alle Integrationsdateien)
- SSH/SMB zu allen LAN-Geräten
- Root-Zugang zum HA-Dateisystem
- Direkter Zugang zu allen Ports im LAN

## Gateway Pairing

Beim Start verbindet sich der Agent mit dem bestehenden OpenClaw Gateway.
