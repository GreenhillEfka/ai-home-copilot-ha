# UX-Designsystem — Dashboard (PilotSuite Styx)

**Status:** Entwurf v1.0
**Kontext:** Dashboard-Darstellung für Habitus, Brain, Zonen, Mood und Echtzeit-Aggregation.
**Ort:** `/dashboard/static/` Frontend-Experience.

Dieses Dokument definiert Design-Prinzipien, die bewusst über klassische Smart-Home-Visualisierung hinausgehen: nicht nur Anzeigen, sondern ein interpretierbares „Cognition Interface“ — schnell, erklärbar und handlungsfähig.

## 0) Leitprinzipien (über den Stand hinaus)

1. **Cognitive Compression statt Datenlawine**  
   Komplexe Ereignisse werden zuerst als *Entscheidungsrelevanz* statt als Rohwerte gezeigt.

2. **Semantic Motion-First**  
   UI reagiert auf Bedeutung (z. B. „Stimmung kippt“ oder „Zone driftet“), nicht auf statische Polling-Updates.

3. **Hierarchie aus drei Ebenen**  
   - **Globaler Überblick** (Systemzustand)
   - **Räumliche Ebene** (Zone)
   - **Modul-Ebene** (Licht/Klima/Media/...).

4. **Explainability by default**  
   Jede aggregierte Aussage braucht einen „Warum“-Pfad.

5. **Latency als UX-Charakteristikum**  
   Die UI kommuniziert Frische/Unsicherheit bewusst (z. B. „2.3 s alt“, „geringe Konfidenz“).

6. **Actionability**  
   Jede Karte erzeugt mindestens einen direkt nutzbaren Eingriff (quick action, Kontext-Panel, Vorschlagsautomatik).

7. **Adaptive Dichte**  
   Bei hoher Update-Rate werden Details verdichtet, nicht unkontrolliert erweitert.

8. **Zero-Trust-UX für Datenintegrität**  
   Schema-gesicherte Konfiguration und Validierung verhindern inkonsistente Panels.

9. **Zentrierte visuelle Grammatik**  
   Einheitliche Typografie, Chips, Statusfarben, Bewegungen und Interaktionsrhythmen für alle Kartenfamilien.

10. **Fail-soft Design**  
    Bei Ausfällen werden Kernaussagen degrade-stabil gehalten (z. B. letzte validierte Werte + Stale-Hinweis).

---

## 1) Habitus-Visualisierung

### Zielbild
Habitus visualisiert **„Wohnen als veränderlicher Lebenszustand“** statt als isolierte Metrik:
- **Zeitachse**: 24h/7d Zustandstrends (Komfort, Präsenz, Aktivitätsdruck)
- **Pattern-Layer**: Wiederkehrende Sequenzen als Kartenkacheln (z. B. „Abendruhe → Präsenz im Wohnzimmer → Licht runter“)
- **Confidence-Layer**: jede Aussage zeigt Verlässlichkeit (Transparenz über Datenhärte)

### Regeln
- **Fokusregel:** Erst Zone-Score + Aktivitätsdruck, danach Detail-Module.
- **Causal Breadcrumbs:** Jede Mustererkennung bietet `Auslöser → Auswirkung → Ergebnis`.
- **Entscheidungs-Hintergrund:** Karten können automatisch „störungsgefährdete“ Muster hervorheben.
- **Interaktion:** Klick auf Muster öffnet Kontextpfad inkl. letzter 5 relevantes Ereignisse.

### Design-Muster
- Verlaufsspur mit farbcodiertem Spannungsindikator.
- „Zone-Match“ als Heat-Layer: wie gut aktueller Zustand zu gewohnten Mustern passt.
- Mini-Timeline als Atemrhythmus: ruhige/aktive/instabile Zonen sind visuell unterscheidbar.

---

## 2) Brain-View

### Zielbild
Brain-View ist ein **interaktiver Wissensraum**, nicht nur ein statisches Diagramm.
- Knoten repräsentieren Entitäten/Neuron-Gruppen/Module.
- Kanten repräsentieren Interaktionen, Stärke = Relevanz, Farbe = Semantikklasse.
- Positionsänderung zeigt dynamische Wichtigkeit (Recent Activity).

### Regeln
- **3D-ähnliche Tiefenwirkung ohne echte 3D-Last:** Parallaxe, Fokus-/Ausblenden, Tiefenunschärfe.
- **Intent-Filtern:** Vorschläge nach Kategorie (Sicherheit, Komfort, Energie, Routine).
- **Prediktion als Overlays:** Knoten erhalten kleine Zukunfts-Vektoren („wohin verschiebt sich die Aktivität als Nächstes?“).
- **Erklärbarkeit:** Edge-Hover zeigt `Wann`, `Warum`, `Wie oft`, `Letzte Änderung`.

### Advanced-Features (state-of-the-art+)
- **Temporal Edge Aging:** veraltete Beziehungen verblassen, frische werden animiert.
- **Context Switch:** Umschalten zwischen `live`, `trend`, `drift` Ansicht.
- **Incident Lens:** temporärer Fokusmodus bei Alarmzuständen mit reduzierter visueller Last.

---

## 3) Zone-Module-Cards

### Zielbild
Zone-Module-Cards sind **modulare, austauschbare UI-Moleküle**.
Jede Zone besteht aus:
- **Header-Layer:** Zone-Identität, Zustand, Kurzrisiko
- **Module-Layer:** aktive Module als Chips/Kacheln (Licht, Musik, Klima, Cover, Energie, Szene, Sicherheit)
- **Action-Layer:** Direktsteuerung und Fokusaktionen
- **Health-Layer:** Modulzustände + Konsistenzscore

### Regeln
- **Komposition statt Monolith:** Jede Zone = konsistente Template-Karte + Modul-Slots.
- **Präferenz-Priorisierung:** Module zeigen zuerst nach Risiko/Impact (z. B. Sicherheit vor Komfort).
- **Fehler-zuweisung:** Bei Konflikten wird sichtbar, welches Modul die Inkonsistenz erzeugte.
- **Vergleichbarkeit:** Gleiche Module besitzen denselben visuellen Vertrag (Farblegende, Toggle-Pattern, Tooltips).

### Verbindungsprinzip
- Eine Zone-Card enthält nur die Module, die aktuell *semantisch aktiv* sind.
- Deaktivierte Module bleiben als reduzierte Platzhalter sichtbar (für Orientierung, nicht für Lärm).

### Umsetzungshinweise
- Das Karten-Editing basiert auf den bestehenden Helper/Validator-Pfaden:
  - **PS-198**: `dashboard/static/utils/card-form-helper.ts` (schema-first Form-Aufbau)
  - **PS-199**: `dashboard/static/cards/styx-zone-creator-card.ts` (modulare Zonenfelder als Vorbild)
  - **PS-200**: `dashboard/static/utils/editor-schema-validation.ts` (Strict-Validierung gegen Config-Durchsetzungsregeln)

---

## 4) Mood-Panels

### Zielbild
Mood-Panels sind kein „Smileys-Widget“, sondern ein **emotionales Zustandsmonitoring mit Handlungsbezug**.
- **Global Panel:** Gesamtstimmung + globale Unsicherheit.
- **Zone Panel:** Stimmungsabweichung je Raum.
- **Historien-Panel:** Verlauf, Trigger-Korrelation, Trendrichtung.
- **Faktoren-Panel:** Top-Macher (welches Modul hat wie viel Einfluss).

### Regeln
- **3D-Mood-Raster statt 1D-Score:** Valenz (positiv/negativ), Aktivierung (ruhig/geladen), Stabilität (wechselhaft/ruhig).
- **Korrelation statt Kausalität:** Erst Hinweise, danach harte Aussagen.
- **Explainability:** Jeder Mood-Shift zeigt Top-Faktoren + nächste erwartete Veränderung.
- **Adaptive Intensität:** Bei hoher Änderung (Spike) wird Panel kurz priorisiert; bei stabilen Phasen ruhiger.

### Advanced-Pattern
- **Mood Diff:** Visualisiert Veränderung pro Zeiteinheit (nicht nur absoluten Wert).
- **Confidence Ring + Uncertainty Fog:** Je niedriger Konfidenz, desto deutlicher „unscharf“.  
- **Interventionshinweise:** panelbasierte Vorschläge (z. B. „lichtdimmung“ bei hoher Aktivierung).

---

## 5) Real-Time-Aggregation

### Zielbild
Echtzeitdaten werden nicht als Einzelereignisse, sondern als **interpretierbare Aggregatsströme** dargestellt.

### Pipeline
1. **Ingest**: Rohereignisse (zone, modul, mood, graph, sensor)
2. **Normalize**: Typ, Zeitslot, Zone-Resolution
3. **Aggregate**: Sliding Windows (5s/30s/5m) je Domäne
4. **Score**: Relevanz + Verlässlichkeit
5. **Render**: Diffing + Batch-Update an betroffene UI-Abschnitte

### Regeln
- **Batch-first rendering:** Updates werden gepackt, erst dann gerendert.
- **Temporal Coalescing:** Gleichzeitige Wiederholungen pro Zone/Modul zusammenfassen.
- **Backpressure handling:** Bei hoher Last Dichte reduzieren (Detailabstufung), nicht UI einfrieren.
- **Clock Awareness:** Jede Card zeigt Altersstempel für letzte vollständige Aggregation.

### Performance-Ziele (Design + UX)
- Update-Frequenz für Live-Elemente: 500ms–2s Fenster je Use-Case.
- Karten-Render-Delta max. auf 250–350 ms UI-Pfadzeit halten (bei normaler Last).
- Re-Render auf betroffene Card-Cluster beschränken.

---

## 6) Qualitätsregeln für alle fünf Bereiche

- **Konsistente Statusfarbe**: ok/warn/critical/unknown identisch über alle Views.
- **Textlänge begrenzen**: lange Labels werden gekürzt + Tooltip mit Volltext.
- **Keyboard-Zugänglichkeit**: Fokuszustand für Karten, Filter, Aktionen.
- **Fallback-Modus**: wenn Aggregation fehlt, zeige letzte gültige Werte + „Daten veraltet“.
- **Versionierte Konfiguration**: Änderungen im UI-Editor nur über validierte Schemata.

---

## 7) Referenzen auf PS-198/199/200

- **PS-198 (Card-Helper)**: Grundlage für modulare Form-/Schema-Definition und wiederverwendbaren Feldbau.
- **PS-199 (Card-Helper-Usage in Zone Creator)**: Referenzmuster für modulare Zonenfelder und Entitätsbindungen.
- **PS-200 (Validation Gate)**: Pflichtvalidierung bei Config-Bau, verhindert Drift zwischen UI-Formular und Runtime-Konfiguration.

Für neue Dashboard-/Card-Features gilt verbindlich:
- Schema zuerst aus dem Helper erzeugen (PS-198)
- Kartentypen über modulare Felder/Slots aufbauen (PS-199)
- Vor Aktivierung strikte Validierung / Drift-Erkennung aktivieren (PS-200)

---

## 8) Deliverable-Klartext

Dieses Dokument ist als Leitfaden für UI/UX-Entwurf und Implementierung im Dashboard gedacht: jede neue Komponente in den Bereichen
`Habitus-Visualisierung`, `Brain-View`, `Zone-Module-Cards`, `Mood-Panels` und `Real-Time-Aggregation` soll diese Prinzipien erfüllen, bevor sie als Release-Feature freigegeben wird.
