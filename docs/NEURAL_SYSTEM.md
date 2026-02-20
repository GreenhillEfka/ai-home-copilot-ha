# Neural System Configuration

## Entity Assignment for Neurons

### Config Flow

Add to `config_flow.py`:

```python
NEURON_CONFIG_SCHEMA = vol.Schema({
    vol.Optional("neuron_presence_entities"): vol.All(
        cv.ensure_list, [cv.entity_id]
    ),
    vol.Optional("neuron_time_timezone", default="Europe/Berlin"): str,
    vol.Optional("neuron_light_use_sun", default=True): bool,
    vol.Optional("neuron_mood_threshold", default=0.6): vol.Coerce(float),
    vol.Optional("neuron_enable_suggestions", default=True): bool,
    vol.Optional("neuron_enable_learning", default=True): bool,
})
```

### Options Flow

```python
class OptionsFlowHandler(config_entries.OptionsFlow, ConfigSnapshotOptionsFlow):
    async def async_step_init(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)
        
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({
                vol.Optional("neuron_presence_entities"): self._get_entity_list(),
                vol.Optional("neuron_mood_threshold", default=0.6): vol.Coerce(float),
                vol.Optional("neuron_enable_suggestions", default=True): bool,
            })
        )
```

### Services

```yaml
# services.yaml
neuron_evaluate:
  name: Evaluate Neurons
  description: Manually trigger neural evaluation
  fields:
    context:
      name: Context
      description: Additional context data
      required: false
      selector:
        object:

neuron_learn:
  name: Learn from Feedback
  description: Apply user feedback to neural system
  fields:
    suggestion_id:
      name: Suggestion ID
      description: ID of the suggestion
      required: true
      selector:
        text:
    accepted:
      name: Accepted
      description: Whether user accepted the suggestion
      required: true
      selector:
        boolean:
```

## Dashboard

### Sensors

| Sensor | Description |
|--------|-------------|
| `sensor.ai_copilot_mood` | Current mood (relax, focus, active, sleep, away, alert, social, recovery) |
| `sensor.ai_copilot_mood_confidence` | Confidence (0-100%) |
| `sensor.ai_copilot_active_neurons` | Count of active neurons |
| `sensor.ai_copilot_neuron_dashboard` | All neurons as JSON |
| `sensor.ai_copilot_mood_history` | Mood trend history |
| `sensor.ai_copilot_suggestions` | Current suggestions |

### Lovelace Card

```yaml
type: entities
title: AI CoPilot Neural System
entities:
  - entity: sensor.ai_copilot_mood
    name: Mood
    icon: mdi:robot-happy
  - entity: sensor.ai_copilot_mood_confidence
    name: Confidence
    icon: mdi:gauge
  - entity: sensor.ai_copilot_active_neurons
    name: Active Neurons
    icon: mdi:brain
  - entity: sensor.ai_copilot_suggestions
    name: Suggestions
    icon: mdi:lightbulb-outline
```

## API Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /api/v1/neurons` | List all neurons |
| `GET /api/v1/neurons/mood` | Get current mood |
| `POST /api/v1/neurons/evaluate` | Run evaluation with HA states |
| `POST /api/v1/neurons/feedback` | Submit user feedback |
| `GET /api/v1/neurons/stats` | Network statistics |

## Architecture

```
HA Integration                    Core Add-on
┌──────────────────┐            ┌──────────────────┐
│ Coordinator      │──API──────▶│ NeuronManager   │
│ MoodSensor       │            │ ContextNeurons  │
│ NeuronSensor     │◀──JSON─────│ StateNeurons    │
│ SuggestionSensor │            │ MoodNeurons     │
└──────────────────┘            │ SynapseManager  │
                                └──────────────────┘
```