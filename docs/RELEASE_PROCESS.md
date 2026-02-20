# AI Home CoPilot - Secure Release Process

## Philosophie

> **"Never merge unverified code. Never release without tests. Never lose the red line."**

Dieser Prozess stellt sicher, dass jeder Release **sicher**, **sauber** und **reproduzierbar** ist.

---

## Entwicklungs-Phasen

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  PHASE 1: DEVELOPMENT                                                       │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │ • Feature-Entwicklung auf Feature-Branches (wip/*)                   │   │
│  │ • Lokale Tests schreiben                                             │   │
│  │ • Self-Review vor Commit                                             │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                    ↓                                       │
│  PHASE 2: VERIFICATION                                                     │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │ • Pull Request erstellen                                            │   │
│  │ • CI/CD Tests laufen lassen (glm-5:cloud + deepseek-r1:latest)       │   │
│  │ • Code Review durch Ollama Cloud Modelle                             │   │
│  │ • Architecture Check                                                 │   │
│  │ • Dependencies Audit                                                 │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                    ↓                                       │
│  PHASE 3: MERGE                                                            │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │ • Review-Fixes einarbeiten                                          │   │
│  │ • Squash & Merge nach dev/autopilot-YYYY-MM-DD                      │   │
│  │ • CHANGELOG.md aktualisieren                                        │   │
│  │ • Activity loggen                                                   │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                    ↓                                       │
│  PHASE 4: RELEASE                                                          │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │ • Version bump (semver)                                              │   │
│  │ • Final Integration Test                                            │   │
│  │ • Tag erstellen                                                     │   │
│  │ • CHANGELOG.md finalisieren                                        │   │
│  │ • Release Notes schreiben                                           │   │
│  │ • Beide Repos sync (HA Integration + Core Add-on)                   │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Branching-Strategie

```
main (production)
  │
  ├── dev/autopilot-YYYY-MM-DD (staging, 1 pro Tag max)
  │     │
  │     └── wip/feature-XXX (feature branches)
  │
  └── releases/v0.X.Y (release branches, protected)
```

### Naming Conventions

| Branch-Typ | Beispiel | Zweck |
|------------|----------|-------|
| Feature | `wip/feature-brain-graph-v2` | Neue Features |
| Bugfix | `wip/fix-import-error` | Fehlerbehebungen |
| Dev-Staging | `dev/autopilot-2026-02-14` | Tägliche Integration |
| Release | `releases/v0.6.2` | Release-Kandidaten |

---

## Verifizierungs-Checkliste (Pflicht vor Merge)

### ✅ Code Quality
- [ ] `py_compile` erfolgreich
- [ ] Keine lint errors
- [ ] Typ-Hints vorhanden (wo sinnvoll)
- [ ] Docstrings für alle public functions

### ✅ Testing
- [ ] Unit Tests geschrieben (min 80% Coverage für neue Module)
- [ ] Integration Tests für API Endpoints
- [ ] Manuelle Tests für HA Entities (wenn nötig)

### ✅ Architecture
- [ ] Basisklassen konsistent genutzt
- [ ] Imports korrekt aufgelöst
- [ ] Keine circular dependencies
- [ ] Module-Struktur eingehalten

### ✅ Security
- [ ] Keine hardcoded secrets
- [ ] Input validation
- [ ] Error handling robust

### ✅ Documentation
- [ ] CHANGELOG.md Eintrag
- [ ] README.md aktualisiert (wenn nötig)
- [ ] API Docs aktualisiert

---

## Review-Prozess (Ollama Cloud)

### Automatische Reviews (pro PR)

| Check | Modell | Zweck |
|-------|--------|-------|
| Code Quality | `glm-5:cloud` | Style, Patterns, Best Practices |
| Security | `deepseek-r1:latest` | Vulnerabilities, Secrets |
| Architecture | `deepseek-r1:latest` | Struktur, Dependencies |
| Tests | `glm-5:cloud` | Coverage, Quality |

### Manual Review (kritische Änderungen)

- Breaking Changes → **Immer User bestätigen lassen**
- Architecture-Änderungen → **Kritische Nachfrage**
- Neue Dependencies → **Immer nachfragen**

---

## Release-Kriterien (Wann ist ein Release "ready"?)

### Must-Haves

- [ ] Alle CI/CD Tests grün
- [ ] Keine offenen critical/high Bugs
- [ ] Code Review bestanden
- [ ] CHANGELOG.md vollständig
- [ ] Beide Repos sync (HA Integration + Core Add-on)

### Should-Haves

- [ ] 100% Coverage für kritische Pfade
- [ ] Performance-Tests bestanden
- [ ] Manuelle QA abgeschlossen

### Nice-to-Haves

- [ ] Screenshots/Demo verfügbar
- [ ] Release-Video

---

## Versionierung

### Semantic Versioning

```
v0.MAJOR.MINOR
```

| Teil | Increment bei |
|------|---------------|
| MAJOR | Breaking Changes |
| MINOR | Neue Features (backwards compatible) |
| PATCH | Bugfixes |

### Beide Repos synchron

| HA Integration | Core Add-on |
|----------------|-------------|
| v0.6.1 | v0.4.1 |
| v0.6.2 | v0.4.2 |
| v0.7.0 | v0.5.0 |

---

## Activity Logging (Pflicht)

### Bei jedem Merge

```
Type: merge
Title: 🔀 [Feature] Feature Name merged
Description: Branch wip/feature-XXX → dev/autopilot-YYYY-MM-DD
Badge: 🔀
```

### Bei jedem Release

```
Type: release
Title: 🚀 v0.6.1 RELEASED
Description: [Kurzbeschreibung der Änderungen]
Badge: 🚀
```

---

## Rollback-Prozess

### Wenn ein Release kritische Bugs hat

```
1. Bug identifizieren und dokumentieren
2. Severity einschätzen (critical/high/medium/low)
3. Wenn critical:
   a. Tag löschen (wenn möglich)
   b. Hotfix-Branch erstellen: hotfix/v0.X.Y-fix
   c. Bug beheben
   d. Schnell-Review + Merge
   e. v0.X.1 release
4. Post-Mortem schreiben
```

---

## Dashboard-Integration

### React Board Updates (pro Phase)

| Phase | Action |
|-------|--------|
| Feature-Start | Task erstellen, Status: in-progress |
| PR-Erstellung | Activity loggen |
| Merge | Task auf done, Activity loggen |
| Release | Version bump, Task auf done, Activity loggen |

---

## Kommunikation

### Bei Unsicherheit - IMMER NACHFRAGEN

| Situation | Aktion |
|----------|--------|
| Unklarer Requirement | Nachfragen bevor Code geschrieben wird |
| Architecture-Änderung | Optionen präsentieren, User wählen lassen |
| Breaking Change | Deutlich markieren, Bestätigung einholen |
| Neue Dependency | Recherche, Empfehlung, Bestätigung |
| Riskante Änderung | Pro und Contra aufzeigen |

---

## Daily Workflow

### Jeder Tag

```
1. Morning: Prüfe open PRs und active Branches
2. Review: Starte Reviews für wartende PRs
3. Merge: Führe verifizierte Features zusammen
4. Verify: Starte Integration Tests
5. Log: Activities und Progress tracken
6. Plan: Nächste Schritte identifizieren
```

### Wöchentlich

```
- Montag: Sprint Review + Planning
- Dienstag-Freitag: Feature Development
- Samstag: Release Preparation
- Sonntag: Relax & Learn
```

---

## Metrics

### Tracken für kontinuierliche Verbesserung

| Metric | Ziel |
|--------|------|
| Merge-to-Release Time | < 24h für Patches, < 1 Woche für Features |
| Bug-Rate post-Release | < 2 critical Bugs pro Release |
| Test Coverage | > 80% overall, > 90% für neue Module |
| Review Time | < 4h für Patches, < 24h für Features |

---

*Letzte Aktualisierung: 2026-02-14*
*Verantwortlich: Project Agents*
