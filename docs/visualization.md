# Visualization Module - PilotSuite

The Visualization module provides interactive graph visualizations for entity relationships, mood contexts, neuron states, and habitus zones in Home Assistant.

## Features

- **Brain Graph Panel**: Interactive D3.js force-directed graph for entity-relationship visualization
- **Lovelace Cards**: Custom Lovelace cards for mood, neurons, and habitus
- **React Components**: React-based visualization components with smooth animations
- **Real-time Updates**: Automatic updates when entity states change
- **Zoom/Pan Support**: Interactive graph exploration with zoom and pan
- **Node Interaction**: Click to select nodes, hover for details

## Structure

```
src/visualizations/
├── brain_graph/          # D3.js-based graph visualization
│   ├── index.ts         # Brain Graph Panel implementation
│   └── types.ts         # TypeScript interfaces
├── lovelace_cards/      # Custom Lovelace cards
│   ├── index.ts         # Card implementations
│   ├── mood-card.ts     # Mood context card
│   ├── neurons-card.ts  # Neuron status card
│   └── habitus-card.ts  # Habitus zone card
├── react_components/    # React visualization components
│   ├── index.tsx        # Main export
│   ├── brain-graph.tsx  # Interactive graph
│   ├── mood-context.tsx # Mood visualization
│   ├── neuron-status.tsx # Neuron activity
│   └── habitus-zone.tsx # Habitus zones
└── index.ts             # Module entry point
```

## Installation

### For Home Assistant Add-on

1. Copy the visualization module to your add-on:
   ```bash
   cp -r src/visualizations /usr/local/share/openclaw/addons/ha-copilot/
   ```

2. Update the add-on manifest to include visualization dependencies:
   ```json
   {
     "dependencies": [
       "d3",
       "framer-motion",
       "custom-card-helpers"
     ]
   }
   ```

### For HACS Integration

1. Add this repository as a custom repository in HACS
2. Install the "Visualization Components" integration

## Usage

### Brain Graph Panel

```typescript
import { BrainGraphPanel, createGraphFromEntities } from '@openclaw/visualizations';

// Create graph container
const container = document.createElement('div');
container.style.height = '600px';
document.body.appendChild(container);

// Initialize brain graph
const graph = new BrainGraphPanel(container, {
  width: 800,
  height: 600,
  nodeRadius: 15,
  showLegend: true
});

// Create graph from Home Assistant entities
const { nodes, links } = createGraphFromEntities(hass.states);
graph.setData(nodes, links);

// Update graph when entities change
hass.subscribeEvents(() => {
  const { nodes, links } = createGraphFromEntities(hass.states);
  graph.setData(nodes, links);
}, 'state_changed');
```

### Custom Lovelace Cards

Add to your `configuration.yaml`:

```yaml
lovelace:
  mode: yaml
  resources:
    - url: /hacsfiles/ha-copilot/brain-graph-panel.js
      type: module
    - url: /hacsfiles/ha-copilot/mood-card.js
      type: module
    - url: /hacsfiles/ha-copilot/neurons-card.js
      type: module
    - url: /hacsfiles/ha-copilot/habitus-card.js
      type: module
```

Use in dashboard:

```yaml
type: custom:brain-graph-panel
entity: sensor.current_mood
title: Mood Graph

type: custom:ha-copilot-mood-card
entity: sensor.current_mood
title: Current Mood

type: custom:ha-copilot-neurons-card
entity: sensor.neuron_activity
title: Neuron Status

type: custom:ha-copilot-habitus-card
entity: select.current_habitus_zone
title: Habitus Zones
```

### React Components

```tsx
import { Visualization } from '@openclaw/visualizations';

// Get data from Home Assistant
const nodes = Object.entries(hass.states).map(([entityId, entity]) => ({
  id: entityId,
  type: 'entity',
  label: entityId.replace('.', '\n'),
  color: getEntityColor(entity),
  value: getEntityValue(entity)
}));

const links = createEntityLinks(nodes);

// Render visualization
return (
  <Visualization
    nodes={nodes}
    links={links}
    mood={moodData}
    neurons={neuronData}
    zones={habitusData}
  />
);
```

## Configuration

### Brain Graph Panel Options

```typescript
{
  width: number;           // Graph width (default: 800)
  height: number;          // Graph height (default: 600)
  nodeRadius: number;      // Base node radius (default: 15)
  linkDistance: number;    // Link distance (default: 100)
  chargeStrength: number;  // Repulsion strength (default: -30)
  fontSize: number;        // Label font size (default: 12)
  showLegend: boolean;     // Show legend (default: true)
  showZoomControls: boolean; // Show zoom controls (default: true)
}
```

### Node Types

- `entity`: Home Assistant entities (blue)
- `mood`: Mood states (orange)
- `neuron`: Neuron states (green)
- `habitus`: Habitus zones (purple)
- `behavior`: Behavior states (gray)

## API Reference

### BrainGraphPanel

- `updateGraph(nodes: GraphNode[], links: GraphLink[])`: Update graph data
- `addNode(node: GraphNode)`: Add a single node
- `addLink(link: GraphLink)`: Add a single link
- `setSelectedNode(nodeId: string)`: Highlight a specific node
- `refresh()`: Force graph recalculation
- `zoomIn()/zoomOut()/resetZoom()`: Control zoom level
- `destroy()`: Clean up resources

### VisualizationManager

- `initialize()`: Initialize the visualization system
- `createBrainGraph(container, config?)`: Create a new brain graph panel
- `updateBrainGraph(panelId, nodes, links)`: Update an existing graph
- `destroyBrainGraph(panelId)`: Destroy a specific graph
- `destroyAll()`: Destroy all graphs
- `loadEntities(hass)`: Create graph from Home Assistant entities
- `getMoodData(hass, entity)`: Get mood state data
- `getNeuronData(hass, entity)`: Get neuron activity data
- `getHabitusData(hass, entity)`: Get habitus zone data

## Development

### Building

```bash
# Install dependencies
npm install

# Build TypeScript
npm run build

# Build React components
npm run build:react
```

### Testing

```bash
# Run tests
npm test

# Run with coverage
npm run test:coverage
```

### Development Server

```bash
npm run dev
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'feat(viz): add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- D3.js for the powerful data visualization framework
- Home Assistant community for the inspiration
- OpenClaw team for the integration
