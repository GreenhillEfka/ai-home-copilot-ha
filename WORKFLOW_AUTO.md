# WORKFLOW_AUTO.md — VERSION SYNC CHECKLISTE

**Version:** 13.0.3  
**Last Updated:** 2026-03-03 12:21  
**Status:** ✅ ALLE VERSIONEN SYNCHRONISIERT

---

## PRE-RELEASE VERSION SYNC CHECKLISTE

Vor jedem Release MUSS folgende Checkliste durchlaufen werden:

### 1. Core Repository (pilotsuite-styx-core)

- [ ] `copilot_core/config.yaml` → `version: "X.Y.Z"`
- [ ] `copilot_core/manifest.json` → `"version": "X.Y.Z"`
- [ ] `VERSION` (root) → `vX.Y.Z`
- [ ] `copilot_core/rootfs/usr/src/app/VERSION` → `X.Y.Z`
- [ ] `CHANGELOG.md` → Aktueller Eintrag für X.Y.Z vorhanden

**Befehl zur Verifikation:**
```bash
cd /config/.openclaw/workspace/pilotsuite-styx-core
echo "config.yaml: $(grep '^version:' copilot_core/config.yaml)"
echo "manifest.json: $(grep '"version":' copilot_core/manifest.json | head -1)"
echo "VERSION (root): $(cat VERSION)"
echo "VERSION (app): $(cat copilot_core/rootfs/usr/src/app/VERSION 2>/dev/null || echo 'N/A')"
```

### 2. HA Repository (pilotsuite-styx-ha)

- [ ] `custom_components/copilot_ha/manifest.json` → `"version": "X.Y.Z"`
- [ ] `VERSION` → `vX.Y.Z`
- [ ] `dashboard/app.py` → `'version': 'X.Y.Z'` (Zeile ~100)
- [ ] `dashboard/api/v1/dashboard.py` → `'version': 'X.Y.Z'` (Zeile ~144)
- [ ] `docs/openapi.yaml` → `version: X.Y.Z` (Zeile ~26)
- [ ] `docs/openapi-phase5-6.yaml` → `version: X.Y.Z` (Zeile ~21)
- [ ] `CHANGELOG.md` → Aktueller Eintrag für X.Y.Z vorhanden

**Befehl zur Verifikation:**
```bash
cd /config/.openclaw/workspace/pilotsuite-styx-ha
echo "manifest.json: $(grep '"version":' custom_components/copilot_ha/manifest.json)"
echo "VERSION: $(cat VERSION)"
echo "dashboard/app.py: $(grep -n "'version'" dashboard/app.py | head -1)"
echo "dashboard/api: $(grep -n "'version'" dashboard/api/v1/dashboard.py | head -1)"
echo "openapi.yaml: $(grep -n '^  version:' docs/openapi.yaml | head -1)"
echo "openapi-phase5-6: $(grep -n '^  version:' docs/openapi-phase5-6.yaml | head -1)"
```

### 3. Cross-Repo Sync

- [ ] Core version == HA version
- [ ] Keine v12.x Referenzen in aktiven Code-Files (nur CHANGELOG erlaubt)
- [ ] Git status clean in beiden Repos
- [ ] Alle Commits gepusht

### 4. Duplicate Add-on Check

**KRITISCH:** Stellen Sie sicher, dass es KEINE duplicate addon definitions gibt:

```bash
# Check für duplicate slugs in HA repo
grep -r "slug: copilot_core" /config/.openclaw/workspace/pilotsuite-styx-ha/ --include="*.yaml" --include="*.json"
# Erwartet: KEINE Ergebnisse

# Check für duplicate slugs in Core repo
grep -r "slug: copilot_core" /config/.openclaw/workspace/pilotsuite-styx-core/ --include="*.yaml" --include="*.json"
# Erwartet: GENAU 1 Ergebnis (in copilot_core/config.yaml)
```

### 5. Home Assistant Verification (Post-Release)

Nach dem Push:

1. HA → Supervisor → Add-on Store
2. Drei-Punkte-Menü → "Check for updates"
3. Verifiziere: Nur EIN "PilotSuite Core" Add-on wird angezeigt
4. Verifiziere: Version zeigt X.Y.Z
5. Optional: HA neu starten für kompletten Cache-Clear

---

## ROOT CAUSE: WARUM VERSION SYNC WICHTIG IST

**Problem (v13.0.0 vs v13.0.3):**
Home Assistant liest Version-Informationen aus mehreren Quellen:
- Add-on Repository (config.yaml)
- Add-on Manifest (manifest.json)
- HA Integration (manifest.json)

Bei Drift zeigt HA:
- ❌ Inkonsistente Versionen
- ❌ Temporär doppelte Einträge während Repository-Scans
- ❌ Falsche "Update available" Hinweise

**Lösung:** Alle Versionen MÜSSEN synchron sein.

---

## HISTORISCHE VERSION MISMATCHES (v12.x)

Folgende Mismatches traten in v12.x auf (bereits behoben):

| Version | Issue | Fix |
|---------|-------|-----|
| v12.8.0 | Dashboard zeigte 12.8.0, Core war 12.9.0 | Sync in v13.0.0 |
| v12.15.0 | manifest.json vs config.yaml Drift | Sync in v13.0.0 |
| v12.17.0 | HA Integration vs Core Drift | Sync in v13.0.0 |
| v13.0.0 | manifest.json: 13.0.0 vs config.yaml: 13.0.3 | Fix in Commit cc8b227 |

**Lesson Learned:** Version-Sync-Checkliste vor JEDEM Release durchlaufen.

---

## AUTOMATISIERUNG

### Pre-Release Script (Empfohlen)

Erstelle ein Script `scripts/version_sync_check.sh`:

```bash
#!/bin/bash
# Version Sync Check Script

CORE_ROOT="/config/.openclaw/workspace/pilotsuite-styx-core"
HA_ROOT="/config/.openclaw/workspace/pilotsuite-styx-ha"

echo "=== VERSION SYNC CHECK ==="

# Core Versionen
CORE_CONFIG=$(grep '^version:' $CORE_ROOT/copilot_core/config.yaml | cut -d'"' -f2)
CORE_MANIFEST=$(grep '"version":' $CORE_ROOT/copilot_core/manifest.json | head -1 | cut -d'"' -f4)
CORE_VERSION_ROOT=$(cat $CORE_ROOT/VERSION | sed 's/v//')

echo "Core config.yaml: $CORE_CONFIG"
echo "Core manifest.json: $CORE_MANIFEST"
echo "Core VERSION: $CORE_VERSION_ROOT"

# HA Versionen
HA_MANIFEST=$(grep '"version":' $HA_ROOT/custom_components/copilot_ha/manifest.json | cut -d'"' -f4)
HA_VERSION=$(cat $HA_ROOT/VERSION | sed 's/v//')

echo "HA manifest.json: $HA_MANIFEST"
echo "HA VERSION: $HA_VERSION"

# Sync Check
if [ "$CORE_CONFIG" = "$CORE_MANIFEST" ] && [ "$CORE_CONFIG" = "$CORE_VERSION_ROOT" ] && \
   [ "$HA_MANIFEST" = "$HA_VERSION" ] && [ "$CORE_CONFIG" = "$HA_MANIFEST" ]; then
    echo "✅ ALLE VERSIONEN SYNCHRONISIERT"
    exit 0
else
    echo "❌ VERSION MISMATCH DETEKTIERT"
    exit 1
fi
```

---

## AKTUELLER STATUS (2026-03-03 12:21)

✅ **ALLE VERSIONEN AUF 13.0.3 SYNCHRONISIERT**

- Core config.yaml: 13.0.3 ✅
- Core manifest.json: 13.0.3 ✅
- Core VERSION: v13.0.3 ✅
- HA manifest.json: 13.0.3 ✅
- HA VERSION: v13.0.3 ✅
- Dashboard: 13.0.3 ✅
- OpenAPI Docs: 13.0.3 ✅

**Duplicate Add-on Definitions:** ❌ KEINE VORHANDEN

**Nächster Check:** Vor Release v13.1.0

---

**Dokumentation erstellt:** 2026-03-03 12:21 (Europe/Berlin)  
**Autor:** @clawdya (basierend auf PATH_AUDIT_FINAL_2026-03-03_1221.md)
