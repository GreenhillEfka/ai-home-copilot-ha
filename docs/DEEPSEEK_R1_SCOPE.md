# Copilot-Core — DeepSeek-R1 Ollama Integration Scope

> Technischer Scope für die LLM-Integration auf der Core-Seite (Add-on).
> Siehe auch: `ai-home-copilot-ha/docs/DEEPSEEK_R1_SCOPE.md` für den HA-seitigen Scope.

---

## 1) Übersicht

DeepSeek-R1 wird als **lokales Reasoning-Backend** via Ollama in den
Copilot-Core integriert. Die Integration erfolgt als **optionales Modul** —
der Core funktioniert weiterhin ohne LLM (heuristische Fallbacks).

```
┌─────────────────────────────┐
│      Copilot-Core           │
│                             │
│  ┌──────────────────────┐  │
│  │  Bestehende Pipeline │  │
│  │  Events → Graph →    │  │
│  │  Candidates → Mood   │  │
│  └────────┬─────────────┘  │
│           │                 │
│           ▼                 │
│  ┌──────────────────────┐  │
│  │  LLM-Modul (NEU)     │  │
│  │  ├─ OllamaProvider   │  │
│  │  ├─ PromptTemplates  │  │
│  │  └─ OutputSchemas    │  │
│  └────────┬─────────────┘  │
│           │ HTTP            │
│           ▼                 │
│  ┌──────────────────────┐  │
│  │  Ollama Server       │  │
│  │  └─ deepseek-r1      │  │
│  │     (localhost:11434) │  │
│  └──────────────────────┘  │
└─────────────────────────────┘
```

---

## 2) Neue Dateistruktur

```
copilot_core/
  └── llm/
      ├── __init__.py           # Modul-Exports
      ├── provider.py           # OllamaProvider Klasse
      ├── prompts.py            # Prompt-Templates (System + Task)
      ├── schemas.py            # JSON-Schemas für strukturierte Ausgabe
      ├── rate_limiter.py       # Token-Bucket Rate-Limiter
      └── fallback.py           # Heuristische Fallback-Logik
```

---

## 3) OllamaProvider — Technische Spezifikation

### 3.1 Klasse

```python
class OllamaProvider:
    """Thread-safe Ollama HTTP Client für DeepSeek-R1."""

    def __init__(
        self,
        host: str = "localhost",
        port: int = 11434,
        model: str = "deepseek-r1",
        timeout: int = 30,
        max_output_tokens: int = 2048,
    ): ...

    def is_available(self) -> bool:
        """Health-Check: GET /api/tags → Modell vorhanden?"""

    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.3,
        response_format: dict | None = None,
    ) -> dict:
        """
        POST /api/generate → strukturierte Antwort.
        Timeout nach self.timeout Sekunden.
        Fallback-Exception bei Fehler.
        """
```

### 3.2 Thread-Safety

> **WICHTIG**: Vor der LLM-Integration müssen die bestehenden
> Thread-Safety Probleme behoben werden (siehe AUDIT_2026_02.md).

- OllamaProvider nutzt `requests.Session` (thread-safe)
- Rate-Limiter nutzt `threading.Lock`
- Kein globaler State im Provider

### 3.3 Ollama API Calls

```
GET  /api/tags                    → Verfügbare Modelle prüfen
POST /api/generate                → Text-Generierung
  Body: {
    "model": "deepseek-r1",
    "prompt": "...",
    "system": "...",
    "stream": false,
    "options": {
      "temperature": 0.3,
      "num_predict": 2048
    },
    "format": "json"             → Strukturierte Ausgabe erzwingen
  }
```

---

## 4) Neue API-Endpunkte

### 4.1 LLM Status
```
GET /api/v1/llm/status

Response:
{
  "available": true,
  "model": "deepseek-r1:7b",
  "provider": "ollama",
  "calls_remaining_this_hour": 15,
  "last_call_duration_ms": 4200
}
```

### 4.2 Kandidaten-Bewertung
```
POST /api/v1/llm/evaluate

Body:
{
  "candidate_id": "cand_abc123",
  "trigger": {"entity_id": "binary_sensor.motion_flur", "domain": "binary_sensor"},
  "action": {"entity_id": "light.flur", "domain": "light"},
  "evidence": {"support": 42, "confidence": 0.85, "time_window": "18:00-23:00"},
  "zone": {"name": "Flur", "entities": [...]}
}

Response:
{
  "candidate_id": "cand_abc123",
  "llm_score": 0.82,
  "recommendation": "accept",
  "explanation": "...",
  "risks": [...],
  "suggestions": [...],
  "duration_ms": 3800
}
```

### 4.3 Erklärung generieren
```
POST /api/v1/llm/explain

Body:
{
  "candidate_id": "cand_abc123",
  "context": {...}
}

Response:
{
  "explanation_short": "Flur-Licht bei Bewegung einschalten (abends).",
  "explanation_detailed": "...",
  "confidence_note": "Hohe Konfidenz (85%) basierend auf 42 Beobachtungen."
}
```

### 4.4 Log-Analyse
```
POST /api/v1/llm/analyze-logs

Body:
{
  "log_entries": ["2026-02-16 ERROR ...", "..."],
  "max_entries": 10
}

Response:
{
  "issues": [
    {
      "severity": "warning",
      "component": "zha",
      "summary": "Zigbee-Gerät antwortet nicht",
      "fix_suggestion": "Gerät neu pairen oder Zigbee-Netzwerk neustarten",
      "reversible": true
    }
  ]
}
```

---

## 5) Konfiguration

### 5.1 Add-on Options (config.json Erweiterung)

```json
{
  "options": {
    "llm_enabled": {
      "name": "LLM aktivieren",
      "description": "DeepSeek-R1 via Ollama als Reasoning-Backend nutzen",
      "default": false
    },
    "llm_host": {
      "name": "Ollama Host",
      "default": "localhost"
    },
    "llm_port": {
      "name": "Ollama Port",
      "default": 11434
    },
    "llm_model": {
      "name": "Modell-Name",
      "default": "deepseek-r1"
    },
    "llm_timeout": {
      "name": "Timeout (Sekunden)",
      "default": 30
    },
    "llm_max_calls_per_hour": {
      "name": "Max Calls pro Stunde",
      "default": 20
    }
  }
}
```

### 5.2 Umgebungsvariablen (Fallback)

```
COPILOT_LLM_ENABLED=false
COPILOT_LLM_HOST=localhost
COPILOT_LLM_PORT=11434
COPILOT_LLM_MODEL=deepseek-r1
COPILOT_LLM_TIMEOUT=30
COPILOT_LLM_MAX_CALLS_PER_HOUR=20
```

---

## 6) Fehlerbehandlung & Fallback

```
LLM-Call
  ├── Erfolg → Strukturierte Antwort zurückgeben
  ├── Timeout (>30s) → 1x Retry → Heuristik-Fallback
  ├── Ollama nicht erreichbar → Heuristik-Fallback + Status-Sensor "offline"
  ├── Modell nicht geladen → Heuristik-Fallback + Warnung loggen
  ├── Ungültiges JSON → Heuristik-Fallback + Warnung loggen
  └── Rate-Limit erreicht → Heuristik-Fallback + Info loggen
```

**Heuristik-Fallback** = bestehende Logik (Mood-Score, Graph-basierte Bewertung).
Der Fallback ist **immer verfügbar** — LLM ist ein Bonus, keine Abhängigkeit.

---

## 7) Voraussetzungen vor Implementation

### Muss vorher erledigt werden:
1. Thread-Safety Fixes (siehe Audit — 8 kritische Issues)
2. Version-Mismatch fixen (config.json vs app.py)
3. `requirements.txt` erstellen (inkl. `requests` für Ollama-Client)

### Parallel möglich:
1. Ollama auf dem Zielserver installieren + DeepSeek-R1 pullen
2. Prompt-Templates entwerfen und manuell testen
3. JSON-Schemas für strukturierte Ausgabe definieren
