# 🚨 NOTFALL-AUDIT: pilotsuite-styx-ha HISTORIEN-BERICHT

**Datum:** 2026-03-03  
**Audit-Tiefe:** Alle Git-Tags (v7.x → v13.x)  
**Status:** ✅ ABGESCHLOSSEN

---

## 📊 ZUSAMMENFASSUNG

### Verlorene Features im Überblick

| Kategorie | Verloren | Status |
|-----------|----------|--------|
| **Dashboard YAMLs** | 1 Datei | ❌ `pilotsuite_dashboard_v10.5.yaml` entfernt in v12.18.0 |
| **Habitus Zones Cards** | 2 Module | ❌ `habitus_zone_dashboard_card.py`, `habitus_control_cards.py` entfernt |
| **Dashboard Generator** | 1 Generator | ❌ `pilotsuite_3tab_generator.py` entfernt |
| **Icons/Assets** | 2 Dateien | ⚠️ `icon@2x.png` entfernt, `brands/` Ordner entfernt |
| **ZeroConfig** | ✅ Vorhanden | ✔️ In v13.0.0 noch enthalten |
| **Token Auth** | ✅ Vorhanden | ✔️ `CONF_TOKEN` in v13.0.0 enthalten |
| **Config Flow** | ✅ Vorhanden | ✔️ ZeroConfig-Step in v13.0.0 enthalten |

---

## 1️⃣ VERLORENE DASHBOARD YAML FILES

### ❌ `pilotsuite_dashboard_v10.5.yaml`

**Pfad (v11.0.0):** `custom_components/ai_home_copilot/dashboard_cards/pilotsuite_dashboard_v10.5.yaml`

**Inhalt:** 576 Zeilen, 3-Tab Layout:
- **Tab 1: Habitus** — Mood/Zonen (Comfort, Joy, Frugality Gauges)
- **Tab 2: Hausverwaltung** — Energie, Präsenz, Automationen
- **Tab 3: Styx** — Neural Dashboard, Brain Graph

**Hinzugefügt:** Commit `79596b7` (v10.5.1, 2026-02-27)  
**Entfernt:** Commit `10489ea` (v12.18.0, 2026-03-02) — "refactor: rename integration"

**Grund:** Beim Refactoring von `ai_home_copilot` → `copilot_ha` wurde die Datei nicht migriert.

**Betroffene Generatoren:**
- `pilotsuite_3tab_generator.py` (840 Zeilen) — ebenfalls entfernt

---

## 2️⃣ VERLORENE HABITUS ZONES MODULE

### ❌ `habitus_zone_dashboard_card.py`

**Pfad (v11.0.0):** `custom_components/ai_home_copilot/dashboard_cards/habitus_zone_dashboard_card.py`

**Funktionalität:**
- Generiert Lovelace Dashboard View pro Habitus-Zone
- Zone Status + Entity Summary
- Mood Gauges pro Zone (Comfort/Joy/Frugality)
- Recent Patterns & Suggestions
- News & Warnings Section
- Household Quick Actions

**Hinzugefügt:** Commit `7b76611` (v7.8.6)  
**Entfernt:** Commit `10489ea` (v12.18.0)

---

### ❌ `habitus_control_cards.py`

**Pfad (v11.0.0):** `custom_components/ai_home_copilot/dashboard_cards/habitus_control_cards.py`

**Funktionalität:**
- **Override-Modi Panel** — Party/Vacation/Sleep/Eco/Guest/Children Sleep
- **Musikwolke Panel** — Volume, Favorites, Coordinator Status, Grouping
- **Light Module Panel** — Brightness Ratio, Circadian Presets, Threshold Slider
- **Presence Module Panel** — Timeout Config, Sensor Status
- **Zone Automation Panel** — Occupancy, Subsystem Evaluations
- **Heating Panel** — Override Target Temperature

**Hinzugefügt:** Commit `cc0f15a` (v10.0.0)  
**Entfernt:** Commit `10489ea` (v12.18.0)

---

## 3️⃣ FEHLENDE ICONS / ASSETS

### ⚠️ `icon@2x.png` (Retina-Icon)

**Pfad (v11.0.0):** `custom_components/ai_home_copilot/icon@2x.png`

**Status:** In v13.0.0 nicht mehr vorhanden  
**Verbleibende Icons:**
- ✅ `custom_components/copilot_ha/icon.png` (vorhanden)
- ✅ `custom_components/copilot_ha/logo.png` (vorhanden)
- ✅ `custom_components/copilot_ha/icons.json` (vorhanden)

### ⚠️ `brands/` Ordner

**Pfad (v11.0.0):** `custom_components/ai_home_copilot/brands/`
- `brands/icon.png`
- `brands/logo.png`

**Status:** Ordner komplett entfernt in v12.18.0  
**Grund:** Struktur-Refactoring, HA-Branding-Richtlinien angepasst

---

## 4️⃣ ZEROCONFIG IMPLEMENTATION

### ✅ VORHANDEN in v13.0.0

**Pfad:** `custom_components/copilot_ha/config_flow.py`

**ZeroConfig-Step:** `async_step_zero_config()`

**Funktionalität:**
- Install & Start mit Smart Defaults
- Auto-Discovery des Core Endpoints
- Fallback auf Defaults wenn Core nicht erreichbar
- Keine manuelle Konfiguration nötig

**Code-Auszug (v13.0.0):**
```python
async def async_step_zero_config(self, user_input: dict | None = None) -> FlowResult:
    """Zero Config - instant start with Styx defaults.
    
    Tries Core connectivity first; if unreachable, creates the entry
    with default values and schedules background discovery.
    """
```

**Status:** ✔️ **NICHT VERLOREN** — ZeroConfig ist in v13.0.0 voll funktionsfähig

---

## 5️⃣ HA TOKEN AUTH

### ✅ VORHANDEN in v13.0.0

**Pfad:** `custom_components/copilot_ha/__init__.py`, `config_flow.py`, `const.py`

**Token-Konstanten:**
- `CONF_TOKEN` — Haupt-Token für Core-Auth
- `_LEGACY_CONNECTION_KEYS` — Backward-Compat für alte Tokens

**Auth-Flow:**
- Bearer Token Auth
- X-Auth-Token Fallback
- Reauth-Flow bei Token-Expiry

**Status:** ✔️ **NICHT VERLOREN** — Token Auth ist in v13.0.0 voll funktionsfähig

---

## 6️⃣ CONFIG-FLOW MODULE

### ✅ VORHANDEN in v13.0.0

**Pfad:** `custom_components/copilot_ha/config_flow.py`

**Steps:**
1. `async_step_user()` — Menü: ZeroConfig / QuickStart / Manual
2. `async_step_zero_config()` — ZeroConfig Setup
3. `async_step_quick_start()` — Guided Wizard (~2 min)
4. `async_step_manual_setup()` — Expert Configuration
5. `async_step_reauth()` — Token Re-Authentifizierung

**Support-Module:**
- `config_helpers.py` — CSV Utils, Constants
- `config_schema_builders.py` — Schema Builder
- `config_wizard_steps.py` — Wizard Step Handler
- `config_zones_flow.py` — Zone Management
- `config_options_flow.py` — OptionsFlowHandler
- `setup_wizard.py` — Setup Wizard

**Status:** ✔️ **NICHT VERLOREN** — Config Flow ist in v13.0.0 voll funktionsfähig

---

## 7️⃣ GIT-COMMITS DIE FEATURES ENTFERNT HABEN

### Haupt-Commit: `10489ea` (v12.18.0)

**Titel:** "refactor: rename integration from ai_home_copilot to copilot_ha"  
**Datum:** 2026-03-02 16:25:43 +0100  
**Autor:** Autopilot <autopilot@copilot.local>

**Entfernte Dateien (relevant für Audit):**
```
D	custom_components/ai_home_copilot/dashboard_cards/habitus_control_cards.py
D	custom_components/ai_home_copilot/dashboard_cards/habitus_zone_dashboard_card.py
D	custom_components/ai_home_copilot/dashboard_cards/pilotsuite_3tab_generator.py
D	custom_components/ai_home_copilot/dashboard_cards/pilotsuite_dashboard_v10.5.yaml
D	custom_components/ai_home_copilot/icon@2x.png
D	custom_components/ai_home_copilot/brands/icon.png
D	custom_components/ai_home_copilot/brands/logo.png
```

**Betroffene Module:**
- 309 Python Files umbenannt (ai_home_copilot → copilot_ha)
- Dashboard Cards nicht vollständig migriert
- Icons teilweise verloren

---

## 8️⃣ PFAD-ANALYSE: WO WAR WAS?

### v7.11.1 (Legacy)
```
custom_components/ai_home_copilot/
├── config_flow.py
├── habitus_zones_store_v2.py
└── (keine dashboard_cards/)
```

### v11.0.0 (Peak)
```
custom_components/ai_home_copilot/
├── config_flow.py
├── setup_wizard.py
├── auto_setup.py
├── habitus_dashboard.py
├── habitus_dashboard_cards.py
├── habitus_zones_store_v2.py
├── dashboard_cards/
│   ├── pilotsuite_dashboard_v10.5.yaml ⭐
│   ├── pilotsuite_3tab_generator.py ⭐
│   ├── habitus_zone_dashboard_card.py ⭐
│   ├── habitus_control_cards.py ⭐
│   ├── brain_graph_card.yaml
│   ├── mesh_dashboard_*.yaml
│   └── ...
├── icon.png
├── icon@2x.png ⭐
├── logo.png
└── brands/
    ├── icon.png ⭐
    └── logo.png ⭐
```

### v12.15.0 (Transition)
```
custom_components/ai_home_copilot/
├── (gleiche Struktur wie v11.0.0)
└── dashboard/ (separates Flask-Dashboard)
    ├── app.py
    ├── api/v1/dashboard.py
    ├── templates/
    └── static/
```

### v13.0.0 (Current)
```
custom_components/copilot_ha/
├── config_flow.py ✅
├── setup_wizard.py ✅
├── habitus_dashboard.py ✅
├── habitus_dashboard_cards.py ✅
├── habitus_zones_store_v2.py ✅
├── dashboard_cards/
│   ├── brain_graph_card.yaml ✅
│   ├── brain_graph_dashboard.yaml ✅
│   ├── dashboard_examples.yaml ✅
│   ├── mesh_dashboard_*.yaml ✅
│   └── (FEHLER: pilotsuite_*.yaml ❌)
├── icon.png ✅
├── logo.png ✅
└── icons.json ✅
```

---

## 9️⃣ EMPFOHLENE WIEDERHERSTELLUNG

### P0: Dashboard YAMLs

1. **`pilotsuite_dashboard_v10.5.yaml` wiederherstellen**
   ```bash
   git show v11.0.0:custom_components/ai_home_copilot/dashboard_cards/pilotsuite_dashboard_v10.5.yaml \
     > custom_components/copilot_ha/dashboard_cards/pilotsuite_dashboard_v10.5.yaml
   ```

2. **`pilotsuite_3tab_generator.py` wiederherstellen**
   ```bash
   git show v11.0.0:custom_components/ai_home_copilot/dashboard_cards/pilotsuite_3tab_generator.py \
     > custom_components/copilot_ha/dashboard_cards/pilotsuite_3tab_generator.py
   ```

### P1: Habitus Zones Cards

3. **`habitus_zone_dashboard_card.py` wiederherstellen**
   ```bash
   git show v11.0.0:custom_components/ai_home_copilot/dashboard_cards/habitus_zone_dashboard_card.py \
     > custom_components/copilot_ha/dashboard_cards/habitus_zone_dashboard_card.py
   ```

4. **`habitus_control_cards.py` wiederherstellen**
   ```bash
   git show v11.0.0:custom_components/ai_home_copilot/dashboard_cards/habitus_control_cards.py \
     > custom_components/copilot_ha/dashboard_cards/habitus_control_cards.py
   ```

### P2: Icons

5. **`icon@2x.png` wiederherstellen** (optional, Retina-Support)
   ```bash
   git show v11.0.0:custom_components/ai_home_copilot/icon@2x.png \
     > custom_components/copilot_ha/icon@2x.png
   ```

---

## 🔟 FAZIT

### Kritische Verluste
- ❌ **3-Tab Dashboard YAML** (576 Zeilen) — Haupt-Dashboard für End-User
- ❌ **3-Tab Generator** (840 Zeilen) — Auto-Generierung des Dashboards
- ❌ **Habitus Zone Dashboard Card** — Per-Zone Übersicht mit Mood
- ❌ **Habitus Control Cards** — Live-Controls für Override-Modi, Musikwolke, Licht

### Nicht betroffen (✅ vorhanden)
- ✔️ ZeroConfig Implementation
- ✔️ HA Token Auth
- ✔️ Config Flow Module
- ✔️ Basis Dashboard Cards (Brain Graph, Mesh)
- ✔️ Haupt-Icons (icon.png, logo.png)

### Hauptursache
Commit `10489ea` (v12.18.0) — Beim Refactoring von `ai_home_copilot` → `copilot_ha` wurden spezifische Dashboard-Dateien nicht migriert. Die Umbenennung betraf 309 Python-Dateien, aber YAML-Generatoren und einige Card-Module wurden übersehen.

---

**Nächste Schritte:**
1. P0-Dateien aus v11.0.0 wiederherstellen
2. Pfade anpassen (ai_home_copilot → copilot_ha)
3. Tests für Dashboard-Generatoren hinzufügen
4. Release v13.0.1 mit Wiederherstellung patchen

---

*Audit erstellt von: @cowdya (Subagent)*  
*Zeitrahmen: 2026-03-03 01:51 - 2026-03-03 02:XX*
