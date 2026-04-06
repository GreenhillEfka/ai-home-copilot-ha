# PilotSuite Core

[![HACS](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)
[![Version](https://img.shields.io/badge/version-1.0.0--rc2-blue)](https://github.com/GreenhillEfka/pilotsuite-styx-ha/releases)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

**AI-Powered Smart Home Automation Platform**

---

## 🚀 Features

### Core Capabilities

- **🧠 RAG System** — Vector search, embeddings, semantic retrieval
- **🤖 ML Engine** — Pattern detection, habit learning, anomaly detection
- **🏠 Presence Detection** — Multi-sensor fusion, Bayesian inference, Wilson Score
- **⚡ Energy Optimization** — LSTM forecasting, OR-Tools scheduler, load shifting
- **🧠 Knowledge Graph** — Neo4j/NetworkX, temporal reasoning, SPARQL-like queries
- **🎤 Voice Pipeline** — Whisper STT, NLU, Piper TTS, emotion recognition
- **📊 Admin Dashboard** — Real-time monitoring, analytics, Lovelace cards
- **🔌 REST API** — FastAPI server, JWT auth, 25+ endpoints
- **🔒 Security** — Encrypted storage, audit logging, rate limiting

### Home Assistant Integration

- Custom entities (sensors, buttons, switches)
- Lovelace dashboard cards (9 custom cards)
- Habitual zone automation
- Brain Graph visualization
- Real-time WebSocket commands

---

## 📦 Installation

### Via HACS (Recommended)

1. Open HACS in Home Assistant
2. Go to **Integrations** → **⋮** → **Custom repositories**
3. Add repository: `https://github.com/GreenhillEfka/pilotsuite-styx-ha`
4. Select category: **Integration**
5. Click **Add**
6. Search for "PilotSuite Core" and install
7. Restart Home Assistant
8. Go to **Settings** → **Devices & Services** → **Add Integration** → **PilotSuite Core**

### Manual Installation

```bash
# SSH into Home Assistant
cd /config/custom_components
git clone https://github.com/GreenhillEfka/pilotsuite-styx-ha.git pilotsuite

# Add to configuration.yaml
pilotsuite:
  # Optional configuration
  debug: false
  llm_model: ollama/qwen3.5:397b-cloud
```

---

## ⚙️ Configuration

### Basic Configuration

```yaml
pilotsuite:
  debug: false                    # Enable debug logging
  llm_model: ollama/qwen3.5:397b-cloud  # Default LLM model
  data_dir: /config/pilotsuite    # Data directory
```

### Advanced Configuration

```yaml
pilotsuite:
  # RAG Configuration
  rag:
    vector_store: faiss
    embedding_model: sentence-transformers/all-MiniLM-L6-v2
    dimension: 384
  
  # ML Configuration
  ml:
    pattern_min_confidence: 0.6
    habit_learning_enabled: true
  
  # Presence Configuration
  presence:
    sensors:
      - pir.living_room
      - radar.bedroom
      - wifi.fingerprinting
    wilson_confidence: 0.95
  
  # Energy Configuration
  energy:
    forecasting_enabled: true
    scheduler_enabled: true
    devices:
      - wallbox.ev_charger
      - climate.heat_pump
      - battery.home
  
  # API Configuration
  api:
    enabled: true
    host: 0.0.0.0
    port: 8080
    jwt_expiry_hours: 24
    rate_limit_requests: 100
```

---

## 🔌 Services

### `pilotsuite.learn_pattern`

Learn automation pattern from user behavior.

```yaml
service: pilotsuite.learn_pattern
data:
  user_id: user_1
  trigger:
    type: state
    entity_id: light.living_room
    to: "on"
  action:
    entity_id: climate.living_room
    service: climate.set_temperature
    data:
      temperature: 22
```

### `pilotsuite.get_suggestions`

Get automation suggestions.

```yaml
service: pilotsuite.get_suggestions
data:
  context:
    time_of_day: morning
    occupancy: home
```

### `pilotsuite.optimize_energy`

Run energy optimization.

```yaml
service: pilotsuite.optimize_energy
data:
  devices:
    - wallbox.ev_charger
    - climate.heat_pump
  horizon_hours: 24
```

---

## 📊 Lovelace Cards

### Brain Graph Card

```yaml
type: custom:pilotsuite-brain-graph
title: Knowledge Graph
height: 400
```

### Habit Pattern Card

```yaml
type: custom:pilotsuite-habit-pattern
entity: sensor.habit_patterns
show_history: true
```

### Energy Optimization Card

```yaml
type: custom:pilotsuite-energy-optimization
devices:
  - wallbox.ev_charger
  - climate.heat_pump
show_forecast: true
```

---

## 🔧 API Usage

### Authentication

```bash
# Get JWT token
curl -X POST http://localhost:8080/api/v1/auth/token \
  -H "Content-Type: application/json" \
  -d '{"api_key": "your_api_key", "scope": "read"}'
```

### Event Ingestion

```bash
# Create event
curl -X POST http://localhost:8080/api/v1/events \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"type": "motion", "entity_id": "pir.living_room"}'
```

### Vector Search

```bash
# Similarity search
curl -X GET http://localhost:8080/api/v1/vector/similar/entity_123 \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Knowledge Graph

```bash
# Query graph
curl -X POST http://localhost:8080/api/v1/kg/query \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query": "SELECT ?e WHERE { ?e type \"device\" }"}'
```

---

## 🧪 Testing

```bash
# Run tests
pytest copilot_core/ -v

# With coverage
pytest copilot_core/ --cov=copilot_core --cov-report=html

# Specific test suite
pytest copilot_core/rag/tests/test_vector_store.py -v
pytest copilot_core/presence/tests/test_presence.py -v
pytest copilot_core/brain/tests/test_brain_graph_store.py -v
```

---

## 📖 Documentation

- **[Installation Guide](docs/INSTALL.md)** — Detailed installation steps
- **[API Reference](docs/API_REFERENCE.md)** — Complete API documentation
- **[Troubleshooting](docs/TROUBLESHOOTING.md)** — Common issues and solutions
- **[Changelog](CHANGELOG.md)** — Version history

---

## 🤝 Contributing

Contributions are welcome! Please read our [Contributing Guidelines](CONTRIBUTING.md) first.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- Home Assistant team for the amazing platform
- Ollama for local LLM inference
- OpenAI Whisper for STT
- Piper for TTS
- Google OR-Tools for optimization
- Neo4j for graph database
- FastAPI for the web framework

---

**Built with ❤️ by the PilotSuite Team**
