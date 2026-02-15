// Brain Graph Panel - Interactive Graph Visualization for Entity-Relationships
import { svg, select, selectAll, forceSimulation, forceLink, forceManyBody, forceCenter, drag } from 'd3';
import { EntityId } from '@openclaw/types';

// Graph Node Interface
export interface GraphNode {
  id: string;
  type: 'entity' | 'state' | 'relationship';
  label: string;
  value?: number;
  color?: string;
  x?: number;
  y?: number;
}

// Graph Link Interface
export interface GraphLink {
  source: string | GraphNode;
  target: string | GraphNode;
  value?: number;
  type?: string;
}

// Brain Graph Configuration
export interface BrainGraphConfig {
  width?: number;
  height?: number;
  nodeRadius?: number;
  linkDistance?: number;
  chargeStrength?: number;
  fontSize?: number;
  showLegend?: boolean;
  showZoomControls?: boolean;
}

// Brain Graph State
export interface BrainGraphState {
  nodes: GraphNode[];
  links: GraphLink[];
  selectedNode?: string;
  hoveredNode?: string;
  zoomLevel: number;
  centerX: number;
  centerY: number;
}

/**
 * Brain Graph Panel Component
 * Visualizes entity relationships using D3.js force-directed graph
 */
export class BrainGraphPanel {
  private container: HTMLElement;
  private config: BrainGraphConfig;
  private state: BrainGraphState;
  private svg: any;
  private simulation: any;
  private nodes: any[] = [];
  private links: any[] = [];
  private zoom: any;

  constructor(container: HTMLElement, config: BrainGraphConfig = {}) {
    this.container = container;
    this.config = {
      width: 800,
      height: 600,
      nodeRadius: 15,
      linkDistance: 100,
      chargeStrength: -30,
      fontSize: 12,
      showLegend: true,
      showZoomControls: true,
      ...config
    };
    
    this.state = {
      nodes: [],
      links: [],
      zoomLevel: 1,
      centerX: this.config.width! / 2,
      centerY: this.config.height! / 2
    };
    
    this.initGraph();
  }

  private initGraph(): void {
    // Create SVG container
    this.svg = select(this.container)
      .append('svg')
      .attr('width', this.config.width)
      .attr('height', this.config.height)
      .attr('class', 'brain-graph-container');

    // Create zoom behavior
    this.zoom = select(this.svg).call(
      require('d3-zoom').zoom()
        .scaleExtent([0.1, 4])
        .on('zoom', (event: any) => {
          this.state.zoomLevel = event.transform.k;
          this.state.centerX = event.transform.x;
          this.state.centerY = event.transform.y;
          this.updateGraph();
        })
    );

    // Create simulation
    this.simulation = forceSimulation<GraphNode>()
      .force('link', forceLink<GraphNode, GraphLink>().id((d: any) => d.id).distance(this.config.linkDistance))
      .force('charge', forceManyBody().strength(this.config.chargeStrength))
      .force('center', forceCenter(this.config.width! / 2, this.config.height! / 2))
      .on('tick', () => this.tick());
  }

  public updateGraph(): void {
    if (!this.svg) return;

    // Draw links
    const linkSelection = this.svg.selectAll('.link')
      .data(this.state.links);

    linkSelection.enter()
      .append('line')
      .attr('class', 'link')
      .attr('stroke', '#999')
      .attr('stroke-width', 2)
      .attr('opacity', 0.6);

    linkSelection.exit().remove();

    // Draw nodes
    const nodeSelection = this.svg.selectAll('.node')
      .data(this.state.nodes, (d: any) => d.id);

    const nodeEnter = nodeSelection.enter()
      .append('g')
      .attr('class', 'node')
      .call(require('d3-drag').drag<GraphNode, any>()
        .on('start', (event: any, d: any) => this.dragStarted(event, d))
        .on('drag', (event: any, d: any) => this.dragged(event, d))
        .on('end', (event: any, d: any) => this.dragEnded(event, d)));

    // Node circle
    nodeEnter.append('circle')
      .attr('r', this.config.nodeRadius)
      .attr('fill', (d: any) => d.color || '#4CAF50')
      .attr('stroke', '#fff')
      .attr('stroke-width', 2)
      .on('click', (event: any, d: any) => this.nodeClicked(d))
      .on('mouseover', (event: any, d: any) => this.nodeHovered(d))
      .on('mouseout', () => this.nodeHovered(null));

    // Node label
    nodeEnter.append('text')
      .attr('dy', 3)
      .attr('text-anchor', 'middle')
      .attr('font-size', this.config.fontSize)
      .attr('fill', '#fff')
      .text((d: any) => d.label);

    nodeSelection.exit().remove();

    // Update simulation with new data
    this.simulation.nodes(this.state.nodes);
    this.simulation.force('link').links(this.state.links);
    this.simulation.alpha(1).restart();
  }

  public setData(nodes: GraphNode[], links: GraphLink[]): void {
    this.state.nodes = nodes;
    this.state.links = links;
    this.updateGraph();
  }

  public addNode(node: GraphNode): void {
    this.state.nodes.push(node);
    this.updateGraph();
  }

  public addLink(link: GraphLink): void {
    this.state.links.push(link);
    this.updateGraph();
  }

  public setSelectedNode(nodeId: string | undefined): void {
    this.state.selectedNode = nodeId;
    this.updateGraphStyles();
  }

  private tick(): void {
    this.svg.selectAll('.link')
      .attr('x1', (d: any) => d.source.x)
      .attr('y1', (d: any) => d.source.y)
      .attr('x2', (d: any) => d.target.x)
      .attr('y2', (d: any) => d.target.y);

    this.svg.selectAll('.node')
      .attr('transform', (d: any) => `translate(${d.x},${d.y})`);
  }

  private dragStarted(event: any, d: any): void {
    if (!event.active) this.simulation.alphaTarget(0.3).restart();
    d.fx = d.x;
    d.fy = d.y;
  }

  private dragged(event: any, d: any): void {
    d.fx = event.x;
    d.fy = event.y;
  }

  private dragEnded(event: any, d: any): void {
    if (!event.active) this.simulation.alphaTarget(0);
    d.fx = null;
    d.fy = null;
  }

  private nodeClicked(node: GraphNode): void {
    this.state.selectedNode = node.id;
    this.updateGraphStyles();
    
    // Emit event for external listeners
    this.container.dispatchEvent(new CustomEvent('node-clicked', {
      detail: { node }
    }));
  }

  private nodeHovered(node: GraphNode | null): void {
    this.state.hoveredNode = node?.id;
    this.updateGraphStyles();
  }

  private updateGraphStyles(): void {
    // Highlight selected node
    this.svg.selectAll('.node')
      .style('opacity', (d: any) => {
        if (this.state.selectedNode && d.id !== this.state.selectedNode) {
          return 0.3;
        }
        return 1;
      });

    // Highlight hovered node
    this.svg.selectAll('.node')
      .select('circle')
      .attr('stroke-width', (d: any) => {
        if (this.state.hoveredNode === d.id) {
          return 4;
        }
        return 2;
      });

    // Highlight related nodes
    if (this.state.selectedNode) {
      const selectedNode = this.state.nodes.find(n => n.id === this.state.selectedNode);
      if (selectedNode) {
        const relatedLinks = this.state.links.filter(l => 
          l.source === selectedNode.id || l.target === selectedNode.id
        );
        
        this.svg.selectAll('.node circle')
          .attr('fill', (d: any) => {
            const isRelated = relatedLinks.some(l => 
              (l.source === d.id || l.target === d.id) && d.id !== this.state.selectedNode
            );
            return isRelated ? '#FF9800' : d.color || '#4CAF50';
          });
      }
    }
  }

  public refresh(): void {
    this.simulation.alpha(1).restart();
    this.tick();
  }

  public zoomIn(): void {
    this.svg.transition().duration(250).call(require('d3-zoom').zoom().scaleBy, 1.2);
  }

  public zoomOut(): void {
    this.svg.transition().duration(250).call(require('d3-zoom').zoom().scaleBy, 0.8);
  }

  public resetZoom(): void {
    this.svg.transition().duration(250).call(require('d3-zoom').zoom().transform, require('d3-zoom').zoomIdentity);
  }

  public destroy(): void {
    if (this.simulation) {
      this.simulation.stop();
    }
    if (this.svg) {
      this.svg.remove();
    }
  }
}

// Helper function to create graph from Home Assistant entities
export function createGraphFromEntities(entities: Record<string, any>): { nodes: GraphNode[], links: GraphLink[] } {
  const nodes: GraphNode[] = [];
  const links: GraphLink[] = [];

  // Create nodes for each entity
  Object.entries(entities).forEach(([entityId, entity]: [string, any]) => {
    nodes.push({
      id: entityId,
      type: 'entity',
      label: entityId.replace('.', '\n'),
      color: getEntityColor(entity),
      value: getEntityValue(entity)
    });
  });

  // Create links based on entity relationships (simplified - could be enhanced with actual relationship data)
  nodes.forEach((sourceNode, sourceIndex) => {
    nodes.forEach((targetNode, targetIndex) => {
      if (sourceIndex < targetIndex) {
        // Simple heuristic: link entities with similar states or in same domain
        const sourceDomain = sourceNode.id.split('.')[0];
        const targetDomain = targetNode.id.split('.')[0];
        
        if (sourceDomain === targetDomain) {
          links.push({
            source: sourceNode.id,
            target: targetNode.id,
            type: 'domain',
            value: 1
          });
        }
      }
    });
  });

  return { nodes, links };
}

function getEntityColor(entity: any): string {
  const state = entity?.state?.state;
  if (state === 'on' || state === 'active' || state === 'home') {
    return '#4CAF50'; // Green
  } else if (state === 'off' || state === 'idle' || state === 'unavailable') {
    return '#9E9E9E'; // Gray
  } else if (state === 'problem' || state === 'error' || state === 'normal') {
    return '#F44336'; // Red
  } else {
    return '#2196F3'; // Blue
  }
}

function getEntityValue(entity: any): number | undefined {
  const state = entity?.state?.state;
  const numericState = entity?.state?.attributes?.numeric_state;
  
  if (numericState !== undefined) {
    return numericState;
  }
  
  if (typeof state === 'number') {
    return state;
  }
  
  return undefined;
}

export default BrainGraphPanel;
