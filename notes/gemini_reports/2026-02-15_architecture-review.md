# Architektur-Review: PilotSuite
**Datum:** 2026-02-15 00:15 (Europe/Berlin)
**Modell:** Gemini CLI (gemini-2.5-pro)
**Umfang:** HA Integration + Core Add-on Cross-Repo Analyse

---

## Zusammenfassung

Die Architektur des PilotSuite basiert auf einer soliden Trennung zwischen der Core-Logik (dem "Add-on", `copilot_core`) und der Präsentationsschicht (der Home Assistant Integration). Die Core-Logik ist konzeptionell reich und modular aufgebaut (Brain Graph, Habitus, Neuronen). Die HA-Integration agiert jedoch nur als ein sehr dünner Client, der lediglich den Status und die Version des Cores anzeigt. Die eigentliche Funktionalität des Cores (Neuronen, Moods, etc.) wird in der HA-UI nicht abgebildet.

Das größte Problem ist die brüchige und inkonsistente API zwischen den beiden Komponenten. Es gibt klare Anzeichen für technische Schulden und einen Mangel an synchronisierter Entwicklung, was zu Instabilität und zukünftigen Fehlern führen wird.

---

## KRITISCH (Muss behoben werden)

### 1. Inkonsistente & fragile API-Kommunikation

Sowohl der Polling-Client (`api.py`) als auch der Webhook-Handler (`webhook.py`) in der HA-Integration enthalten spezielle Logik, um unterschiedliche JSON-Strukturen für dieselben Daten (Version, Status) zu parsen (z.B. `{"version": "x"}` vs. `{"data": {"version": "x"}}`).

**Problem:** Dies ist ein klares Symptom für einen Mangel an festen API-Verträgen und Versionierung. Änderungen am Core-API-Format scheinen nicht sauber in der Integration nachgezogen zu werden. Dies führt zwangsläufig zu Fehlern, erhöht die Komplexität und den Wartungsaufwand.

### 2. Fehlende funktionale Integration

Die HA-Integration verarbeitet aktuell nur `online`-Status und `version`-Informationen vom Core. Die gesamte reichhaltige Logik (Neuronen, Mood, Habitus-Muster, Brain Graph) wird **nicht** in Home Assistant repräsentiert.

**Problem:** Die Integration erfüllt ihren Zweck nicht. Der Benutzer kann in Home Assistant nicht mit den Kernfunktionen des Copiloten interagieren. Der Mehrwert der komplexen Core-Logik geht für den Endanwender verloren.

---

## WICHTIG (Sollte behoben werden)

### 1. Inkonsistente Implementierung des "Neuron"-Konzepts

Die Dokumentation beschreibt "Neuronen" als fundamentales Architekturkonzept. Bestehende Analyse-Reports weisen darauf hin, dass eine `BaseNeuron`-Abstraktionsklasse fehlt.

**Problem:** Ohne eine gemeinsame Basisklasse wird die Implementierung neuer Neuronen inkonsistent, was zu Code-Duplizierung und erhöhtem Wartungsaufwand führt. Die Architektur-Idee wird nicht sauber im Code abgebildet.

### 2. Technische Schulden im Core

Die Analyse-Logs zeigen konkrete Beispiele für technische Schulden, wie die Inkonsistenz bei der Benennung von `BrainGraphStore` vs. `GraphStore`.

**Problem:** Solche Inkonsistenzen erschweren das Onboarding neuer Entwickler, führen zu Verwirrung und können Laufzeitfehler verursachen.

### 3. Sicherheit des Webhooks

Der Webhook ist durch ein Token geschützt, was grundsätzlich gut ist. Die URL ist jedoch potenziell öffentlich erreichbar.

**Problem:** Sollten zukünftig sensible Daten über den Webhook übertragen werden, reicht ein einfaches Token nicht aus. Es fehlen robustere Sicherheitsmechanismen (z.B. signierte Payloads).

---

## EMPFEHLUNG (Nice-to-have)

### 1. API-Spezifikation formalisieren

Führen Sie eine formale API-Spezifikation wie **OpenAPI (Swagger)** ein. Dies sollte im `ha-copilot-repo` (Core) angesiedelt sein.

**Vorteil:** Dies schafft einen klaren, versionierten Vertrag zwischen Core und Integration. Es ermöglicht die automatische Generierung von Client-Code und verhindert die aktuell beobachteten API-Inkonsistenzen.

### 2. Funktionale Erweiterung der HA-Integration

Implementieren Sie Entitäten (Sensoren, Binärsensoren) und Dienste in der HA-Integration, die den Zustand und die Ergebnisse der Neuronen, des Mood-Systems und der Habitus-Muster abbilden.

**Beispiele:**
- `sensor.copilot_mood` → aktuelle Stimmung
- `binary_sensor.habitus_pattern_coffee` → Kaffeemuster erkannt
- `copilot.force_habitus_mining` → Mustererkennung manuell anstoßen

### 3. Repository-Struktur überdenken

Die Trennung in `ai_home_copilot_custom_component`, `ai_home_copilot_hacs_repo` und `ha-copilot-repo` scheint die Entwicklung zu verlangsamen und Inkonsistenzen zu fördern. Prüfen Sie den Umstieg auf ein **Monorepo**.

**Vorteil:** Änderungen an der API und der Implementierung können in einem einzigen, atomaren Commit über beide Komponenten hinweg durchgeführt werden, was die Synchronisation sicherstellt.

---

## POSITIV (Was gut läuft)

### 1. Saubere Architekturtrennung (Separation of Concerns)

Die Aufteilung in einen potenten, zustandslosen Logik-Core und eine "dumme" HA-Integrationsschicht ist ein exzellentes und skalierbares Architekturmuster.

### 2. Modulare Core-Struktur

Die Core-Logik ist in klar abgegrenzte Module (`BrainGraph`, `Habitus`, `Mood`, `Candidates`) unterteilt. Dies fördert die Wartbarkeit und Erweiterbarkeit des Systems.

### 3. Effiziente Push-Kommunikation

Die Verwendung von Webhooks für Status-Updates vom Core zur Integration ist die richtige Wahl. Es ist effizienter als ständiges Polling und ermöglicht Echtzeit-Updates.

### 4. Best Practices in der Integration

Die Nutzung des `DataUpdateCoordinator` in der HA-Integration ist eine etablierte Best Practice und sorgt für eine robuste Handhabung von Datenabrufen.

### 5. Hoher Grad an Selbstreflexion

Das Projekt verfügt über eine beeindruckende Menge an interner Dokumentation, Entscheidungs-Logs und Architektur-Reviews. Dies ist ein Zeichen für einen reifen Entwicklungsprozess.

---

## Action Items (Priorisiert)

| Prio | Issue | Lösung |
|------|-------|--------|
| 🔴 Kritisch | API-Inkonsistenz | OpenAPI-Spec definieren, Client generieren |
| 🔴 Kritisch | Fehlende HA-Entitäten | Mood-Sensor, Neuron-Sensoren implementieren |
| 🟡 Wichtig | Fehlende BaseNeuron | Abstrakte Basisklasse erstellen |
| 🟡 Wichtig | Naming-Inkonsistenzen | Refactoring BrainGraphStore vs GraphStore |
| 🟢 Empfehlung | Monorepo | Repos zusammenführen für sync'd Development |