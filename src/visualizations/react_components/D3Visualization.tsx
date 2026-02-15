// React Components for Interactive Visualization - with D3.js
import React, { useState, useEffect, useRef, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { svg, select, forceSimulation, forceLink, forceManyBody, forceCenter, drag } from 'd3';

// Types
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
  strength?: number;
}

// Color palettes
const COLORS = {
  entity: '#2196F3',
  mood: '#FF9800',
  neuron: '#4CAF50',
  habitus: '#9C27B0',
  behavior: '#607D8B',
  link: '#9E9E9E'
};

// Utility functions
const getNodeColor = (type: string): string => COLORS[type as keyof typeof COLORS] || '#9E9E9E';

const getNodeSize = (type: string, value?: number): number => {
  const baseSize = 20;
  if (value) return baseSize + value * 2;
  return baseSize;
};

// Brain Graph Component with D3 integration
interface BrainGraphProps {
  data: { nodes: GraphNode[]; links: GraphLink[] };
  onNodeClick?: (node: GraphNode) => void;
  onZoomChange?: (zoom: number) => void;
  height?: number;
}

export const BrainGraph: React.FC<BrainGraphProps> = ({ 
  data, 
  onNodeClick, 
  onZoomChange,
  height = 500 
}) => {
  const [zoom, setZoom] = useState(1);
  const [panX, setPanX] = useState(0);
  const [panY, setPanY] = useState(0);
  const [selectedNode, setSelectedNode] = useState<string>();
  const [hoveredNode, setHoveredNode] = useState<string>();
  
  const svgRef = useRef<SVGSVGElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  // Effect for data changes
  useEffect(() => {
    if (!svgRef.current) return;
    
    // Clear existing elements
    select(svgRef.current).selectAll('*').remove();
    
    // Initialize D3 graph with data
    const width = containerRef.current?.clientWidth || 800;
    
    const svgElement = select(svgRef.current)
      .attr('width', width)
      .attr('height', height);

    // Zoom behavior
    const zoomBehavior = require('d3-zoom').zoom()
      .scaleExtent([0.1, 4])
      .on('zoom', (event: any) => {
        setPanX(event.transform.x);
        setPanY(event.transform.y);
        setZoom(event.transform.k);
        if (onZoomChange) onZoomChange(event.transform.k);
      });

    svgElement.call(zoomBehavior);

    // Draw links
    svgElement.selectAll('.link')
      .data(data.links)
      .enter()
      .append('line')
      .attr('class', 'link')
      .attr('stroke', (d: any) => d.type === 'domain' ? COLORS.entity : COLORS.link)
      .attr('stroke-width', 2)
      .attr('opacity', 0.6);

    // Draw nodes
    const nodes = svgElement.selectAll('.node')
      .data(data.nodes)
      .enter()
      .append('g')
      .attr('class', 'node')
      .attr('cursor', 'pointer')
      .on('click', (event: any, d: any) => {
        setSelectedNode(d.id);
        if (onNodeClick) onNodeClick(d);
      })
      .on('mouseover', (event: any, d: any) => {
        setHoveredNode(d.id);
      })
      .on('mouseout', () => {
        setHoveredNode(undefined);
      });

    // Node circles
    nodes.append('circle')
      .attr('r', (d: any) => d.size || getNodeSize(d.type, d.value))
      .attr('fill', (d: any) => getNodeColor(d.type))
      .attr('stroke', '#fff')
      .attr('stroke-width', 2)
      .attr('opacity', (d: any) => {
        if (selectedNode && d.id !== selectedNode) return 0.6;
        return 1;
      })
      .attr('stroke-width', (d: any) => {
        if (d.id === selectedNode || d.id === hoveredNode) return 3;
        return 2;
      });

    // Node labels
    nodes.append('text')
      .attr('dy', (d: any) => (d.size || getNodeSize(d.type, d.value)) + 15)
      .attr('text-anchor', 'middle')
      .attr('font-size', '12px')
      .attr('fill', '#fff')
      .text((d: any) => d.label);
  }, [data, selectedNode, hoveredNode, height, onNodeClick, onZoomChange]);

  return (
    <div 
      ref={containerRef}
      className="brain-graph-container"
      style={{ 
        height: `${height}px`,
        width: '100%',
        position: 'relative',
        overflow: 'hidden'
      }}
    >
      <svg
        ref={svgRef}
        className="brain-graph-svg"
        style={{ width: '100%', height: '100%' }}
      >
        <g transform={`translate(${panX},${panY}) scale(${zoom})`}>
          <g className="graph-elements">
            {/* Links will be drawn by D3 */}
          </g>
        </g>
      </svg>

      {/* Zoom controls */}
      <div className="zoom-controls" style={{ position: 'absolute', top: 20, left: 20 }}>
        <div className="zoom-control-btn" onClick={() => setZoom(z => Math.min(z * 1.5, 4))}>+</div>
        <div className="zoom-control-btn" onClick={() => setZoom(z => Math.max(z / 1.5, 0.1))}>-</div>
        <div className="zoom-display">{zoom.toFixed(2)}x</div>
      </div>
    </div>
  );
};

// Mood Context Component
interface MoodContextProps {
  mood: {
    type: string;
    intensity: number;
    confidence: number;
    emotions: Record<string, number>;
    timestamp: string;
  };
  onEmotionSelect?: (emotion: string) => void;
}

export const MoodContext: React.FC<MoodContextProps> = ({ mood, onEmotionSelect }) => {
  return (
    <motion.div
      className="mood-context"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
    >
      <div className="mood-header">
        <div className="mood-icon">
          {mood.type === 'happy' && '😊'}
          {mood.type === 'sad' && '😢'}
          {mood.type === 'angry' && '😠'}
          {mood.type === 'excited' && '⚡'}
          {mood.type === 'calm' && '🌿'}
          {mood.type === 'neutral' && '😐'}
          {mood.type === 'focused' && '🎯'}
          {mood.type === 'creative' && '🎨'}
          {mood.type === 'tired' && '😴'}
        </div>
        
        <div className="mood-info">
          <h3 className="mood-title">
            {mood.type.charAt(0).toUpperCase() + mood.type.slice(1)}
          </h3>
          <div className="mood-meta">
            <span className="confidence">
              {(mood.confidence * 100).toFixed(0)}% confident
            </span>
            <span className="timestamp">
              {new Date(mood.timestamp).toLocaleTimeString()}
            </span>
          </div>
        </div>
      </div>

      <div className="emotions">
        <h4 className="emotions-title">Emotion Breakdown</h4>
        <div className="emotions-grid">
          {Object.entries(mood.emotions).map(([name, value]) => (
            <motion.button
              key={name}
              className="emotion-item"
              onClick={() => onEmotionSelect?.(name)}
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
            >
              <div className="emotion-bar">
                <motion.div
                  className="emotion-fill"
                  initial={{ width: 0 }}
                  animate={{ width: `${value * 100}%` }}
                  transition={{ duration: 0.5 }}
                />
              </div>
              <span className="emotion-name">{name}</span>
              <span className="emotion-value">{(value * 100).toFixed(0)}%</span>
            </motion.button>
          ))}
        </div>
      </div>
    </motion.div>
  );
};

// Neuron Status Component
interface NeuronStatusProps {
  neurons: {
    id: string;
    name: string;
    active: boolean;
    firingRate: number;
    lastFired: string;
  }[];
  onSelectNeuron?: (neuron: any) => void;
}

export const NeuronStatus: React.FC<NeuronStatusProps> = ({ neurons, onSelectNeuron }) => {
  const activeNeurons = neurons.filter(n => n.active);
  const totalNeurons = neurons.length;
  const activityRate = totalNeurons > 0 ? (activeNeurons.length / totalNeurons) * 100 : 0;

  return (
    <motion.div
      className="neuron-status"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.3 }}
    >
      <div className="neuron-header">
        <h3 className="neuron-title">Neuron Activity</h3>
        <div className="neuron-stats">
          <div className="stat-item">
            <span className="stat-value active">{activeNeurons.length}</span>
            <span className="stat-label">Active</span>
          </div>
          <div className="stat-item">
            <span className="stat-value">{totalNeurons}</span>
            <span className="stat-label">Total</span>
          </div>
          <div className="stat-item">
            <span className="stat-value">{activityRate.toFixed(1)}%</span>
            <span className="stat-label">Active</span>
          </div>
        </div>
      </div>

      <div className="neuron-grid">
        {neurons.map((neuron) => (
          <motion.div
            key={neuron.id}
            className={`neuron-item ${neuron.active ? 'active' : ''}`}
            onClick={() => onSelectNeuron?.(neuron)}
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
          >
            <div className="neuron-icon">
              {neuron.active ? '⚡' : '•'}
            </div>
            <div className="neuron-info">
              <div className="neuron-name">{neuron.name}</div>
              <div className="neuron-details">
                <span className="firing-rate">
                  {neuron.firingRate} Hz
                </span>
                <span className="last-fired">
                  {neuron.lastFired ? 'Last: ' + neuron.lastFired : 'Never'}
                </span>
              </div>
            </div>
          </motion.div>
        ))}
      </div>
    </motion.div>
  );
};

// Habitus Zone Component
interface HabitusZoneProps {
  zones: {
    id: string;
    name: string;
    description: string;
    active: boolean;
    settings: {
      ambience: string;
      activity: string;
      optimization: string;
    };
    mood: {
      type: string;
      intensity: number;
    };
  }[];
  selectedZone?: string;
  onSelectZone?: (zone: any) => void;
}

export const HabitusZone: React.FC<HabitusZoneProps> = ({ zones, selectedZone, onSelectZone }) => {
  const currentZone = zones.find(z => z.id === selectedZone) || zones[0];

  return (
    <motion.div
      className="habitus-zone"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.3 }}
    >
      <div className="zone-selector">
        {zones.map((zone) => (
          <motion.button
            key={zone.id}
            className={`zone-btn ${zone.id === currentZone?.id ? 'active' : ''}`}
            onClick={() => onSelectZone?.(zone)}
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
          >
            {zone.name}
          </motion.button>
        ))}
      </div>

      {currentZone && (
        <div className="zone-content">
          <div className="zone-header">
            <div className="zone-icon">🏠</div>
            <div className="zone-info">
              <h3 className="zone-name">{currentZone.name}</h3>
              <p className="zone-description">{currentZone.description}</p>
            </div>
          </div>

          <div className="zone-settings">
            <div className="setting">
              <span className="setting-label">Ambience</span>
              <span className="setting-value">{currentZone.settings.ambience}</span>
            </div>
            <div className="setting">
              <span className="setting-label">Activity</span>
              <span className="setting-value">{currentZone.settings.activity}</span>
            </div>
            <div className="setting">
              <span className="setting-label">Optimization</span>
              <span className="setting-value">{currentZone.settings.optimization}</span>
            </div>
          </div>

          <div className="zone-mood">
            <div className="mood-label">Current Mood</div>
            <div className="mood-bar">
              <motion.div
                className="mood-fill"
                initial={{ width: 0 }}
                animate={{ width: `${currentZone.mood.intensity * 100}%` }}
                transition={{ duration: 0.5 }}
              />
            </div>
            <div className="mood-text">{currentZone.mood.type}</div>
          </div>
        </div>
      )}
    </motion.div>
  );
};

// Main Visualization Container
interface VisualizationProps {
  nodes: GraphNode[];
  links: GraphLink[];
  mood?: {
    type: string;
    intensity: number;
    confidence: number;
    emotions: Record<string, number>;
    timestamp: string;
  };
  neurons?: {
    id: string;
    name: string;
    active: boolean;
    firingRate: number;
    lastFired: string;
  }[];
  zones?: {
    id: string;
    name: string;
    description: string;
    active: boolean;
    settings: {
      ambience: string;
      activity: string;
      optimization: string;
    };
    mood: {
      type: string;
      intensity: number;
    };
  }[];
}

export const Visualization: React.FC<VisualizationProps> = ({
  nodes,
  links,
  mood,
  neurons,
  zones
}) => {
  const [selectedNode, setSelectedNode] = useState<string>();

  return (
    <div className="visualization-container">
      <div className="visualization-header">
        <h2 className="visualization-title">PilotSuite Visualizer</h2>
        <div className="visualization-controls">
          <button className="control-btn">
            <span className="icon">🔄</span> Refresh
          </button>
          <button className="control-btn">
            <span className="icon">💾</span> Save
          </button>
        </div>
      </div>

      <div className="visualization-content">
        <div className="left-panel">
          <BrainGraph 
            data={{ nodes, links }} 
            onNodeClick={(node) => setSelectedNode(node.id)}
            onZoomChange={(zoom) => console.log('Zoom:', zoom)}
            height={500}
          />
        </div>

        <div className="right-panel">
          <div className="panel-grid">
            {mood && (
              <div className="panel-item">
                <MoodContext mood={mood} />
              </div>
            )}
            
            {neurons && (
              <div className="panel-item">
                <NeuronStatus neurons={neurons} />
              </div>
            )}
            
            {zones && (
              <div className="panel-item">
                <HabitusZone zones={zones} selectedZone={selectedNode} />
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

// Export all components
export default {
  BrainGraph,
  MoodContext,
  NeuronStatus,
  HabitusZone,
  Visualization
};
