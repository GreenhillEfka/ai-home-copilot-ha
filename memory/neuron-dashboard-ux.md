# Neuron Dashboard UX Research Report

**Datum:** 2026-03-01  
**Recherche:** D3.js Neural Network Visualization, Real-time Updates, WebSocket Integration

---

## Zusammenfassung

D3.js Force-Directed Graphs sind ideal für Neuronen-Visualisierungen mit dynamischen Zuständen. Die Kombination aus `d3-force` Simulation mit WebSocket-basierten Live-Updates ermöglicht Echtzeit-Darstellung feuernder Neuronen. Für 14+ Neuronen und 50+ Connections ist Canvas-Rendering (statt SVG) empfehlenswert für Performance. Node/Edge-Styling über Farb-Scales und Opacity erlaubt klare Unterscheidung von aktiv/inaktiv/feuernd.

---

## Key Findings

### D3.js Force-Directed Graph Basics

- **Core Module:** `d3-force` verwendet Velocity-Verlet-Integration für physikalische Partikelsimulation
- **Simulation Setup:**
  ```javascript
  const simulation = d3.forceSimulation(nodes)
    .force("link", d3.forceLink(links).id(d => d.id).distance(100))
    .force("charge", d3.forceManyBody().strength(-300))
    .force("center", d3.forceCenter(width / 2, height / 2))
    .force("collide", d3.forceCollide().radius(30));
  ```

- **Tick-Rendering:** Jede Simulation-Iteration triggert `tick`-Event für Re-Render
  ```javascript
  simulation.on("tick", () => {
    link.attr("x1", d => d.source.x).attr("y1", d => d.source.y)
        .attr("x2", d => d.target.x).attr("y2", d => d.target.y);
    node.attr("cx", d => d.x).attr("cy", d => d.y);
  });
  ```

### Node/Edge Styling für Neuronen

- **Zustandsbasierte Farben:**
  ```javascript
  const neuronColor = {
    inactive: "#666666",
    active: "#4CAF50",
    firing: "#FF5722"
  };

  node.attr("fill", d => {
    if (d.state === "firing") return neuronColor.firing;
    if (d.state === "active") return neuronColor.active;
    return neuronColor.inactive;
  });
  ```

- **Edge-Styling nach Connection-Stärke:**
  ```javascript
  const linkWidth = d3.scaleLinear()
    .domain([0, 10])
    .range([1, 5]);

  link.attr("stroke-width", d => linkWidth(d.value || 1))
      .attr("stroke", d => d.active ? "#FF5722" : "#999999")
      .attr("opacity", d => d.active ? 1 : 0.3);
  ```

- **Kategorische Farb-Scales (d3-scale-chromatic):**
  ```javascript
  const colorScale = d3.scaleOrdinal()
    .domain(["input", "hidden", "output"])
    .range(d3.schemeSet3);
  ```

### WebSocket Integration Pattern

- **WebSocket Client Setup:**
  ```javascript
  const ws = new WebSocket('ws://localhost:8080/neuron-updates');

  ws.onmessage = (event) => {
    const update = JSON.parse(event.data);
    updateNeuronState(update.neuronId, update.state);
  };

  function updateNeuronState(neuronId, newState) {
    const node = nodes.find(n => n.id === neuronId);
    if (node) {
      node.state = newState;
      // Trigger visual update
      node.transition().duration(200)
        .attr("fill", getColorForState(newState));
    }
  }
  ```

- **Batch Updates für Performance:**
  ```javascript
  let updateQueue = [];
  let updateScheduled = false;

  ws.onmessage = (event) => {
    updateQueue.push(JSON.parse(event.data));
    if (!updateScheduled) {
      updateScheduled = true;
      requestAnimationFrame(applyUpdates);
    }
  };

  function applyUpdates() {
    updateQueue.forEach(update => {
      // Apply state changes
    });
    updateQueue = [];
    updateScheduled = false;
  }
  ```

- **D3 Data-Join Pattern für Updates:**
  ```javascript
  function updateGraph(data) {
    const nodes = svg.selectAll(".node").data(data.nodes, d => d.id);
    const links = svg.selectAll(".link").data(data.links, d => `${d.source}-${d.target}`);

    // Enter
    const nodeEnter = nodes.enter().append("circle")
      .attr("class", "node")
      .attr("r", 20);

    // Update
    nodes.merge(nodeEnter)
      .attr("fill", d => getColorForState(d.state));

    // Exit
    nodes.exit().remove();
  }
  ```

### Performance-Optimierung (>14 Neuronen, 50+ Connections)

1. **Canvas statt SVG für große Netzwerke:**
   ```javascript
   const canvas = d3.select("#network").append("canvas")
     .attr("width", width)
     .attr("height", height);

   const context = canvas.node().getContext("2d");

   simulation.on("tick", () => {
     context.clearRect(0, 0, width, height);
     // Draw links
     links.forEach(d => {
       context.beginPath();
       context.moveTo(d.source.x, d.source.y);
       context.lineTo(d.target.x, d.target.y);
       context.stroke();
     });
     // Draw nodes
     nodes.forEach(d => {
       context.beginPath();
       context.arc(d.x, d.y, 10, 0, 2 * Math.PI);
       context.fill();
     });
   });
   ```

2. **Simulation-Parameter optimieren:**
   ```javascript
   const simulation = d3.forceSimulation()
     .velocityDecay(0.4)  // Höher = schneller stabil
     .alphaMin(0.01)      // Früher stoppen
     .alphaDecay(0.02);   // Langsamere Abkühlung
   ```

3. **Alpha-Target für Reheat nach Updates:**
   ```javascript
   function addNode(newNode) {
     nodes.push(newNode);
     simulation.nodes(nodes);
     simulation.alpha(0.3).restart(); // Reheat simulation
   }
   ```

4. **Throttling bei High-Frequency Updates:**
   ```javascript
   const throttle = (func, limit) => {
     let inThrottle;
     return function(...args) {
       if (!inThrottle) {
         func.apply(this, args);
         inThrottle = true;
         setTimeout(() => inThrottle = false, limit);
       }
     };
   };

   const throttledUpdate = throttle(updateGraph, 100); // Max 10 Updates/sec
   ```

5. **Node-Filterung für Fokus-Ansichten:**
   ```javascript
   function showNeighborhood(centerNodeId, depth = 2) {
     const visible = new Set([centerNodeId]);
     // BFS für Nachbarn
     for (let i = 0; i < depth; i++) {
       links.forEach(l => {
         if (visible.has(l.source.id)) visible.add(l.target.id);
         if (visible.has(l.target.id)) visible.add(l.source.id);
       });
     }
     // Filter nodes/links
   }
   ```

---

## Code-Beispiele (Copy-Paste Ready)

### Beispiel 1: Basis Force-Directed Graph mit Neuronen

```html
<!DOCTYPE html>
<html>
<head>
  <script src="https://d3js.org/d3.v7.min.js"></script>
  <style>
    .link { stroke: #999; stroke-opacity: 0.6; }
    .node { stroke: #fff; stroke-width: 2px; }
    .node.inactive { fill: #666; }
    .node.active { fill: #4CAF50; }
    .node.firing { fill: #FF5722; }
  </style>
</head>
<body>
  <svg id="network" width="800" height="600"></svg>
  <script>
    const width = 800, height = 600;
    const svg = d3.select("#network");

    // Beispiel-Daten
    const nodes = [
      { id: "N1", state: "firing", type: "input" },
      { id: "N2", state: "active", type: "hidden" },
      { id: "N3", state: "inactive", type: "hidden" },
      { id: "N4", state: "active", type: "output" }
    ];

    const links = [
      { source: "N1", target: "N2", weight: 1 },
      { source: "N2", target: "N3", weight: 2 },
      { source: "N2", target: "N4", weight: 1 },
      { source: "N3", target: "N4", weight: 3 }
    ];

    const simulation = d3.forceSimulation(nodes)
      .force("link", d3.forceLink(links).id(d => d.id).distance(120))
      .force("charge", d3.forceManyBody().strength(-400))
      .force("center", d3.forceCenter(width / 2, height / 2))
      .force("collide", d3.forceCollide().radius(25));

    const link = svg.append("g")
      .selectAll("line")
      .data(links)
      .join("line")
      .attr("class", "link")
      .attr("stroke-width", d => Math.sqrt(d.weight * 2));

    const node = svg.append("g")
      .selectAll("circle")
      .data(nodes)
      .join("circle")
      .attr("class", d => `node ${d.state}`)
      .attr("r", 20)
      .call(drag(simulation));

    simulation.on("tick", () => {
      link
        .attr("x1", d => d.source.x)
        .attr("y1", d => d.source.y)
        .attr("x2", d => d.target.x)
        .attr("y2", d => d.target.y);

      node
        .attr("cx", d => d.x)
        .attr("cy", d => d.y);
    });

    function drag(simulation) {
      function dragstarted(event) {
        if (!event.active) simulation.alphaTarget(0.3).restart();
        event.subject.fx = event.subject.x;
        event.subject.fy = event.subject.y;
      }
      function dragged(event) {
        event.subject.fx = event.x;
        event.subject.fy = event.y;
      }
      function dragended(event) {
        if (!event.active) simulation.alphaTarget(0);
        event.subject.fx = null;
        event.subject.fy = null;
      }
      return d3.drag()
        .on("start", dragstarted)
        .on("drag", dragged)
        .on("end", dragended);
    }

    // Simuliere WebSocket-Update
    setInterval(() => {
      const randomNode = nodes[Math.floor(Math.random() * nodes.length)];
      randomNode.state = ["inactive", "active", "firing"][Math.floor(Math.random() * 3)];
      node.attr("class", d => `node ${d.state}`);
    }, 2000);
  </script>
</body>
</html>
```

### Beispiel 2: WebSocket Integration mit Live-Updates

```javascript
class NeuronNetwork {
  constructor(containerId, wsUrl) {
    this.svg = d3.select(containerId);
    this.nodes = [];
    this.links = [];
    this.ws = new WebSocket(wsUrl);
    this.setupWebSocket();
    this.initSimulation();
  }

  setupWebSocket() {
    this.ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      this.handleUpdate(data);
    };

    this.ws.onopen = () => {
      console.log("WebSocket connected");
      this.ws.send(JSON.stringify({ type: "subscribe", channel: "neurons" }));
    };
  }

  handleUpdate(update) {
    switch(update.type) {
      case "neuron_state":
        this.updateNeuronState(update.neuronId, update.state);
        break;
      case "connection_activity":
        this.updateConnectionActivity(update.source, update.target, update.active);
        break;
      case "network_snapshot":
        this.fullUpdate(update.nodes, update.links);
        break;
    }
  }

  updateNeuronState(neuronId, state) {
    const node = this.nodes.find(n => n.id === neuronId);
    if (node) {
      node.state = state;
      d3.selectAll(".node")
        .filter(d => d.id === neuronId)
        .transition().duration(200)
        .attr("fill", this.getColorForState(state));
    }
  }

  initSimulation() {
    this.simulation = d3.forceSimulation()
      .force("link", d3.forceLink().id(d => d.id).distance(100))
      .force("charge", d3.forceManyBody().strength(-300))
      .force("center", d3.forceCenter(400, 300));

    this.simulation.on("tick", () => this.tick());
  }

  getColorForState(state) {
    const colors = {
      inactive: "#666666",
      active: "#4CAF50",
      firing: "#FF5722"
    };
    return colors[state] || colors.inactive;
  }

  tick() {
    this.link
      .attr("x1", d => d.source.x)
      .attr("y1", d => d.source.y)
      .attr("x2", d => d.target.x)
      .attr("y2", d => d.target.y);

    this.node
      .attr("cx", d => d.x)
      .attr("cy", d => d.y);
  }

  render(data) {
    this.nodes = data.nodes;
    this.links = data.links;

    this.link = this.svg.append("g")
      .selectAll("line")
      .data(this.links)
      .join("line")
      .attr("stroke", "#999")
      .attr("stroke-width", 2);

    this.node = this.svg.append("g")
      .selectAll("circle")
      .data(this.nodes)
      .join("circle")
      .attr("r", 20)
      .attr("fill", d => this.getColorForState(d.state));

    this.simulation.nodes(this.nodes);
    this.simulation.force("link").links(this.links);
    this.simulation.alpha(1).restart();
  }
}

// Usage:
// const network = new NeuronNetwork("#network", "ws://localhost:8080");
// network.render({ nodes: [...], links: [...] });
```

### Beispiel 3: Canvas-Rendering für Performance

```javascript
const width = 1200, height = 800;
const canvas = d3.select("#network").append("canvas")
  .attr("width", width)
  .attr("height", height);

const context = canvas.node().getContext("2d");
const nodes = []; // 50+ nodes
const links = []; // 100+ links

const simulation = d3.forceSimulation(nodes)
  .force("link", d3.forceLink(links).distance(80))
  .force("charge", d3.forceManyBody().strength(-200))
  .force("center", d3.forceCenter(width / 2, height / 2))
  .force("collide", d3.forceCollide().radius(15));

simulation.on("tick", () => {
  context.clearRect(0, 0, width, height);

  // Draw links first (behind nodes)
  context.strokeStyle = "rgba(150, 150, 150, 0.5)";
  context.lineWidth = 1.5;
  links.forEach(d => {
    context.beginPath();
    context.moveTo(d.source.x, d.source.y);
    context.lineTo(d.target.x, d.target.y);
    context.stroke();
  });

  // Draw nodes
  nodes.forEach(d => {
    context.beginPath();
    context.arc(d.x, d.y, 12, 0, 2 * Math.PI);
    context.fillStyle = getColorForState(d.state);
    context.fill();
    context.strokeStyle = "#fff";
    context.lineWidth = 2;
    context.stroke();
  });
});

function getColorForState(state) {
  switch(state) {
    case "firing": return "#FF5722";
    case "active": return "#4CAF50";
    default: return "#666666";
  }
}
```

### Beispiel 4: Pulsierende Animation für feuernde Neuronen

```javascript
// Füge zu SVG-Beispiel hinzu
const firingNodes = node.filter(d => d.state === "firing");

firingNodes.each(function() {
  d3.select(this)
    .transition()
    .duration(500)
    .attr("r", 25)
    .transition()
    .duration(500)
    .attr("r", 20)
    .on("end", function repeat() {
      if (d3.select(this).datum().state === "firing") {
        d3.select(this).call(arguments.callee);
      }
    });
});

// Alternative: Glow-Effekt mit SVG-Filter
const defs = svg.append("defs");
const filter = defs.append("filter")
  .attr("id", "glow");

filter.append("feGaussianBlur")
  .attr("stdDeviation", "4")
  .attr("result", "coloredBlur");

const feMerge = filter.append("feMerge");
feMerge.append("feMergeNode").attr("in", "coloredBlur");
feMerge.append("feMergeNode").attr("in", "SourceGraphic");

// Anwendung auf feuernde Neuronen
node.filter(d => d.state === "firing")
  .style("filter", "url(#glow)");
```

### Beispiel 5: Legende und Interaktion

```javascript
// Legende hinzufügen
const legend = svg.append("g")
  .attr("class", "legend")
  .attr("transform", "translate(20, 20)");

const legendData = [
  { state: "firing", color: "#FF5722", label: "Feuernd" },
  { state: "active", color: "#4CAF50", label: "Aktiv" },
  { state: "inactive", color: "#666666", label: "Inaktiv" }
];

const legendItem = legend.selectAll(".legend-item")
  .data(legendData)
  .join("g")
  .attr("class", "legend-item")
  .attr("transform", (d, i) => `translate(0, ${i * 30})`);

legendItem.append("circle")
  .attr("r", 10)
  .attr("fill", d => d.color);

legendItem.append("text")
  .attr("x", 25)
  .attr("y", 5)
  .text(d => d.label)
  .style("font-size", "14px")
  .style("fill", "#333");

// Tooltip auf Hover
const tooltip = d3.select("body").append("div")
  .attr("class", "tooltip")
  .style("opacity", 0)
  .style("position", "absolute")
  .style("background", "rgba(0,0,0,0.8)")
  .style("color", "#fff")
  .style("padding", "8px")
  .style("border-radius", "4px")
  .style("pointer-events", "none");

node.on("mouseover", (event, d) => {
  tooltip.transition().duration(200).style("opacity", 1);
  tooltip.html(`
    <strong>${d.id}</strong><br/>
    Zustand: ${d.state}<br/>
    Typ: ${d.type}<br/>
    Verbindungen: ${d.connections || 0}
  `)
  .style("left", (event.pageX + 10) + "px")
  .style("top", (event.pageY - 10) + "px");
})
.on("mouseout", () => {
  tooltip.transition().duration(500).style("opacity", 0);
});
```

---

## Empfehlung für PilotSuite

### Architektur-Vorschlag

```
┌─────────────────────────────────────────────────────────┐
│  PilotSuite Dashboard (Frontend)                        │
│  ┌─────────────────────────────────────────────────┐   │
│  │  D3.js Canvas Renderer                          │   │
│  │  - 60 FPS Animation                             │   │
│  │  - Neuron States (inactive/active/firing)       │   │
│  │  - Connection Activity Visualization            │   │
│  └─────────────────────────────────────────────────┘   │
│                    ↕ WebSocket                          │
└─────────────────────────────────────────────────────────┘
                    ↕
┌─────────────────────────────────────────────────────────┐
│  Backend (Node.js / Python)                             │
│  ┌─────────────────────────────────────────────────┐   │
│  │  WebSocket Server (ws / Socket.IO)              │   │
│  │  - Broadcast Neuron State Changes               │   │
│  │  - Throttle: max 10 updates/sec                 │   │
│  │  - Delta-Updates (nur Änderungen senden)        │   │
│  └─────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

### Konkrete Umsetzungsschritte

1. **Phase 1: Basis-Visualisierung**
   - D3.js Force-Directed Graph mit SVG (für <20 Neuronen)
   - Statische Darstellung mit manuellen State-Updates
   - 3 Zustandsfarben (inactive/active/firing)

2. **Phase 2: WebSocket Integration**
   - WebSocket-Server im Backend (Socket.IO empfohlen)
   - Frontend-Client mit Auto-Reconnect
   - Batch-Updates für Performance

3. **Phase 3: Performance-Optimierung**
   - Wechsel zu Canvas bei >20 Neuronen
   - Throttling auf 10-15 FPS
   - Fokus-Ansicht (nur relevante Neuronen anzeigen)

4. **Phase 4: UX-Enhancements**
   - Tooltips auf Hover
   - Legende und Filter-Controls
   - Pulsierende Animation für feuernde Neuronen
   - Zoom & Pan (d3-zoom)

### Tech-Stack Empfehlung

| Komponente | Empfehlung | Alternative |
|------------|------------|-------------|
| Rendering | D3.js v7 + Canvas | Pixi.js, Konva.js |
| WebSocket | Socket.IO | Native WebSocket, ws |
| State-Management | D3 Data-Join | Redux, Zustand |
| Backend | Node.js + ws | Python + websockets |
| Build | Vite | Webpack, Parcel |

### Performance-Benchmarks (Richtwerte)

- **SVG:** ~100 Nodes @ 30 FPS, ~200 Nodes @ 15 FPS
- **Canvas:** ~500 Nodes @ 60 FPS, ~1000 Nodes @ 30 FPS
- **WebGL (Pixi.js):** ~5000+ Nodes @ 60 FPS

**Für PilotSuite MVP:** Start mit Canvas-Rendering, später auf WebGL skalierbar wenn >100 Neuronen benötigt.

---

## Quellen

- D3.js Force-Directed Graph: https://observablehq.com/@d3/force-directed-graph
- D3 Force Module: https://d3js.org/d3-force
- D3 Graph Gallery: https://d3-graph-gallery.com/
- Mike Bostock's Blocks: https://bl.ocks.org/mbostock/4062045

---

**Nächste Schritte:**
1. Proof-of-Concept mit 14 Neuronen + 50 Connections
2. WebSocket-Server Setup für Test-Datenstream
3. User-Testing mit PilotSuite-Team
4. Iteration basierend auf Feedback
