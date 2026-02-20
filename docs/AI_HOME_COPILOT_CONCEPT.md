# AI Home CoPilot – Gesamtkonzept, Architektur & Workflow

> **Ziel dieses Dokuments**  
> Dieses Dokument ist die **vollständige, konsolidierte Konzeptbeschreibung** des AI Home CoPilot – extrahiert aus allen bisherigen Chatverläufen (plus bereits getroffene, dokumentierte Setup‑Entscheidungen in diesem Repo). Es beschreibt **Architektur, Module, neuronales Modell, Workflows, Betriebsmodi und Schlussfolgerungen**.
>
> Es ist **kein Implementierungsleitfaden**, sondern eine **strategisch‑technische Blaupause**, die später in Code, Dashboards und Add-ons überführt werden kann.

---

## 1. Grundidee & Positionierung
Der **AI Home CoPilot** ist ein **systemischer Entscheidungs‑ und Vorschlagslayer** über Home Assistant. Er ist:

- kein monolithisches KI‑System
- kein autonomer Smart‑Home‑Controller
- keine Blackbox‑Automation

Sondern:

> Ein **erklärbares, neuronales Orchestrierungssystem**, das Sensorik, Kontext, Stimmung, Historie und Nutzerintention zusammenführt und daraus **gewichtete Vorschläge** ableitet.

**Home Assistant bleibt jederzeit das führende System.**

---

## 2. Leitprinzipien (konsolidiert)
1. **User‑Kontrolle vor Autonomie**  
   Autonomie existiert nur nach expliziter Freigabe.
2. **Erklärbarkeit statt Magie**  
   Jede Entscheidung ist begründbar und (später) visualisierbar.
3. **Modularität auf allen Ebenen**  
   Module, Neuronen, Synapsen, Dienste.
4. **Wachstum statt Re‑Konfiguration**  
   Neue Fähigkeiten ergänzen das System; sie ersetzen es nicht.
5. **KI ist austauschbar**  
   Das System muss auch ohne externes LLM stabil nutzbar sein.
6. **Alles ist beobachtbar**  
   States, Scores, Logs, Historien, Visualisierung.

**Sicherheits‑SOP (aktuelle Arbeitsregel):**  
- Smart‑Home/State‑Changes: *Vorschlag → explizites „Ja“ → Ausführung*  
- Read‑only sofort ok.

---

## 3. Gesamtarchitektur (logische Ebenen)
### 3.1 Ebenenmodell

```text
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

### 3.2 Systemgrenzen (wichtig)
- **Home Assistant**: Quelle der Wahrheit für Geräte/States/Services/Automationen.
- **CoPilot**: interpretiert, erklärt, priorisiert, schlägt vor – führt nur in erlaubten Modi aus.
- **Chat/UI**: primäre Steuerung/Feedback/Erklärbarkeit („Nervensystem“).

---

## 4. Das neuronale Modell (konzeptionell)
### 4.1 Grundannahme
Das neuronale Modell ist **biologisch inspiriert, aber technisch deterministisch**:

- **Neuronen** = bewertende Module
- **Synapsen** = gewichtete Abhängigkeiten
- **Aktivierung** = Score (0.0 – 1.0)
- **Keine Aktion ohne Entscheidungsschicht**

Kein Neuron kennt die Gesamtlogik.

---

## 5. Neuronen – Modulkatalog (konzeptionell)
### 5.1 Kontext-Neuronen (objektiv)
- Presence (Raum, Haus, Person)
- TimeOfDay / DayType
- LightLevel / SunPosition
- Weather / Forecast
- CalendarLoad / Termine
- NoiseLevel
- MediaActivity
- SystemHealth (HA, Netz, Dienste)
- NetworkQuality (WLAN, Thread, Zigbee, Z‑Wave)
- SecurityState

### 5.2 Zustands-Neuronen (glätten, träge)
- EnergyLevel
- StressIndex
- RoutineStability
- SleepDebt
- AttentionLoad
- ComfortIndex

### 5.3 Stimmungsmodule (Mood Layer)
Stimmungen sind **abstrakte Systemzustände**, nicht Emotionen.

**Kern-Moods:**
- mood.relax
- mood.focus
- mood.active
- mood.sleep
- mood.away
- mood.alert
- mood.social
- mood.recovery

Mood-Neuronen sind die **Hauptauslöser für Vorschläge**.

---

## 6. Synapsen – Beziehungsmodell
### 6.1 Definition
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

Synapsen sind **konfigurierbar, visualisierbar und deaktivierbar**.

---

## 7. Entscheidungs‑ & Vorschlagslogik
Der CoPilot **entscheidet nicht**, er **empfiehlt**.

Ergebnis eines Zyklus:
- Vorschlag
- Begründung
- Priorität
- Alternativen
- beteiligte Neuronen

---

## 8. Workflow – End‑to‑End (Chart)

```text
[ Sensor / Event / User-Input ]
          ↓
[ Kontext-Neuronen aktualisieren ]
          ↓
[ Zustands-Neuronen glätten ]
          ↓
[ Mood-Neuronen aggregieren ]
          ↓
[ Synapsen evaluieren ]
          ↓
[ Vorschläge generieren ]
          ↓
[ Chat & UI anzeigen ]
          ↓
[ Nutzerentscheidung ]
     ↓           ↓
 [Ablehnen]   [Freigeben]
                 ↓
        [ Aktion / Automation ]
                 ↓
        [ Logging & Lernen ]
```

---

## 9. Chat‑Interface als zentrales Nervensystem
Der Chat ist:
- Eingabe
- Erklärung
- Steuerung
- Lernfreigabe

Typische Interaktionen:
- „Was machst du gerade?“
- „Warum schlägst du das vor?“
- „Mach das künftig automatisch.“
- „Zeig mir dein Gehirn.“

---

## 10. Visualisierung – das wachsende Gehirn
### 10.1 Bedeutung
Die Visualisierung ist **kein Gimmick**, sondern:
- Debug‑Werkzeug
- Lern‑Interface
- Vertrauensanker

### 10.2 Darstellung
- Neuronen = Knoten
- Synapsen = Linien
- Aktivität = Puls / Farbe
- Gewicht = Linienstärke

### 10.3 Wachstum
- Neue Module → neue Neuronen
- Neue Regeln → neue Synapsen
- Lernprozesse → veränderte Gewichte

---

## 11. Betriebsmodi
### Manual Mode (Default)
- Alles sichtbar
- Nichts automatisch
- Volle Kontrolle

### Assisted Mode
- Vorschläge priorisiert
- Teilautomatik nach Freigabe

### Auto Mode (explizit)
- Definierte Synapsen dürfen auslösen
- Vollständiges Logging
- Jederzeit rücknehmbar

---

## 12. Logging, Historie & Nachvollziehbarkeit
Zu loggen:
- Bewertung pro Neuron
- Auslösung pro Synapse
- Entscheidungshistorie
- Nutzerreaktionen
- Lernverlauf

Diese Daten sind Grundlage für:
- Vertrauen
- Optimierung
- spätere KI‑Unterstützung

---

## 13. Zentrale Konklusionen
1. **Autonomie ohne Transparenz ist nicht akzeptabel**
2. **Das Gehirn‑Modell schafft Vertrauen und Verständnis**
3. **Mood‑Layer ist entscheidender als einzelne Sensoren**
4. **Chat ist die wichtigste Schnittstelle**
5. **Visuelle Rückkopplung beschleunigt Akzeptanz**
6. **Modularität ist zwingend für Langzeitpflege**

---

## 14. Fazit
Der AI Home CoPilot ist ein **lebendes, wachsendes Entscheidungssystem**, das Smart Home von einer regelbasierten Automatik zu einem **kontextbewussten, erklärbaren Assistenzsystem** entwickelt.

Er denkt nicht für den Nutzer – **er denkt mit ihm.**

---

## Anhang A: Aktueller Projektstatus / Setup (kurz, nicht normativ)
> Dieser Anhang ist **keine Implementierungsanleitung** – nur der aktuelle Stand, damit Konzept und Realität nicht auseinanderlaufen.

- Kommunikation: Telegram DM‑Pairing.
- Sicherheit: „erst fragen, dann ausführen“ bei allen state‑ändernden HA‑Aktionen.
- Gruppen in HA: immer Mitglieder/Segmente einzeln setzen.
- Recherche: Perplexity direct (on-demand) via `pplx:` (quick) und `pplx-deep:` (deep), Antworten erzwungen auf Deutsch.
