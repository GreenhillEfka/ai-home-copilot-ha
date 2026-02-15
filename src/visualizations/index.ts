// Visualization Module - Main Entry Point
export * from './brain_graph';
export * from './lovelace_cards';
export * from './react_components';

// Visualization Manager
export class VisualizationManager {
  private brainGraphPanels: Map<string, any> = new Map();
  private initialized: boolean = false;

  public initialize(): void {
    if (this.initialized) return;
    
    // Register custom elements if in browser environment
    if (typeof window !== 'undefined' && customElements) {
      try {
        import('./lovelace_cards').then(() => {
          // Custom elements are auto-registered via decorators
          console.log('LOVELACE: Custom cards registered');
        });
      } catch (error) {
        console.warn('Failed to register custom elements:', error);
      }
    }

    this.initialized = true;
    console.log('Visualization Manager initialized');
  }

  public createBrainGraph(container: HTMLElement, config?: any): any {
    const { BrainGraphPanel } = require('./brain_graph');
    const panel = new BrainGraphPanel(container, config);
    
    const panelId = `brain-graph-${Date.now()}`;
    this.brainGraphPanels.set(panelId, panel);
    
    return panelId;
  }

  public updateBrainGraph(panelId: string, nodes: any[], links: any[]): boolean {
    const panel = this.brainGraphPanels.get(panelId);
    if (!panel) return false;
    
    panel.setData(nodes, links);
    return true;
  }

  public destroyBrainGraph(panelId: string): boolean {
    const panel = this.brainGraphPanels.get(panelId);
    if (!panel) return false;
    
    panel.destroy();
    this.brainGraphPanels.delete(panelId);
    return true;
  }

  public destroyAll(): void {
    this.brainGraphPanels.forEach((panel, id) => {
      panel.destroy();
    });
    this.brainGraphPanels.clear();
  }

  public async loadEntities(hass: any): Promise<{ nodes: any[], links: any[] }> {
    const { createGraphFromEntities } = require('./brain_graph');
    const entities = hass.states;
    return createGraphFromEntities(entities);
  }

  public async getMoodData(hass: any, entity: string): Promise<any> {
    const stateObj = hass.states[entity];
    if (!stateObj) return null;
    
    return {
      type: stateObj.state,
      intensity: stateObj.attributes?.intensity || 0.5,
      confidence: stateObj.attributes?.confidence || 0.8,
      emotions: stateObj.attributes?.emotions || {},
      timestamp: stateObj.attributes?.last_updated || new Date().toISOString()
    };
  }

  public async getNeuronData(hass: any, entity: string): Promise<any[]> {
    const stateObj = hass.states[entity];
    if (!stateObj) return [];
    
    const neurons = stateObj.attributes?.neurons || [];
    return neurons.map((n: any) => ({
      id: n.id || `neuron-${Date.now()}`,
      name: n.name || 'Unnamed',
      active: n.active || false,
      firingRate: n.firing_rate || 0,
      lastFired: n.last_fired || ''
    }));
  }

  public async getHabitusData(hass: any, entity: string): Promise<any[]> {
    const stateObj = hass.states[entity];
    if (!stateObj) return [];
    
    const zones = stateObj.attributes?.zones || [];
    return zones.map((z: any) => ({
      id: z.id || `zone-${Date.now()}`,
      name: z.name || 'Unknown',
      description: z.description || '',
      active: z.active || false,
      settings: z.settings || {},
      mood: z.mood || { type: 'neutral', intensity: 0.5 }
    }));
  }
}

// Export singleton instance
export const visualizationManager = new VisualizationManager();

// Initialize on module load
if (typeof window !== 'undefined') {
  visualizationManager.initialize();
}

export default visualizationManager;
