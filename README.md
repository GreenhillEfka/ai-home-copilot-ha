# PilotSuite — Styx: HACS Integration

[![Release](https://img.shields.io/github/v/release/GreenhillEfka/pilotsuite-styx-ha)](https://github.com/GreenhillEfka/pilotsuite-styx-ha/releases)
[![HACS](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)

**PilotSuite** — Privacy-first, lokaler KI-Assistent für Home Assistant mit Brain Graph, Habitus Pattern Learning, Mood Engine und Predictive Automation. Aktuelle Test-Release-Linie: **v13.5.7**.

---

## 🏠 Was ist PilotSuite?

PilotSuite ist eine **vollständige Home Assistant Integration** mit:

- 🧠 **94+ Sensoren** (Brain Graph, Habitus, Mood, Energy, etc.)
- 🎨 **15+ Dashboard Cards** (Habitus Dashboard, Brain Graph Panel, etc.)
- 🤖 **23 Core Module** (Agent Auto Config, Connection Config, etc.)
- 🔒 **Zero-Config Setup** (Auto-Discovery)
- 👥 **Multi-User Preference Learning**

---

## 📦 Installation

### **Option 1: HACS (Empfohlen)**

1. **HACS installieren** (falls noch nicht vorhanden)
   - Home Assistant → HACS → Integrationen
   - "Custom Repository" hinzufügen

2. **PilotSuite Repository hinzufügen**
   - HACS → Integrationen → ⋮ (Menü) → Custom repositories
   - Repository: `https://github.com/GreenhillEfka/pilotsuite-styx-ha`
   - Category: Integration

3. **PilotSuite installieren**
   - HACS → Integrationen → PilotSuite
   - Klick auf "Install"
   - Home Assistant neu starten

4. **Integration einrichten**
   - Home Assistant → Einstellungen → Geräte & Dienste
   - "Integration hinzufügen" → PilotSuite
   - Folge dem Einrichtungs-Assistenten

---

### **Option 2: Manuell**

1. **Files kopieren**
   ```bash
   cp -r custom_components/copilot_ha /config/custom_components/
   ```

2. **Home Assistant neu starten**

3. **Integration einrichten**
   - Home Assistant → Einstellungen → Geräte & Dienste
   - "Integration hinzufügen" → PilotSuite

---

## 🔧 Voraussetzungen

### **Core Backend (ERFORDERLICH)**

PilotSuite benötigt das **PilotSuite Core Backend** (separates Add-on, aktuelle Test-Release-Linie **v13.5.7**):

- **Repository:** https://github.com/GreenhillEfka/pilotsuite-styx-core
- **Installation:**
  1. Home Assistant → Einstellungen → Add-ons → Add-on Store
  2. ⋮ (Menü) → Repositories → URL hinzufügen:
     ```
     https://github.com/GreenhillEfka/pilotsuite-styx-core
     ```
  3. **PilotSuite Core** installieren und starten
  4. Core läuft auf Port **8909**

### **Abhängigkeiten**

- Home Assistant ≥ 2024.1.0
- Python ≥ 3.11
- Conversation Integration (built-in)
- History Integration (built-in)
- Recorder Integration (built-in)

---

## 🎯 Features

### **Sensoren (94+)**

| Kategorie | Sensoren |
|-----------|----------|
| **Brain Graph** | Neuron States, Connections, Graph Metrics |
| **Habitus** | Zone States, Room Metrics, Pattern Recognition |
| **Mood Engine** | Stimmung, Kontext, Emotionen |
| **Energy** | Verbrauch, Vorhersagen, Optimierung |
| **System** | API Status, Cache, Performance |

### **Dashboard Cards (15+)**

- **Habitus Dashboard** — 10 Zonen live visualisieren
- **Brain Graph Panel** — Neuronales Netzwerk anzeigen
- **Mood Timeline** — Stimmungsverlauf
- **Energy Forecast** — Verbrauchsprognosen
- **Agent Status** — Alle Agents im Überblick
- **Styx Dashboard Link** — Direkte Verknüpfung zum Styx SPA (Musikwolke, Vorschläge, Chat)

### **Automationen**

- **Predictive Automation** — Vorausschauende Automatisierungen
- **Pattern Learning** — Lernt deine Gewohnheiten
- **Context-Aware** — Reagiert auf Kontext
- **Multi-User** — Unterscheidet Bewohner

---

## 🔌 Services

PilotSuite stellt folgende Services bereit:

| Service | Beschreibung |
|---------|-------------|
| `copilot_ha.evaluate_zone` | Bewertet eine Habituszone |
| `copilot_ha.trigger_automation` | Löst Automation aus |
| `copilot_ha.query_brain_graph` | Fragt Brain Graph ab |
| `copilot_ha.update_mood` | Aktualisiert Stimmung |
| `copilot_ha.sync_core` | Sync mit Core Backend |

---

## 📊 Architecture

```
Home Assistant
├── PilotSuite HACS Integration (copilot_ha)
│   ├── 94+ Sensoren
│   ├── 15+ Dashboard Cards
│   ├── 23 Core Module
│   └── HTTP REST API (Token-Auth)
│       ↓
└── PilotSuite Core Add-on (Port 8909)
    ├── Brain Graph Engine
    ├── Habitus Pattern Learning
    ├── Mood Engine
    ├── LLM Provider Chain
    ├── Tool Calling
    └── Ollama (bundled, lokal)
```

---

## 🔗 Links

| Resource | URL |
|----------|-----|
| **GitHub (HA)** | https://github.com/GreenhillEfka/pilotsuite-styx-ha |
| **GitHub (Core)** | https://github.com/GreenhillEfka/pilotsuite-styx-core |
| **Issues** | https://github.com/GreenhillEfka/pilotsuite-styx-ha/issues |
| **Documentation** | https://github.com/GreenhillEfka/pilotsuite-styx-ha/docs |

---

## 📝 Changelog

Siehe [CHANGELOG.md](CHANGELOG.md) für alle Änderungen.

---

## 🙏 Credits

- **Developer:** GreenhillEfka
- **License:** MIT
- **Community:** Home Assistant Forum

---

**PilotSuite — Smart Home Intelligence with ML, Anomaly Detection & Predictive Automation** 🧠✨
