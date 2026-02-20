# TAG_SYSTEM v0.1 (AI Home CoPilot) — Spezifikation (Entwurf)

**Ziel:** Ein konsistentes, privacy-first Tag-System für AI Home CoPilot (AICoPilot), das
- sauber zwischen *physischer Struktur* (Areas/Zones), *Inventar* (Devices/Entities), *Semantik/Intention* (Rollen) und *Organisation* (Labels) trennt,
- in Home Assistant (HA) möglichst nativ über **Labels** arbeitet,
- intern (Core Add-on / „Brain Graph“) reichere Semantik (Rollen, Kategorien, Provenienz, Governance) abbildet,
- migrationsfähig ist und langfristig stabil bleibt.

> Hinweis zur Begriffsvermeidung: Home Assistant hat auch eine **„tag“ Integration** (NFC/QR). Diese Spezifikation meint **Klassifizierungs-Tags/Labels** – nicht NFC-Tags.

---

## 1. Begriffe & Semantik (klar getrennt)

### 1.1 Tag (AICoPilot-Tag)
Ein **Tag** ist ein *atomarer, stabiler Schlüssel*, der auf Objekte (Entity/Device/Area/Automation/…​) angewendet werden kann.
- **Atomar:** nicht „kitchen+light“, sondern getrennte Tags (z. B. `place.kitchen`, `kind.light`).
- **Stabil:** ID bleibt über Zeit stabil, auch wenn Anzeigenamen/Icons sich ändern.
- **Maschinenlesbar:** gut für Regeln/Policies/Filter/Graph-Queries.

### 1.2 Label (HA-Label)
Ein **Label** ist die *Home-Assistant-native* Gruppierung, die im UI sichtbar ist und als Ziel in Automationen/Skripten genutzt werden kann.
- HA-Labels können auf Areas, Devices, Entities, Automationen, Szenen, Skripte, Helper angewendet werden (laut HA-Doku).
- Für AICoPilot ist **HA-Label** die **primäre UI-/HA-Kompatibilitäts-Schicht**.

**Entscheidung v0.1:**
- *Wenn möglich:* AICoPilot-Tags **werden als HA-Labels materialisiert** (1:1), damit Nutzer/Automationen sie direkt nutzen können.
- *Zusätzlich:* AICoPilot führt eine interne Registry (Brain) für Metadaten, Rollen, Governance, Versionierung, Aliases.

### 1.3 Rolle (Role)
Eine **Rolle** ist ein spezieller Tag-Typ, der Verhalten/Interpretation steuert.
Beispiele:
- `role.safety_critical` (nie automatisch ausschalten)
- `role.primary_light` (Default-Licht in Raum)
- `role.essential` (bei „Haus verlassen“ prüfen)

Rollen sind **nicht rein organisatorisch**, sondern verändern Entscheidungspfade.

### 1.4 Kategorie / Facette (Category/Facet)
**Kategorien** strukturieren Tags in Facetten (für Konsistenz, Suche, UX):
- `place.*` (Ort/Zone)
- `kind.*` (Art: light, sensor, switch)
- `domain.*` (HA-Domain, optional)
- `cap.*` (Capabilities: dimmable, power_metering)
- `role.*` (Behavior)
- `state.*` (Zustände: candidate, broken, needs_repair)
- `inv.*` (Inventory/Lifecycle)

Eine Kategorie ist **kein eigener Datentyp**, sondern Namenskonvention.

---

## 2. Namensschema / Taxonomie

### 2.1 Tag-ID Format
**Format:**
```
<namespace>.<facet>.<key>
```
- alles **lowercase**
- Trennzeichen: Punkt für Segmente, Bindestrich innerhalb von Keys
- keine Leerzeichen, keine Umlaute in der ID
- Beispiele:
  - `aicp.place.kueche`
  - `aicp.kind.light`
  - `aicp.cap.dimmable`
  - `aicp.role.safety_critical`
  - `aicp.state.needs_repair`

**Rationale:**
- Punkt-segmentiert ist gut für Prefix-Queries (z. B. alle `aicp.role.*`).

### 2.2 Namespaces
- `aicp.*` — von AI Home CoPilot verwaltete Tags (empfohlen)
- `user.*` — vom Nutzer definierte Tags, die AICoPilot respektiert, aber nicht umbenennt
- `sys.*` — reserviert (intern), **nicht** exportiert als HA-Label, außer explizit erlaubt
- `ha.*` — optionales Mirror/Mapping für vorhandene HA-Labels (nur als Alias-Layer)

**Regel:** `sys.*` nie in UI anzeigen, nie als HA-Label materialisieren.

### 2.3 Lokalisierung (de/en)
- **ID bleibt sprachneutral** (ASCII, z. B. `kueche` statt `küche`).
- Anzeigename kann lokalisiert werden.

**Minimal v0.1:** nur `name_de` + optional `name_en`.

### 2.4 Versionierung
- Tags selbst sind stabil; Änderungen sind meist an Metadaten (Name/Icon/Description).
- **Schema-Version** der Registry separat: `tag_system_version: 0.1`.

**Breaking changes:** über Migration (siehe Abschnitt 8), nicht über Tag-ID-Änderungen.

---

## 3. Datenmodell (intern, Core Add-on / Brain)

### 3.1 Tag-Objekt
```yaml
Tag:
  id: aicp.role.safety_critical
  namespace: aicp
  facet: role
  key: safety_critical
  display:
    de: "Sicherheitskritisch"
    en: "Safety critical"
  description:
    de: "Darf nicht automatisch deaktiviert/abgeschaltet werden."
  icon: "mdi:shield-alert"
  color: "#D32F2F"  # optional
  type: "tag" | "role"  # role ist tag+semantik
  governance:
    visibility: public | private | internal
    source: system | user | learned
    confidence: 0.0-1.0     # nur für learned
    pii_risk: none | low | high
    retention: permanent | ephemeral
  aliases:
    - "aicp.role.critical"  # legacy IDs
  ha:
    materialize_as_label: true
    label_slug: "aicp_role_safety_critical" # optional, falls HA Slug/ID anders ist
  timestamps:
    created_at: 2026-02-08T00:00:00Z
    updated_at: 2026-02-08T00:00:00Z
```

### 3.2 Tag-Zuweisung (Assignment)
Assignments sind Ereignisse/Edges im Brain Graph:
```yaml
Assignment:
  subject:
    kind: entity | device | area | automation | scene | script | helper | person
    ha_id: "light.kueche_decke"  # canonical HA ID (oder registry-ID)
  tag_id: "aicp.kind.light"
  source: user | system | learned
  confidence: 1.0
  reason: "derived_from_domain" # optional
  scope: runtime | persisted
  created_at: 2026-02-08T00:00:00Z
```

### 3.3 Graph-Integration (Brain Graph)
- Knoten: `Entity`, `Device`, `Area`, `Automation`, `Scene`, `Script`, `Helper`, `Person`, `InventoryItem`, `Candidate`, `RepairTicket`, `HabitusZone`
- Kanten: `HAS_TAG`, `SUGGESTS_TAG`, `CONFLICTS_WITH_TAG`, `DERIVED_FROM`

**Query-Beispiele:**
- „Alle Geräte mit `aicp.state.needs_repair`“
- „Alle Entities in Area X mit `aicp.role.safety_critical`“

---

## 4. Mapping auf Home Assistant

### 4.1 Grundprinzip
- AICoPilot nutzt HA-Registries als „Source of Truth“ für **Objekte**:
  - Areas: Area Registry
  - Devices: Device Registry
  - Entities: Entity Registry
- Für **Gruppierung/Targets** nutzt AICoPilot **HA Labels**.
- AICoPilot speichert zusätzliche Semantik/Provenienz im Add-on (nicht in HA-Registries), um HA-Kern sauber zu halten.

### 4.2 HA Labels als Materialisierung
**Warum Labels?**
- UI sichtbar
- in Automationen/Skripten als Target nutzbar
- auf vielen Objektarten anwendbar

**Regel:**
- Jeder AICoPilot-Tag mit `materialize_as_label=true` wird als HA-Label erzeugt/abgeglichen.
- Assignments werden als Label-Zuweisungen in HA gespiegelt (wo möglich).

### 4.3 Areas vs Zones vs Labels
- **Area**: physischer Standort (meist 1 Gerät → 1 Area)
- **Zone**: geofencing/Standortlogik (HA Zones), nicht „Raum“
- **Label**: orthogonale Gruppierung (z. B. „Energiehungrig“, „Kinderzimmer“, „Wartung“)

**Entscheidung v0.1:**
- „Habitus-Zonen“ sind **nicht** HA-Zones. Sie sind AICoPilot-Konzepte und werden über Tags/Label + interne HabitusZone-Objekte modelliert.

### 4.4 Umgang mit HA-eigenen Labels
- Wenn Nutzer Labels manuell anlegt, kann AICoPilot sie als `user.*` importieren (optional).
- Konflikte (gleiches Label, andere Semantik) werden über Namespace-Präfixe minimiert.

---

## 5. Nutzung in AICoPilot-Modulen

### 5.1 Habitus-Zonen
**Ziel:** Verhaltensräume (z. B. „Schlafmodus“, „Arbeitsmodus“, „Gäste“), die nicht 1:1 physische Areas sind.

Empfohlenes Tagging:
- `aicp.habitus.sleep`
- `aicp.habitus.work`
- `aicp.habitus.guest`

Zusätzlich Rollen:
- `aicp.role.quiet_hours_sensitive`
- `aicp.role.notification_critical`

**Regel:** Habitus-Zonen definieren *Policy-Sets* (wann/was automatisiert wird), nicht nur Gruppierung.

### 5.2 Inventory
Inventory ist Lifecycle-/Asset-Sicht:
- `aicp.inv.installed`
- `aicp.inv.spare`
- `aicp.inv.retired`
- `aicp.inv.warranty`

und Typ/Hersteller ggf. als Tag (sparsam):
- `aicp.kind.sensor`
- `aicp.vendor.shelly` (optional; nur wenn wirklich nützlich)

### 5.3 Candidates / Repairs
**Candidates** (Vorschläge der AI):
- `aicp.state.candidate`
- `aicp.state.needs_attention`

**Repairs:**
- `aicp.state.needs_repair`
- `aicp.repair.battery_low`
- `aicp.repair.unreachable`

**Governance:** learned/candidate Tags haben `confidence < 1.0` und können „nur intern“ bleiben, bis bestätigt.

### 5.4 Brain Graph
- Tags sind die schnellste Achse zur Verdichtung von Kontext.
- Rollen beeinflussen „Planung/Tool-Auswahl“ (z. B. keine aggressiven Aktionen bei `role.safety_critical`).

---

## 6. Governance & Privacy (privacy-first)

### 6.1 Sichtbarkeit
- `public`: darf als HA-Label erscheinen und in UI angezeigt werden
- `private`: nur intern (Brain); keine HA-Materialisierung
- `internal`: systemreserved (`sys.*`)

### 6.2 PII/Heikle Inhalte
**Regel:** Keine Tags, die direkt personenbezogene/gesundheitliche/hoch-sensible Informationen kodieren.
- Nicht: `aicp.person.alice_sleep_disorder`
- Stattdessen: Rolle/Policy abstrakt halten, z. B. `aicp.role.quiet_hours_sensitive`.

### 6.3 Provenienz & Audit
- Jede Zuweisung trägt `source` + optional `reason`.
- Learned Tags sind widerrufbar und müssen UI/CLI-Review unterstützen.

### 6.4 Minimierung
- Nur materialisieren, was echten Mehrwert für Nutzer/Automationen hat.
- „Debug/Engineering“-Tags bleiben `private/internal`.

---

## 7. Implementations-Empfehlung: Integration vs Core Add-on

### 7.1 Home Assistant Integration (leichtgewichtig, „Connector“)
**Aufgaben (empfohlen):**
- Lesen/Beobachten von:
  - Area/Device/Entity Registry
  - HA Labels (falls API verfügbar)
- Anwenden/Entfernen von **HA Labels** für unterstützte Objektarten
- Exponieren eines Services/API:
  - `aicopilot.tag_apply` (subject + tag_id)
  - `aicopilot.tag_remove`
  - `aicopilot.tag_list`

**Nicht in Integration:** komplexe Ontologie, ML, Graph, heuristische Entscheidungen.

### 7.2 Core Add-on („Brain“)
**Aufgaben (empfohlen):**
- Tag Registry (Metadaten, Version, Aliases)
- Assignment Store (mit Audit)
- Konfliktregeln / Policies
- Migrationsengine
- Export/Sync in Richtung Integration (Materialisierung in HA)

**Kommunikation:** lokale API (Supervisor/Ingress), keine Cloud nötig.

---

## 8. Migration (legacy → v0.1)

### 8.1 Migrationsquellen
- Vorhandene AICoPilot-Tag-Listen/Configs
- Vorhandene HA Labels (optional import)
- Alte „Gruppen“/„Kategorien“ aus früheren Versionen

### 8.2 Strategie
1. **Inventarisieren:** alle bisherigen „Tags/Labels/Groups“ einsammeln.
2. **Mapping-Tabelle:** legacy → neue `aicp.*` IDs.
3. **Aliases** setzen, um alte IDs zu akzeptieren.
4. **Materialisieren:** neue Tags als HA-Labels anlegen, nur `public`.
5. **Validate:** Konflikte (Doppelbedeutungen) markieren, Review-Queue erzeugen.

### 8.3 Deprication ohne Bruch
- Alte IDs bleiben als Alias für eine Übergangszeit.
- Intern immer auf canonical `Tag.id` normalisieren.

---

## 9. YAML-Beispiele (konkret)

### 9.1 Tag-Registry Datei (Add-on)
```yaml
# tags.yaml
schema_version: 0.1
reserved_namespaces:
  - sys
  - aicp

tags:
  - id: aicp.kind.light
    display:
      de: "Licht"
      en: "Light"
    icon: mdi:lightbulb
    type: tag
    ha:
      materialize_as_label: true

  - id: aicp.role.safety_critical
    display:
      de: "Sicherheitskritisch"
    icon: mdi:shield-alert
    type: role
    governance:
      visibility: public
    ha:
      materialize_as_label: true

  - id: sys.debug.no_export
    display:
      de: "(intern)"
    type: tag
    governance:
      visibility: internal
    ha:
      materialize_as_label: false
```

### 9.2 Assignments (Add-on)
```yaml
# assignments.yaml
schema_version: 0.1
assignments:
  - subject:
      kind: entity
      ha_id: light.kueche_decke
    tag_id: aicp.kind.light
    source: system
    confidence: 1.0
    reason: derived_from_domain

  - subject:
      kind: device
      ha_id: "device:1234abcd"  # falls ihr device-registry IDs nutzt
    tag_id: aicp.role.safety_critical
    source: user
    confidence: 1.0
```

### 9.3 Konfliktregel (Policy)
```yaml
# policies.yaml
schema_version: 0.1
policies:
  - if_has_tag: aicp.role.safety_critical
    then:
      forbid_actions:
        - turn_off
        - disable_automation
      require_confirmation: true
```

---

## 10. Offene Punkte (v0.1 → v0.2)
- Welche Objektarten sollen *initial* Label-Sync bekommen (nur Entities/Devices/Areas oder auch Automations/Scripts)?
- Wie genau adressieren wir „subject.ha_id“ stabil (entity_id vs registry unique_id vs device_id)?
- Welche learned Tags dürfen automatisch als HA-Label erscheinen (Default: nein)?

---

## 11. Quellen (für HA-Teil)
- Home Assistant Doku: Labels (Zuweisung auf Areas/Devices/Entities/Automations/Szenen/Skripte/Helper, Targets in Actions).
  - https://www.home-assistant.io/docs/organizing/labels/
- Home Assistant Developer Docs: Device Registry / Entity Registry.
  - https://developers.home-assistant.io/docs/device_registry_index/
  - https://developers.home-assistant.io/docs/entity_registry_index/
