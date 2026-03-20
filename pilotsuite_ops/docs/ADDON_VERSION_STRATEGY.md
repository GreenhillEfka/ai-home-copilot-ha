# ADDON_VERSION_STRATEGY.md

**Task:** PS-061 — Add-on-Version-Semantik klären  
**Erstellt:** 2026-03-20  
**Agent:** PilotClaw (Subagent)  
**Status:** ✅ ABGESCHLOSSEN

---

## 1. Ausgangslage

Es gab Unklarheit, ob die Add-on-Version `v13.9.0` im Core-`addon/config.json` bewusst stehen bleibt oder auf `v14.7.x` gezogen werden darf. Die Frage betrifft die Versionierungsstrategie über zwei getrennte Produkte hinweg.

---

## 2. Befundlage (Evidence)

### 2.1 Geprüfte Artefakte

| Artefakt | Pfad | Version | Funktion |
|----------|------|---------|----------|
| HA `manifest.json` | `custom_components/copilot_ha/manifest.json` | `14.7.5` | HA-Add-on-Version (HACS) |
| HA `VERSION` | `custom_components/copilot_ha/VERSION` | `14.7.5` | Python-Paket-Version |
| HA `hacs.json` | `hacs.json` | *(kein `version`-Feld)* | HACS-Metadaten, kein Version-Feld |
| Core `addon/config.json` | `copilot_core/rootfs/usr/src/app/addon/config.json` | `v13.9.0` | **Home Assistant Add-on (OS)** |
| Core `VERSION` | `copilot_core/VERSION` | `14.7.3` (prep) / `14.7.4` (current) | Core-Release-Version |

### 2.2 HACS `hacs.json` — Kein `version`-Feld

```json
{
  "name": "PilotSuite",
  "content_in_root": false,
  "render_readme": true,
  "homeassistant": "2024.1.0"
}
```

**Befund:** `hacs.json` führt bewusst kein `version`-Feld.  
**Begründung:** HACS erwartet die Version ausschließlich aus `manifest.json`. Das `hacs.json`-Metadatenfile steuert nur Darstellung, Region und Domain-Whitelist.

### 2.3 Drei Produkte, drei Versionierungsstränge

```
PilotSuite
├── pilotsuite-styx-ha (dieses Repo)
│   ├── custom_components/copilot_ha/     ← HA-Integration (HACS)
│   │   ├── manifest.json   version=14.7.5 ← HACS-Versionierbar
│   │   └── VERSION        version=14.7.5
│   └── pilotsuite_ops/
│
└── pilotsuite-styx-core (anderes Repo)
    └── copilot_core/rootfs/usr/src/app/addon/
        └── config.json  version=v13.9.0  ← HA-OS-Add-on (nicht HACS)
```

**Kritische Unterscheidung:**

| Produkt | Vertriebsweg | Versionsquelle |
|---------|-------------|----------------|
| HA-Integration (`copilot_ha`) | HACS | `manifest.json` `version` |
| Core Add-on (`addon/config.json`) | HA-OS Add-on Store | `config.json` `version` |

Das Core Add-on (`v13.9.0`) ist ein **separates Docker-Container-Add-on** für Home Assistant OS. Es hat ein eigenes Versionsregime und wird **nicht über HACS ausgeliefert**.

### 2.4 Release-Gate-Dokumentation (RELEASE_GATE_14_7_5.md)

Das bestehende Release Gate dokumentiert den Stand präzise:

- HA `manifest.json`: `14.7.5` ✅
- Core prep `VERSION`: `14.7.3` ❌ (sollte `14.7.5` sein)
- Core current `VERSION`: `14.7.4` ❌
- HA-Changelog vermerkt: *"Paired Core v14.7.5 release is still pending"*

---

## 3. Analyse: Darf Core-Addon-Version auf v14.7.x gezogen werden?

### 3.1 Kurze Antwort

**Das Core Add-on (`v13.9.0`) ist NICHT der Blocker für HA v14.7.5.**

Es handelt sich um zwei vollständig unabhängig versionierte Produkte:
- HA-Integration: bereits auf `14.7.5` (HACS)
- Core Add-on: steht auf `v13.9.0` (OS Add-on Store)

### 3.2 Warum v13.9.0 im Core Add-on?

Das ist **kein Versehen, sondern korrekt** — es reflektiert den Stand des letzten Common Release. Das Core Add-on führt seine eigene semantische Version und wird nur dann erhöht, wenn Core-seitig ein neues Add-on-Release gebaut wird.

Die Frage „darf ich auf v14.7.x ziehen" ist daher:
- **Für HA-Integration:** bereits passiert (`manifest.json` = `14.7.5`)
- **Für Core Add-on:** Noch nicht freigegeben — RELEASE_GATE G1 blockiert, Core-Release-Prep muss `VERSION` auf `14.7.5` setzen und CHANGELOG-Eintrag erstellen

### 3.3 Was passiert, wenn Core Add-on auf v14.7.x geht?

Das ist ein **Core-Release-Event**, kein HA-Event. Voraussetzungen:
1. Core `VERSION` → `14.7.5` setzen
2. Core `CHANGELOG.md` → `[v14.7.5]` Eintrag mit HA-Referenz
3. Core-seitige Änderungen für PS-171, PS-136 verifizieren
4. Add-on-Build + OS-Add-on-Store Upload

Danach ist das Paired Release komplett: `HA v14.7.5 <-> Core v14.7.5`

---

## 4. Strategische Implications

| Entscheidung | Gilt für | Status |
|-------------|----------|--------|
| HA-Integration auf `14.7.5` | `manifest.json`, `VERSION` | ✅ Bereits done (HACS) |
| Core Add-on auf `14.7.x` | `addon/config.json` | ⏳ Blockiert durch Core-Release-Gate |
| HACS-Version = `14.7.5` | `manifest.json` | ✅ Korrekt |
| `hacs.json` Version-Feld | — | ❌ Existiert nicht, kein Handlungsbedarf |

---

## 5. Empfehlung

### Sofort (HA-Repo — kein Blocker):
- `manifest.json` Version `14.7.5` ist korrekt ✅
- `VERSION` Datei `14.7.5` ist korrekt ✅
- `hacs.json` braucht kein Version-Feld — HACS liest es aus `manifest.json` ✅

### Mittelfristig (Core-Release-Prep —offener Blocker):
- Core `VERSION` auf `14.7.5` setzen
- Core `CHANGELOG.md` Eintrag `[v14.7.5]` erstellen
- Add-on/`config.json` Version auf `v14.7.5` aktualisieren
- RELEASE_GATE G1+G2 nachholen

---

## 6. Tasklog-Report

```
Task:        PS-061 — Add-on-Version-Semantik klären
Agent:      PilotClaw (Subagent, depth 1/1)
Kanal:      telegram (group -1003815316785)
Session:     agent:pilotclaw:subagent:9d79e867-e06c-44e1-9f44-c5c75c3d9ccb
Gestartet:   2026-03-20 19:34 GMT+1
Abgeschlossen: 2026-03-20 19:36 GMT+1

Befund:
  • hacs.json: kein version-Feld (HACS-spec-konform)
  • manifest.json: 14.7.5 (HACS-Versionierbar)
  • VERSION: 14.7.5
  • Core addon/config.json: v13.9.0 (separates Produkt, eigenes Regime)

Entscheidung:
  HA-Integration v14.7.5 ist frei für HACS-Release
  Core Add-on v13.9.0 ist NICIT der Blocker
  Core-Addon-Update auf v14.7.x ist Core-Release-Prep-Sache

Output:
  pilotsuite_ops/docs/ADDON_VERSION_STRATEGY.md erstellt
```

---

*Evidence-Quelle: Alle Befunde direkt aus Quellfiles im Worktree `pilotsuite-styx-ha-release-prep-v14.7.3` und Repo `pilotsuite-styx-ha` entnommen.*
