# PilotSuite HA Add-on — Release Notes v14.7.5

**Datum:** 2026-03-20  
**Version:** 14.7.5  
**Minimale Home Assistant Version:** 2024.4.0  
**Gepaart mit:** Core v14.7.5

---

## Was ist neu

### HA ConfigFlow Modernisierung

- **Delta-Write-Pattern:** ConfigEntry State wird nur noch als Delta geschrieben — kein Full-Overwrite mehr bei Updates
- **Reconfigure-Step:** `async_step_reconfigure()` mit `_get_reconfigure_entry()` ab sofort nach HA 2024.4+ Muster
- **OptionsFlow Parameter-Sync:** Gemeinsame Parameter (host/port/token) werden beim Reconfigure akkumuliert statt verworfen
- **ConfigFlow Helper-Migration:** Alle Flows auf `self.config_entry` + `self._config_entry_id` umgestellt

### HA UI Cards

- **Zone-Creator-Card `getConfigForm()`:** `static async getConfigForm()` mit HaFormSchema nach HA-PR #16142
- **habitus-brain-card.ts:** Number-Felder (`stale_threshold_seconds`, `mood_history_hours`), Mehrfachfelder (`zones`, `monitored_modules`)
- **zone-module-editor-card.ts:** Modulabhaengige Pflichtfeld-Validierung, Secondary-Zone-States (dark/sleep/extended)
- **card-form-helper.ts:** number/array/attribute-Support mit zentraler Validierung
- **editor-schema-validation.ts:** Typsichere Schema-Validierung
- **zone-editor-api-client.ts:** CRUD-Client fuer `/api/v1/zone-editor` Endpunkte

### HA Tests & Schema

- **conftest.py:** Standardisierte Test-Fixtures (MockHass, ConfigEntry, Flow-Handler-Factories)
- **Module-per-Zone Schemas:** Pydantic-v2-Schema-Dateien fuer alle 8 Modultypen (Light/Audio/Climate/Cover/Energy/Scene/Security/Zone)
- **Integration-Tests Zone-Flows:** 46 neue Tests fuer ConfigFlow/OptionsFlow/SnapshotFlow
- **Dynamic-Entity-Generation-Tests:** 57 Tests fuer schema-getriebene Entity-Generierung

### HA Add-on

- **hacs.json:** HACS-Listing-Konfiguration hinzugefuegt

---

## Was wurde behoben

- **Dashboard-Init-Binding:** `window.dashboard` wird jetzt per IIFE vor `init()` gesetzt — inline onclick-Handler funktionieren korrekt
- **Snapshot-Import Path-Resolve:** Robust gegen `/local/...`, `~`, `$ENV` und Path-Traversal

---

## Breaking Changes

**Keine.**

Es gibt keine Breaking Changes in diesem Release. Das Update kann ohne Migrationsschritte oder Konfigurationsanpassungen eingespielt werden.

---

## Upgrade-Hinweise

- **Home Assistant 2024.4.0+ erforderlich.** Bitte stelle sicher, dass dein Home Assistant auf Version 2024.4.0 oder höher aktualisiert ist, bevor du dieses Add-on installierst.
- Bei einem Update von einer Version < 14.7.5 werden bestehende ConfigEntry-Daten automatisch migriert (Delta-Write-Pattern kompatibel).
- Nach dem Update einen Restart der Integration durchführen, damit alle neuen Zone-Editor-UI-Komponenten initialisiert werden.

---

## Kompatibilität

| Komponente | Version |
|---|---|
| PilotSuite HA Add-on | **14.7.5** |
| PilotSuite Core | **14.7.5** (Paired Release) |
| Home Assistant | **2024.4.0+** |
| Integration Type | hub (`local_push`) |
