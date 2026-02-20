# PilotSuite Dashboard

## Overview

The dashboard provides visibility into the neural system's state and suggestions.

## Available Sensors

### Mood Sensors

| Sensor | State | Attributes |
|--------|-------|------------|
| `sensor.ai_copilot_mood` | relax, focus, active, sleep, away, alert, social, recovery | confidence, zone, last_update, contributing_neurons |
| `sensor.ai_copilot_mood_confidence` | 0-100% | mood, factors |
| `sensor.ai_copilot_active_neurons` | count | active_neurons, total_neurons |

### Dashboard Sensors

| Sensor | State | Attributes |
|--------|-------|------------|
| `sensor.ai_copilot_neuron_dashboard` | ok | context_neurons, state_neurons, mood_neurons, total_count, active_count |
| `sensor.ai_copilot_mood_history` | ok | history, current_mood, current_confidence |
| `sensor.ai_copilot_suggestions` | action_type or "none" | suggestions, count, top_suggestion |

## Lovelace Dashboard Configuration

### Main Panel

```yaml
type: vertical-stack
cards:
  - type: entities
    title: AI CoPilot Mood
    entities:
      - entity: sensor.ai_copilot_mood
        name: Current Mood
        icon: mdi:robot-happy
      - entity: sensor.ai_copilot_mood_confidence
        name: Confidence
        icon: mdi:gauge
      - entity: sensor.ai_copilot_active_neurons
        name: Active Neurons
        icon: mdi:brain

  - type: history-graph
    title: Mood History
    entities:
      - sensor.ai_copilot_mood
      - sensor.ai_copilot_mood_confidence
    hours_to_show: 24

  - type: entities
    title: Suggestions
    entities:
      - entity: sensor.ai_copilot_suggestions
        name: Current Suggestion
        icon: mdi:lightbulb-outline
```

### Detailed Neuron Panel

```yaml
type: entities
title: Neuron States
entities:
  - type: section
    label: Context Neurons
  - entity: sensor.ai_copilot_neuron_dashboard
    name: Presence
    attribute: context_neurons.presence.house
  - entity: sensor.ai_copilot_neuron_dashboard
    name: Time of Day
    attribute: context_neurons.time_of_day
  - entity: sensor.ai_copilot_neuron_dashboard
    name: Light Level
    attribute: context_neurons.light_level
  - type: section
    label: State Neurons
  - entity: sensor.ai_copilot_neuron_dashboard
    name: Energy Level
    attribute: state_neurons.energy_level
  - entity: sensor.ai_copilot_neuron_dashboard
    name: Stress Index
    attribute: state_neurons.stress_index
  - type: section
    label: Mood Neurons
  - entity: sensor.ai_copilot_neuron_dashboard
    name: Relax Mood
    attribute: mood_neurons.mood.relax
  - entity: sensor.ai_copilot_neuron_dashboard
    name: Focus Mood
    attribute: mood_neurons.mood.focus
```

## Configuration

### Options Flow

Navigate to **Settings → Devices & Services → AI Home CoPilot → Configure**

#### Neuron Configuration

| Option | Description | Default |
|--------|-------------|---------|
| Presence Entities | Person entities for presence detection | [] |
| Timezone | Timezone for time-of-day neuron | Europe/Berlin |
| Use Sun Position | Use sun position for light level | true |
| Mood Threshold | Activation threshold for mood neurons | 0.6 |
| Enable Suggestions | Generate suggestions from mood | true |
| Enable Learning | Learn from user feedback | true |

## Services

### neuron_evaluate

Manually trigger neural evaluation.

```yaml
service: ai_home_copilot.neuron_evaluate
data:
  context:
    states:
      person.andreas:
        state: home
      sensor.temperature:
        state: "21.5"
```

### neuron_learn

Apply user feedback to improve suggestions.

```yaml
service: ai_home_copilot.neuron_learn
data:
  suggestion_id: "sugg_relax_20260215_123456"
  accepted: true
```

## API

### GET /api/v1/neurons

Returns all neuron states.

### GET /api/v1/neurons/mood

Returns current mood and confidence.

### POST /api/v1/neurons/evaluate

Evaluate with provided context.

### POST /api/v1/neurons/feedback

Submit user feedback.

### GET /api/v1/neurons/stats

Network statistics.