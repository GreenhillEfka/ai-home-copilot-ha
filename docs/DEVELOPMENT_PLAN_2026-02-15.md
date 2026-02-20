# Development Plan - 2026-02-15

## Priorität 1: Security Fixes (P0)

### log_fixer_tx API Auth
**File:** `addons/copilot_core/rootfs/usr/src/app/api/v1/log_fixer_tx.py`

```python
from security import require_api_key

@require_api_key
def status():
    # Bestehender Code

@require_api_key  
def transactions():
    # Bestehender Code

@require_api_key
def recover():
    # Bestehender Code

@require_api_key
def create_transaction():
    # Bestehender Code
```

### Path-Allowlist für rename
```python
ALLOWED_RENAME_PATHS = [
    "/config/homeassistant",
    "/config/.openclaw/workspace",
    "/config/www"
]

def validate_rename_path(path: str) -> bool:
    """Validiere dass rename-Operation nur erlaubte Pfade betrifft"""
    resolved = os.path.realpath(path)
    return any(resolved.startswith(allowed) for allowed in ALLOWED_RENAME_PATHS)
```

---

## Priorität 2: Architecture Improvements

### BaseNeuron-Abstraktionsklasse
**Ziel:** Konsistente Neuron-Implementierungen

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, Any, Optional

@dataclass
class NeuronState:
    """Basis-Zustand für alle Neuronen"""
    active: bool = False
    confidence: float = 0.0
    last_update: Optional[str] = None

class BaseNeuron(ABC):
    """Abstrakte Basisklasse für alle Neuronen"""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        self.name = name
        self.config = config
        self.state = NeuronState()
    
    @abstractmethod
    def evaluate(self, context: Dict[str, Any]) -> float:
        """Evaluiere Neuron basierend auf Kontext"""
        pass
    
    @abstractmethod
    def update(self, value: float, confidence: float = 1.0):
        """Update Neuron-Zustand"""
        pass
    
    def reset(self):
        """Reset Neuron-Zustand"""
        self.state = NeuronState()
```

### Mood-Integration
**Ziel:** Mood in Home Assistant sichtbar machen

```yaml
# Neue Entities
sensor.ai_copilot_mood:
  name: "AI CoPilot Mood"
  icon: mdi:robot-happy
  
sensor.ai_copilot_mood_confidence:
  name: "AI CoPilot Mood Confidence"
  icon: mdi:gauge
```

---

## Priorität 3: OpenAPI-Spec

**Ziel:** API-Verträge zwischen Core und HA Integration

```yaml
openapi: 3.0.0
info:
  title: PilotSuite Core API
  version: 1.0.0
paths:
  /api/v1/status:
    get:
      summary: Get system status
      responses:
        '200':
          content:
            application/json:
              schema:
                type: object
                properties:
                  version:
                    type: string
                  mood:
                    type: string
```

---

## Zeitplan

| Woche | Aufgabe |
|-------|---------|
| 1 | Security P0 Fixes |
| 2 | BaseNeuron-Klasse |
| 3 | Mood-Entities |
| 4 | OpenAPI-Spec |

---

## Branches

- HA Integration: `development` (Features)
- Core Add-on: `main` (Stable)