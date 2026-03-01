# PilotSuite UX/Frontend Prioritäten

**Erstellt:** 1. März 2026  
**Priorität:** P0 — Muss von Anfang an funktionieren  
**Vision:** Benutzerfreundliche Installation & Bedienung ab Tag 1

---

## 🎯 Kern-Anforderungen

### 1. **Zero-Config Installation**
- [ ] Automatische HA-Instanz-Erkennung (Zeroconf/mDNS)
- [ ] Auto-Tag-System für Entities (Klassifizierung ohne Nutzer-Input)
- [ ] Beispiel-Konfiguration basierend auf **echter HA-Instanz** laden
- [ ] Editierbar im Nachgang (alle Zuweisungen korrigierbar)

### 2. **Zonen-Verwaltung (Backend + Frontend)**

**Backend:**
- [ ] Zone Store v2 mit Tag-System Integration
- [ ] Entity-Zuweisung korrigierbar (UI + API)
- [ ] Zonen-Namen änderbar
- [ ] Auto-Tags manuell überschreibbar

**Frontend:**
- [ ] Zonen-Dashboard (alle Zonen im Überblick)
- [ ] Zone-Editor (Entities hinzufügen/entfernen)
- [ ] Tag-Übersicht pro Zone
- [ ] Zone-Status (aktiv, inaktiv, Personen, Mood)

### 3. **Styx Dashboard Tab**

**Visualisierung:**
- [ ] **Aktives Neuronen-Brain** (welche Neuronen feuern gerade?)
- [ ] **Kommunikations-Pipeline** (HA → Core → Webhook → HA)
- [ ] **System-Zustände** (Mood: Comfort/Joy/Frugality, Confidence)
- [ ] **Live-Events** (was passiert gerade im System?)

**Chat-Interface:**
- [ ] Chat-History (vergangene Konversationen)
- [ ] Tool-Calling Visualisierung (welche Actions wurden ausgeführt?)
- [ ] Kontext-Anzeige (welche Entities/Zonen waren relevant?)

**Handlungsempfehlungen (Side-Panel):**
- [ ] **Phase 1:** Bestehende Automationen analysieren & Fehler melden
- [ ] **Phase 2:** Optimierungsvorschläge (Energie, Komfort)
- [ ] **Phase 3:** Habitus-basierte Vorschläge (nach Lernphase)
- [ ] Jede Empfehlung mit: Begründung, Auswirkung, Accept/Reject

### 4. **Installations-Routine**

**Schritt-für-Schritt:**
1. HA-Instanz erkennen (Auto)
2. Entities auslesen & auto-taggen
3. Zonen vorschlagen (basierend auf Entity-Gruppierung)
4. Nutzer bestätigt/korrigiert Zonen
5. Beispiel-Automationen laden (editierbar)
6. Styx Dashboard aktivieren
7. Ready!

**Dauer:** < 5 Minuten für Standard-Setup

---

## 📊 Research-Aufträge

### @styx — HA-Instanz Analyse
- [ ] Entities auslesen (Typ, Domain, Attributes)
- [ ] Bestehende Zonen erfassen
- [ ] Automationen analysieren (Trigger, Conditions, Actions)
- [ ] User-Präferenzen erkennen (welche Entities werden oft genutzt?)

### @cowdya — Frontend Implementation
- [ ] Dashboard Tab Struktur (Lovelace oder Custom Panel?)
- [ ] Neuronen-Visualisierung (Canvas, SVG, oder Chart?)
- [ ] Chat-Interface (History, Context, Tool-Calls)
- [ ] Zone-Editor (Drag & Drop, Tag-Selection)

### @groky — Review & UX-Testing
- [ ] Installation testen (frisches HA, keine Vorkonfiguration)
- [ ] Zeit messen (Ziel: < 5 Min bis ready)
- [ ] Fehler-Szenarien dokumentieren
- [ ] Accessibility-Check (Screen Reader, Keyboard-Navigation)

---

## 🎨 Design-Prinzipien

1. **Progressive Disclosure** — Zeige nur was relevant ist
2. **Safe Defaults** — Vorschläge sind nie automatisch aktiv
3. **Undo-Friendly** — Jede Änderung reversibel
4. **Transparent** — Nutzer sieht immer was Styx tut & warum
5. **Lernfähig** — System verbessert Vorschläge mit der Zeit

---

## 📈 Erfolgskriterien

| Kriterium | Ziel | Messung |
|-----------|------|---------|
| Installation Duration | < 5 Min | Time-to-Ready |
| Manual Corrections | < 3 pro Setup | User-Actions |
| Dashboard Load Time | < 2 Sek | Performance |
| User Satisfaction | > 80% | Feedback-Survey |
| Error Rate | < 5% | Failed-Setups |

---

## 🔄 Integration in Dev-Workflow

**Nächste 3 Iterationen (20-Min-Takt):**

| Iteration | Fokus | Deliverable |
|-----------|-------|-------------|
| **11:00** | HA-Instanz Analyse | Entity-List, Zone-Vorschläge, Automation-Report |
| **11:20** | Zero-Config Setup | Auto-Tag-System, Example-Config Generator |
| **11:40** | Dashboard Tab v1 | Neuronen-Visualisierung, System-Status |
| **12:00** | Chat-Interface v1 | History, Context, Tool-Calls |
| **12:20** | Zone-Editor v1 | Editierbare Zuweisungen, Tag-System |
| **12:40** | Handlungsempfehlungen v1 | Automation-Analyse, Fehler-Detection |

**Review nach jeder Iteration durch @groky**
**Final Release durch @clawdya**

---

**Erstellt:** 1. März 2026  
**Status:** 🟢 Aktiv (P0)  
**Nächste Iteration:** 11:00 Uhr
