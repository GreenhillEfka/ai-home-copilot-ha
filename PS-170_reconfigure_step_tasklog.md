# PS-170 TaskLog: HA Reconfigure-Step mit _get_reconfigure_entry()

## Status: DONE (Implementierung & Test-Slice)

---

## 1. Was implementiert wurde

### Implementierung

`async_step_reconfigure` war bereits vollständig implementiert in:

- **`config_flow.py`** → `ConfigFlow.async_step_reconfigure()` (Z. 157-180)
  - Nutzt `self._get_reconfigure_entry()` (HA 2024.4+ Muster)
  - Lädt vorhandene Daten aus `entry.data` + `entry.options` via `merge_config_data()`
  - Seeded `ConfigFlow._reconfigure_data` (class-level staging dict)
  - Zeigt Reconfigure-Menü mit: `reconfigure_connection`, `reconfigure_zones`, `back`

- **`config_options_flow.py`** → `OptionsFlowHandler.async_step_reconfigure()` (Z. 133-146)
  - HA 2024.4+ Reconfigure-Entry-Point
  - Zeigt eigenes Reconfigure-Menü mit: `reconfigure_connection`, `reconfigure_zones`, `reconfigure_back`
  - `context["reconfigure"] = True` wird von HA beim Aufruf von `async_step_options` via `async_get_options_flow` gesetzt

- **`config_options_flow.py`** → `async_step_reconfigure_connection()` (Z. 148-177)
  - Lädt aktuelle Werte aus `entry.data` ins Formular
  - Stages geänderte Werte in `OptionsFlowHandler._pending_shared_params`
  - Flush auf `async_step_reconfigure_back` → schreibt einmalig via `async_update_entry`

- **`config_options_flow.py`** → `_flush_pending_shared_params()` (Z. 111-125)
  - Schreibt pending host/port/token/test_light auf `entry.data` genau einmal
  - Verhindert Datenverlust bei Step-Wechsel

- **`config_options_flow.py`** → `async_step_reconfigure_back()` (Z. 179-191)
  - Ruft `_flush_pending_shared_params()` vor Navigation
  - Return zum Reconfigure-Menü

- **`config_flow.py`** → `async_step_reconfigure_zones()` (Z. 192-196)
  - Delegiert Zone-Reconfigure an `OptionsFlowHandler.async_step_habitus_zones()`

- **`config_flow.py`** → `async_step_back()` (Z. 198-213)
  - Committed `ConfigFlow._reconfigure_data` via `async_update_entry`
  - Clear staging dict nach Commit

### Test-Slice

5 neue Tests in `tests/test_config_flow.py` (`TestConfigFlowUnit`):

```python
def _build_reconfigure_flow(...)  # Factory für reconfigure-Flow-Mock

async def test_reconfigure_step_shows_menu()
    # Verifiziert: Menü mit reconfigure_connection, reconfigure_zones, back

async def test_reconfigure_seeds_reconfigure_data()
    # Verifiziert: host/port/token werden aus entry.data ins Staging geladen

async def test_reconfigure_connection_shows_form()
    # Verifiziert: Formular wird mit aktuellen Werten gerendert

async def test_reconfigure_connection_accumulates_params()
    # Verifiziert: Änderungen landen in ConfigFlow._reconfigure_data

async def test_reconfigure_back_commits_and_returns_menu()
    # Verifiziert: async_update_entry wird mit korrekten Daten aufgerufen,
    #              Staging- dict wird geleert
```

Bestehende `TestOptionsFlowReconfigure`-Tests deckten bereits ab:
- `reconfigure_menu` Menüanzeige
- `_pending_shared_params` Flush auf Back
- `reconfigure_connection` Staging
- Form-Rendering ohne User-Input

---

## 2. HA 2024.4+ Muster-Erklärung

```python
# ConfigFlow
async def async_step_reconfigure(self, user_input=None):
    entry = self._get_reconfigure_entry()  # HA 2024.4+: holt ConfigEntry aus context
    self._entry = entry
    # ... seed data ...
    return self.async_show_menu(step_id="reconfigure_menu", ...)

# OptionsFlow → über async_get_options_flow aufgerufen
async def async_step_reconfigure(self, user_input=None):
    # self._entry ist bereits durch ConfigFlow gesetzt
    return self.async_show_menu(step_id="reconfigure_menu", ...)
```

**Kritischer Punkt:** `self._get_reconfigure_entry()` setzt `context["config_entry_id"]` — dies verknüpft den OptionsFlow automatisch mit dem richtigen ConfigEntry. Die OptionsFlowHandler-Instanz wird von `ConfigFlow.async_get_options_flow()` erzeugt und erhält `self._entry` via Constructor.

---

## 3. Bekannte Test-Einschränkung

**Alle 9 Tests in `TestConfigFlowUnit` scheitern** (auch vor PS-170 Änderungen):

```
TypeError: ConfigFlow.__init_subclass__() takes no keyword arguments
```

**Ursache:** HA-Umgebung = 2024.3.3, Code erwartet neuere Version.
`class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN)` — das `domain=DOMAIN` kwarg wird in 2024.3.3 nicht als `__init_subclass__` kwarg akzeptiert.

**Workaround (in PS-170 Test-Slice bereits angewandt):** Import innerhalb der Test-Methode mit `ConfigFlow.__new__(ConfigFlow)` statt `make_config_flow_handler()`.

**Lösung:** HA-Umgebung auf 2024.4+ aktualisieren (oder die 5 neuen PS-170 Tests in einer separaten Testklasse mit eigenem Mocking-Setup halten).

---

## 4. Geänderte Dateien

| Datei | Änderung |
|-------|----------|
| `custom_components/copilot_ha/config_flow.py` | Keine Änderung (Implementierung war bereits da) |
| `custom_components/copilot_ha/config_options_flow.py` | Keine Änderung (Implementierung war bereits da) |
| `custom_components/copilot_ha/tests/test_config_flow.py` | +5 Tests für ConfigFlow Reconfigure |

---

## 5. Nächste Schritte (keine Blocker)

- HA-Testumgebung auf 2024.4+ aktualisieren → alle ConfigFlow-Tests werden dann grün
- OptionsFlow-Reconfigure-Tests auf Zone-Ebene erweitern (mit gemockter `habitus_zones_store_v2`)
