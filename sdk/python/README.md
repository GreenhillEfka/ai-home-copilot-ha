# AI Home CoPilot Python SDK

Python client for AI Home CoPilot Core API.

## Installation

```bash
pip install ai-home-copilot-client
```

## Usage

```python
from ai_home_copilot_client import CopilotClient

# Initialize client
client = CopilotClient(
    base_url="http://localhost:48099",
    auth_token="your-token-here"  # optional
)

# Get habitus status
status = client.habitus.get_status()

# Mine rules from events
result = client.habitus.mine_rules(events=[...])

# Get brain graph state
graph = client.graph.get_state()

# Get neurons
neurons = client.neurons.list()

# Get current mood
mood = client.neurons.get_mood()

# Work with tags
tags = client.tags.list()
client.tags.assign_tag("light.living_room", tag_id="aicp.place.living_room")

# Vector embeddings
client.vector.create_embedding(
    type="entity",
    id="light.living_room",
    domain="light",
    area="living_room"
)
```

## API Endpoints

### Habitus
- `get_status()` - Get miner status
- `get_rules()` - Get discovered rules
- `mine_rules(events)` - Mine rules from events
- `get_zones()` - Get zones
- `get_dashboard_cards()` - Get dashboard cards

### Graph
- `get_state()` - Get brain graph state
- `get_patterns()` - Get discovered patterns
- `sync(entities)` - Sync graph with HA entities

### Neurons
- `list()` - List all neurons
- `get(neuron_id)` - Get neuron state
- `evaluate()` - Run neural evaluation
- `get_mood()` - Get current mood
- `get_suggestions()` - Get suggestions

### Tags
- `list()` - Get all tags
- `create(tag_id, description)` - Create tag
- `get_subject_tags(subject_id)` - Get subject tags
- `assign_tag(subject_id, tag_id)` - Assign tag

### Vector Store
- `create_embedding()` - Create embedding
- `find_similar(entry_id)` - Find similar entities
- `list_vectors()` - List vectors
- `get_stats()` - Get stats

## License

MIT