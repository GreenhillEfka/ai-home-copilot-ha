# PilotSuite – Vollständige Vision & Architektur

> **Stand: 2026-02-15** – Konsolidiert aus allen bisherigen Dokumenten und Gesprächen

---

## 1. Was ist PilotSuite?

**PilotSuite = AI Home CoPilot** – Ein **erklärbares, neuronales Orchestrierungssystem** über Home Assistant.

### Was es IST:
- Ein **Entscheidungs- und Vorschlagslayer**, der Sensorik, Kontext, Stimmung, Historie und Nutzerintention zusammenführt
- Ein System, das aus all dem **gewichtete Vorschläge** ableitet
- Ein Werkzeug, das mit dem Nutzer denkt – **nicht für ihn**

### Was es NICHT ist:
- Kein monolithisches KI-System
- Kein autonomer Smart-Home-Controller
- Keine Blackbox-Automation

---

## 2. Die Philosophie (Die wichtigste Ebene!)

### 2.1 Leitprinzipien

| Prinzip | Bedeutung |
|---------|-----------|
| **User-Kontrolle vor Autonomie** | Autonomie existiert nur nach expliziter Freigabe |
| **Erklärbarkeit statt Magie** | Jede Entscheidung ist begründbar und visualisierbar |
| **Modularität auf allen Ebenen** | Module, Neuronen, Synapsen, Dienste sind austauschbar |
| **Wachstum statt Re-Konfiguration** | Neue Fähigkeiten ergänzen das System; sie ersetzen es nicht |
| **KI ist austauschbar** | Das System muss auch ohne externes LLM stabil nutzbar sein |
| **Alles ist beobachtbar** | States, Scores, Logs, Historien, Visualisierung |

### 2.2 Sicherheits-SOP (NICHT VERLETZEN!)

```
⚠️ SMART HOME / STATE-CHANGES:
   Vorschlag → explizites "Ja" → Ausführung
   Read-only → sofort ok

⚠️ GRUPPEN IN HOME ASSISTANT:
   Immer Mitglieder/Segmente identifizieren und EINZELN setzen
   Gruppen-State kann verzögert sein

⚠️ KONFIGURATIONEN:
   NIEMALS openclaw.json oder andere Configs ohne explizite Erlaubnis ändern
   Immer ERST fragen, DANN vorschlagen
```

### 2.3 Stakeholder-Matrix

| Aktion | User | CoPilot | System |
|--------|------|---------|--------|
| **Vorschlagen** | ✔ | ✔ | ✖ |
| **Erklären** | ✔ | ✔ | ✔ |
| **Handeln** | ✔ | ⛔/✔* | ✔ |
| **Lernen** | ✔ | ⛔ | ⛔ |

*Handeln nur nach expliziter Freigabe

---

## 3. Das Neuronale Modell

### 3.1 Die logische Kette

```
State (objektiv) → Neuron (bewertet Aspekt) → Mood (aggregiert Bedeutung) → Entscheidung
```

**WICHTIG:**
- Kein direkter Sprung State → Mood
- Neuronen sind zwingende Zwischenschicht
- Mood kennt keine Sensoren/Geräte – nur Bedeutung

### 3.2 Ebenen

```
┌──────────────────────────────────────────┐
│ Benutzer / Sprache / Chat / UI           │
└──────────────────────────────────────────┘
                    ↓
┌──────────────────────────────────────────┐
│ Entscheidungs- & Vorschlagslayer         │
│ (Begründung, Priorisierung, Alternativen)│
└──────────────────────────────────────────┘
                    ↓
┌──────────────────────────────────────────┐
│ Neuronales System                        │
│ (Kontext-, Zustands-, Mood-Neuronen)     │
└──────────────────────────────────────────┘
                    ↓
┌──────────────────────────────────────────┐
│ Sensorik, States, Historie, externe APIs │
└──────────────────────────────────────────┘
                    ↓
┌──────────────────────────────────────────┐
│ Home Assistant Core (Aktionen)           │
└──────────────────────────────────────────┘
```

### 3.3 Neuronen-Katalog

#### Kontext-Neuronen (objektiv)
- Presence (Raum, Haus, Person)
- TimeOfDay / DayType
- LightLevel / SunPosition
- Weather / Forecast
- CalendarLoad / Termine
- NoiseLevel
- MediaActivity
- SystemHealth (HA, Netz, Dienste)
- NetworkQuality
- SecurityState

#### Zustands-Neuronen (glätten, träge)
- EnergyLevel
- StressIndex
- RoutineStability
- SleepDebt
- AttentionLoad
- ComfortIndex

#### Mood-Neuronen (Hauptauslöser für Vorschläge)
- mood.relax
- mood.focus
- mood.active
- mood.sleep
- mood.away
- mood.alert
- mood.social
- mood.recovery

### 3.4 Synapsen – Beziehungsmodell

Synapsen verbinden:
- Neuron → Neuron
- Neuron → Vorschlag
- Mood → Aktionsempfehlung

Eigenschaften:
- Gewicht
- Schwellenwert
- Richtung
- Sichtbarkeit
- Lernstatus

---

## 4. Habitus – Das Muster-Erkennungs-System

### 4.1 Ziel

Der Habitus beobachtet Events und lernt **Verhaltensmuster**:
- „Nach A passiert oft B innerhalb Δt"
- Aus Mustern werden **Automationsvorschläge**
- **Niemals automatisch aktiv** – User muss bestätigen

### 4.1.1 Wichtige Design-Entscheidung: Manuelle Entity-Auswahl

**Entities werden MANUELL bei der Installation ausgewählt:**
- Wenn ein Habitus-Bereich hinzugefügt wird, wählt der User die relevanten Entities aus
- **Nur diese manuell ausgewählten Entities** werden für die Auswertung herangezogen
- Das macht das System zu Beginn **übersichtlicher** und vermeidet Rauschen

**Aktuelles Beispiel:**
- Aktuell ist nur **Wohnbereich** als Habitus-Zone für die Entwicklung definiert
- Weitere Zones können später ergänzt werden

**Begründung:**
1. **Übersichtlichkeit** - nur relevante Entities pro Zone
2. **Privacy-First** - keine automatisierte Entity-Erkennung
3. **User-Kontrolle** - User entscheidet was relevant ist
4. **Entwicklungsimplizität** - klares, bekanntes Set für Tests

### 4.2 MVP Pattern-Detection

```
Für Paare A→B (innerhalb Δt):
- support = count_pair(A,B)
- confidence = count_pair(A,B)/count_action(A)
- lift = confidence / (count_action(B)/total_actions)
- median_lag_s aus Delay-Histogramm

Empfehlungsschwellen:
- support >= 8 UND confidence >= 0.75 UND lift >= 1.5
```

### 4.3 Mood-Weighting

Zwei Ebenen:
1. **Beim Lernen**: Muster speichert Mood zum Zeitpunkt A → `mood_profile`
2. **Bei Vorschlägen**: `relevance = f(confidence, lift, support) * mood_match * governance_factor`

---

## 5. Betriebsmodi

| Modus | Beschreibung |
|-------|--------------|
| **Manual Mode** (Default) | Alles sichtbar, nichts automatisch, volle Kontrolle |
| **Assisted Mode** | Vorschläge priorisiert, Teilautomatik nach Freigabe |
| **Auto Mode** (explizit) | Definierte Synapsen dürfen auslösen, vollständiges Logging, jederzeit rücknehmbar |

---

## 6. Home Assistant UX

### Best Practice: Repairs + Blueprints
- Integration erzeugt **Repair-Issue** für jeden neuen Vorschlag
- "Fix" führt in einen Flow:
  - **Accept** → erstellt Automation aus Blueprint
  - **Reject** → blocklist / downrank
  - **Defer/Snooze** → später entscheiden

### Entities (beispielhaft)
```yaml
sensor.ai_copilot_mood:
  name: "AI CoPilot Mood"
  icon: mdi:robot-happy
  
sensor.ai_copilot_mood_confidence:
  name: "AI CoPilot Mood Confidence"
  icon: mdi:gauge
```

---

## 7. Tag System v0.1

### Namensschema
```
<namespace>.<facet>.<key>
```

Beispiele:
- `aicp.place.kueche`
- `aicp.kind.light`
- `aicp.cap.dimmable`
- `aicp.role.safety_critical`

### Kategorien
| Kategorie | Bedeutung |
|-----------|-----------|
| `place.*` | Ort/Zone |
| `kind.*` | Art (light, sensor, switch) |
| `cap.*` | Capabilities (dimmable, power_metering) |
| `role.*` | Verhalten (safety_critical, primary_light) |
| `state.*` | Zustände (candidate, broken, needs_repair) |

---

## 8. Release-Philosophie

### Branching-Strategie
```
main (production)
  │
  ├── dev/autopilot-YYYY-MM-DD (staging, 1 pro Tag max)
  │     │
  │     └── wip/feature-XXX (feature branches)
  │
  └── releases/v0.X.Y (release branches, protected)
```

### Verifizierungs-Checkliste (Pflicht vor Merge)
- [ ] `py_compile` erfolgreich
- [ ] Keine lint errors
- [ ] Unit Tests geschrieben
- [ ] CHANGELOG.md Eintrag
- [ ] Security Check (keine hardcoded secrets)

### Versionierung
```
v0.MAJOR.MINOR
```
- MAJOR: Breaking Changes
- MINOR: Neue Features (backwards compatible)
- PATCH: Bugfixes

### Release-Kommunikation
**Automatisch wenn:**
- Code frei geprüft (Tests grün, Review ok)
- Home Assistant Docs konform (https://www.home-assistant.io/docs/)
- CHANGELOG aktualisiert

**Manuell bei:**
- Breaking Changes
- Security-relevanten Änderungen

---

## 9. Modul-Orchestrierung

### Aktive Module (Stand 2026-02-15)

| Modul | Status | Zweck |
|-------|--------|-------|
| **SystemHealth** | ✅ | Systemzustand überwachen |
| **UniFi** | ✅ | Netzwerk-Kontext |
| **Energy** | ✅ | Energie-Analyse |
| **Tag System** | ✅ v0.2 | Entity-Klassifizierung |
| **Habitus Zones** | ✅ v2 | Zonen-basierte Muster |
| **Mood Context** | ✅ | Stimmungs-Aggregation |
| **Brain Graph** | ✅ | Neuronen-Visualisierung |

### Geplante Module
- Interactive Brain Graph Panel
- Multi-user Learning
- Performance-Optimierung

---

## 10. Cron Jobs (Orchestrierung)

### Aktive Jobs

| Job | Intervall | Zweck |
|-----|-----------|-------|
| HomeAssistant Pipeline Agent | 5min | Status-Checks, Muster-Erkennung |
| Selbstheilungs-Check | 30min | Verbindungen prüfen |
| Modul Orchestrierung | 30min | Modul-Konsistenz sicherstellen |
| Release Pipeline | 30min | Checkpoint erstellen |
| Project Agents | 3min | Kontinuierliche Entwicklung |

### WICHTIG: Model-Allowlist
Cron Jobs nutzen das **Default-Modell** (`glm-5:cloud`). Keine expliziten `model`-Felder in den Job-Payloads, sonst gibt es "model not allowed"-Fehler!

---

## 11. Die Goldene Regel

> **Home Assistant bleibt jederzeit das führende System.**
> 
> Der CoPilot **denkt mit**, er **denkt nicht für** den Nutzer.
> 
> **Jede State-Change erfordert explizite Zustimmung ("Ja").**

---

## 12. Mood-Diagnose

| Frage | Diagnose |
|-------|----------|
| "Warum keine Vorschläge?" | Mood zu niedrig |
| "Warum viele Vorschläge?" | Mood konkurrierend |
| "Warum falsche Richtung?" | Falsche Gewichtung |

**Mood ist Debug-Ebene, nicht Werkzeug.**

---

## 13. Chat-Interface als Nervensystem

Der Chat ist:
- **Eingabe** – "Mach das Licht aus" / "Warum schlägst du das vor?"
- **Erklärung** – "Ich habe das vorgeschlagen, weil..."
- **Steuerung** – "Mach das künftig automatisch" / "Nicht mehr vorschlagen"
- **Lernfreigabe** – "Merke dir, dass..."

---

## 14. Design-Entscheidungen (2026-02-15 entschieden)

| Entscheidung | Wahl | Begründung |
|--------------|------|------------|
| **Event-Transport** | WebSocket | Bidirektional, Real-time, HA-pushed Events, passt zu neuronalem System |
| **Automation-Erstellung** | Beides | Blueprints für komplexe Automations + 1-Klick-Create für einfache Vorschläge |
| **Scope-Modell** | Area/Person-spezifisch | Nutzt vorhandenes MUPL (v0.8.0) und Habitus Zones (v2) |
| **Token** | X-Auth-Token | Überall (API + Webhook callbacks) |

### Implementierung Scope-Modell
```
Vorschlag → Scope prüfen (area/person) → MUPL-Gewichtung → Personalisierter Vorschlag
```

---

## 15. Nächste Schritte

1. **Interactive Brain Graph Panel** – Visualisierung im Dashboard
2. **Multi-user Learning** – Unterschiedliche Nutzer profile
3. **Performance-Optimierung** – Caching, Query-Optimierung
4. **OpenAPI-Spec** – API-Verträge zwischen Core und HA Integration

---

*Dieses Dokument ist die konsolidierte Wahrheit. Bei Widersprüchen mit anderen Dokumenten gilt dieses.*