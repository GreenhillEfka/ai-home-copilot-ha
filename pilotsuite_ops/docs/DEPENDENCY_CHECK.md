# Dependency Check — PS-052

## Stand: 2026-03-20

## 🔴 CRITICAL BLOCKER

**`pilotsuite_core/manifest.json`** — sofortige Handlung erforderlich:

| Package | Version | Issue | Severity |
|---|---|---|---|
| `requests` | 2.31.0 | Bekannte CVE-Sicherheitslücken | 🔴 CRITICAL |
| `aiohttp` | 3.9.1 | Bekannte CVE-Sicherheitslücken | 🔴 CRITICAL |

## Dashboard (package.json)

| Dependency | Version | Latest | Issue | Status |
|---|---|---|---|---|
| esbuild | ≤0.24.2 | aktuell | GHSA-67mh-4wv8-2f99 CORS-Security-Lücke | 🔴 Update nötig |
| express | 4.x | 5.x | Breaking Changes | ⚠️ Testen |

## Core (manifest.json)

| Dependency | Version | Latest | Status |
|---|---|---|---|
| requests | 2.31.0 | aktuell | 🔴 CRITICAL — unsichere Version |
| aiohttp | 3.9.1 | aktuell | 🔴 CRITICAL — unsichere Version |
| neo4j | 5.x | 6.x | ⚠️ Major Upgrade, Breaking Changes |
| numpy | 1.x | 2.x | ⚠️ Major Upgrade, Breaking Changes |

## HA Mindestversionen

| Manifest | Aktuell | Sollte sein | Status |
|---|---|---|---|
| HA Integration | 2024.4.0 | 2025.x | ⚠️ Veraltet |
| Add-on Config | 2024.1 | 2025.x | ⚠️ Veraltet |

## Zusammenfassung

| Kategorie | Count |
|---|---|
| Total Dependencies analysiert | 16+ |
| Critical Blocker | 2 (requests, aiohttp) |
| Major Upgrades nötig | 4 (esbuild, neo4j, numpy, express) |
| HA Version veraltet | 2 Manifests |

## Handlungsplan

1. **Sofort**: `requests` und `aiohttp` in Core auf sichere Versionen
2. **Kurzfristig**: `esbuild` im Dashboard auf >0.24.2
3. **Geplant**: Major Upgrades (neo4j 5→6, numpy 1→2, express 4→5) isoliert testen
4. **Geplant**: HA Mindestversionen auf 2025.x
