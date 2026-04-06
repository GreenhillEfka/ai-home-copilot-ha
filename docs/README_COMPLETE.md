# PilotSuite Core v16.0.0 — Complete Documentation

**Release Date:** 2026-04-07
**Version:** 16.0.0
**Build:** 168H-Massive-Iteration

---

## 📖 TABLE OF CONTENTS

1. [Introduction](#introduction)
2. [Architecture](#architecture)
3. [Installation](#installation)
4. [Configuration](#configuration)
5. [API Reference](#api-reference)
6. [Voice Assistant](#voice-assistant)
7. [Machine Learning](#machine-learning)
8. [RAG System](#rag-system)
9. [UI Components](#ui-components)
10. [Security](#security)
11. [Testing](#testing)
12. [Deployment](#deployment)
13. [Troubleshooting](#troubleshooting)

---

## INTRODUCTION

PilotSuite Core is an AI-powered smart home automation platform featuring:
- **Voice Control** — Local STT/TTS with Whisper & Piper
- **Habit Learning** — ML-based pattern detection and predictive automation
- **RAG System** — Local LLM integration with Ollama
- **Home Assistant Integration** — Full bidirectional sync
- **Production-Grade** — Security, monitoring, high availability

---

## ARCHITECTURE

```
┌─────────────────────────────────────────────────────────────┐
│                    PilotSuite Core v16                       │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │   Voice  │  │    ML    │  │   RAG    │  │   API    │   │
│  │ Pipeline │  │  Engine  │  │  System  │  │ Gateway  │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
├─────────────────────────────────────────────────────────────┤
│                    Home Assistant Bridge                     │
└─────────────────────────────────────────────────────────────┘
```

---

## INSTALLATION

### Prerequisites
- Python 3.10+
- Home Assistant 2024.1+
- Ollama (optional, for local LLM)

### Quick Start
```bash
# Clone repository
git clone https://github.com/GreenhillEfka/pilotsuite-styx-core.git
cd pilotsuite-styx-core

# Install dependencies
pip install -r requirements.txt

# Configure
cp config.example.yaml config.yaml
# Edit config.yaml with your settings

# Start
python -m copilot_core
```

---

## CONFIGURATION

### Core Settings
```yaml
core:
  name: PilotSuite
  version: 16.0.0
  
database:
  url: sqlite:///data/pilotsuite.db
  pool_size: 20
  
ollama:
  base_url: http://localhost:11434
  model: llama3.2
  
voice:
  stt: whisper
  tts: piper
  language: de
  
ml:
  pattern_detection: true
  habit_learning: true
  anomaly_detection: true
```

---

## API REFERENCE

### REST API

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/health` | GET | Health check |
| `/api/v1/rag/query` | POST | Query RAG system |
| `/api/v1/voice/transcribe` | POST | Transcribe audio |
| `/api/v1/ml/patterns` | GET | Get patterns |
| `/api/v1/users` | GET | List users |

### WebSocket API
```javascript
const ws = new WebSocket('ws://localhost:8123/api/ws');
ws.send(JSON.stringify({
  type: 'subscribe',
  channel: 'events'
}));
```

### GraphQL API
```graphql
query {
  health { status }
  patterns { id, type, confidence }
  user(id: "123") { name, preferences }
}
```

---

## VOICE ASSISTANT

### Supported Commands
- "Mach das Licht an" — Turn on lights
- "Stelle Heizung auf 21 Grad" — Set thermostat
- "Was ist der Status?" — Query status

### Configuration
```yaml
voice:
  wake_word: "Hey Pilot"
  stt_model: base
  tts_voice: de_DE-thorsten
```

---

## MACHINE LEARNING

### Pattern Detection
Automatically detects:
- Daily routines
- Weekly patterns
- Event-triggered behaviors

### Habit Learning
Learns user preferences for:
- Lighting scenes
- Temperature settings
- Media preferences

---

## RAG SYSTEM

### Components
- **Vector Store** — HNSW index for fast similarity search
- **Embedding Pipeline** — Batch processing with caching
- **Memory System** — Episodic, semantic, procedural memory

### Usage
```python
from copilot_core.rag import query_rag

results = query_rag("How do I set up automations?", k=5)
```

---

## UI COMPONENTS

### Admin Dashboard
- 6 tabs: Overview, RAG, Voice, ML, Users, Settings
- Real-time widgets
- Analytics integration

### Lovelace Cards
- Zone Card
- Presence Card
- Habitus Card
- Music Card
- Alarm Card
- Energy Card
- Weather Card
- Camera Card

---

## SECURITY

### Features
- Token-based authentication
- Rate limiting (100 req/s default)
- Input validation
- Encryption at rest
- Audit logging

### Security Audit
Run security audit:
```python
from copilot_core.testing import run_security_audit
report = run_security_audit()
print(f"Score: {report.overall_score}/100")
```

---

## TESTING

### Run Tests
```bash
# Unit tests
pytest tests/unit

# Integration tests
pytest tests/integration

# E2E tests
pytest tests/e2e

# Load testing
python -m copilot_core.testing.load_test --rps 1000
```

---

## DEPLOYMENT

### Docker
```bash
docker-compose up -d
```

### Kubernetes
```bash
kubectl apply -f k8s/
```

### Home Assistant Add-on
Available via HACS (coming soon)

---

## TROUBLESHOOTING

### Common Issues

**Ollama Connection Failed**
```bash
# Check Ollama is running
ollama list

# Restart Ollama
systemctl restart ollama
```

**High API Latency**
- Check database connection pool
- Enable query caching
- Review slow query logs

---

*Documentation Version: 16.0.0*
*Last Updated: 2026-04-07*
