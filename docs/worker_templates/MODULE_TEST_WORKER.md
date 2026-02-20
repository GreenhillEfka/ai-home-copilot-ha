# Module Test Worker Template

## Name
`module-test-{module}`

## Zweck
Führe Tests und Quality Checks für einzelne Module durch.

## Inputs
- Modul-Name aus Queue
- Spec-Datei (`docs/module_specs/{module}_v0.1.md`)
- Branch-Info

## Arbeitsweise

### 1. Vorbereitung
```bash
# Checkout des Modul-Branch
cd /config/.openclaw/workspace/ai_home_copilot_hacs_repo
git checkout {branch}

# py_compile für alle Python-Dateien
python3 -m py_compile custom_components/ai_home_copilot/{module_files}
```

### 2. Tests ausführen
```bash
# Wenn tests/ existiert
python3 -m pytest tests/test_{module}.py -v

# Ohne Tests: nur Import-Check
python3 -c "from custom_components.ai_home_copilot.{module_import}; print('OK')"
```

### 3. Review-Checkliste
- [ ] Alle Imports funktionieren
- [ ] Keine Syntax-Fehler
- [ ] manifest.json aktualisiert (falls nötig)
- [ ] CHANGELOG.md-Eintrag (falls nötig)
- [ ] Deutsche Übersetzungen (falls UI-Elemente)

### 4. Merge-Vorbereitung
```bash
# Wenn alles OK:
git checkout development
git merge {branch} --no-ff -m "merge: {Module Name} v0.1"

# Push vorbereiten (nicht pushen!)
git push origin development --dry-run
```

## Output
- Report: `notes/module_test_reports/{module}_latest.md`
- Status: `ready_for_user_ok` ODER `needs_fixes`

## Beispiel-Report

```markdown
# Module Test Report: mood_module

**Datum:** 2026-02-14
**Branch:** mood_module_dev_work
**Tester:** Module Test Worker

## Ergebnisse

| Check | Status |
|-------|--------|
| py_compile | ✅ OK |
| Imports | ✅ OK |
| Tests | ⚠️ 2 von 5 fehlgeschlagen |
| CHANGELOG | ✅ OK |

## Details

### Fehlgeschlagene Tests
- `test_mood_context_init` - fixture fehlt
- `test_mood_suggestion_filter` - timeout

## Empfehlung
❌ NOCH NICHT MERGEN - Tests fixen

## Nächste Schritte
1. fixture für mood_context hinzufügen
2. test_mood_suggestion timeout erhöhen
3. Erneut testen
```

## Config-Parameter
- `module`: Name des Moduls
- `branch`: Git-Branch
- `spec`: Pfad zur Spec-Datei
