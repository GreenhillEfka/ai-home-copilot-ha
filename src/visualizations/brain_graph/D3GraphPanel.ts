// D3-based Graph Visualization Panel
import { svg, select, forceSimulation, forceLink, forceManyBody, forceCenter, drag } from 'd3';

export interface GraphNode {
  id: string;
  type: 'entity' | 'mood' | 'neuron' | 'habitus' | 'behavior';
  label: string;
  value?: number;
  color?: string;
  x?: number;
  y?: number;
  size?: number;
}

export interface GraphLink {
  source: string | GraphNode;
  target: string | GraphNode;
  value?: number;
  type?: string;
}

export class D3GraphPanel {
  private container: HTMLElement;
  private width: number;
  private height: number;
  private svg: any;
  private simulation: any;
  private nodes: GraphNode[] = [];
  private links: GraphLink[] = [];
  private zoom: any;
  private selectedNode?: string;

  constructor(container: HTMLElement, options: { width?: number; height?: number } = {}) {
    this.container = container;
    this.width = options.width || 800;
    this.height = options.height || 600;
    
    this.initGraph();
  }

  private initGraph(): void {
    this.svg = select(this.container)
      .append('svg')
      .attr('width', this.width)
      .attr('height', this.height)
      .attr('class', 'd3-graph-container');

    // Zoom behavior
    this.zoom = select(this.svg).call(
      require('d3-zoom').zoom()
        .scaleExtent([0.1, 4])
        .on('zoom', (event: any) => {
          this.updateGraphTransform(event.transform);
        })
    );

    // Force simulation
    this.simulation = forceSimulation<GraphNode>()
      .force('link', forceLink<GraphNode, GraphLink>().id((d: any) => d.id).distance(100))
      .force('charge', forceManyBody().strength(-30))
      .force('center', forceCenter(this.width / 2, this.height / 2))
      .on('tick', () => this.tick());
  }

  public setData(nodes: GraphNode[], links: GraphLink[]): void {
    this.nodes = nodes;
    this.links = links;
    
    this.simulation.nodes(nodes);
    this.simulation.force('link').links(links);
    this.simulation.alpha(1).restart();
  }

  public updateGraphTransform(transform: any): void {
    this.svg.selectAll('.graph-elements')
      .attr('transform', `translate(${transform.x},${transform.y}) scale(${transform.k})`);
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

  public destroy(): void {
    if (this.simulation) {
      this.simulation.stop();
    }
    if (this.svg) {
      this.svg.remove();
    }
  }

  // Getters for React integration
  public getNodes(): GraphNode[] {
    return this.nodes;
  }

  public getLinks(): GraphLink[] {
    return this.links;
  }
}

export default D3GraphPanel;
