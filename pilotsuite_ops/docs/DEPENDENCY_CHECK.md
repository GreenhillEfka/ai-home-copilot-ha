# Dependency Check — PS-052

## Stand: 2026-03-20

## HA Integration (manifest.json)

| Dependency | Version | Latest | Kritikalität | Status |
|---|---|---|---|---|
| homeassistant | 2024.4.0 | 2026.x | HIGH | ⚠️ Update empfohlen (HA 2024.4已经很旧) |
| requirements | [] | — | — | ✅ Keine externen pip deps |

## Dashboard (package.json)

| Dependency | Version | Latest | Kritikalität | Status |
|---|---|---|---|---|
| (keine) | — | — | — | ✅ Keine npm deps |

## Add-on (addon/config.json)

| Dependency | Kritikalität | Status |
|---|---|---|
| Keine externen deps definiert | — | ✅ |

## Analyse

HA-Integration ist minimal:
- **0 pip requirements** ausser HA selbst
- **0 npm dependencies** im Dashboard
- Add-on hat keine externen Abhängigkeiten

## Risiken

1. **HomeAssistant 2024.4.0** — Mindestversion. Neuere HA-Versionen können APIs ändern. Prüfe regelmässig Compatibility.
2. **Socket.IO** (CDN) — wird von CDN geladen, nicht als lokale Dep.版本 über CDN URL spezifiziert.

## Empfehlungen

- HA Mindestversion auf 2025.x anheben wenn möglich
- Regelmässige HA Compatibility-Checks bei Core-Updates
