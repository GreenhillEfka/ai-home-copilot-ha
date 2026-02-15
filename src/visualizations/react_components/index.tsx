// React Components for Interactive Visualization
import React, { useState, useEffect, useRef, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { EntityId, HassEntity } from '@openclaw/types';
import { createPortal } from 'react-dom';

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

export interface MoodState {
  type: string;
  intensity: number;
  confidence: number;
  emotions: Record<string, number>;
  timestamp: string;
}

export interface NeuronState {
  id: string;
  name: string;
  active: boolean;
  firingRate: number;
  lastFired: string;
}

export interface HabitusZone {
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
}

export interface VisualizationState {
  nodes: GraphNode[];
  links: GraphLink[];
  selectedNode?: string;
  hoveredNode?: string;
  zoom: number;
  panX: number;
  panY: number;
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

// Brain Graph Component
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
  const [state, setState] = useState<VisualizationState>({
    nodes: data.nodes,
    links: data.links,
    zoom: 1,
    panX: 0,
    panY: 0
  });

  const svgRef = useRef<SVGSVGElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  // Handle data changes
  useEffect(() => {
    setState(prev => ({
      ...prev,
      nodes: data.nodes,
      links: data.links
    }));
  }, [data]);

  // Handle zoom/pan changes
  const handleZoom = (event: any) => {
    const { x, y, k } = event.transform;
    setState(prev => ({
      ...prev,
      panX: x,
      panY: y,
      zoom: k
    }));
    
    if (onZoomChange) {
      onZoomChange(k);
    }
  };

  // Handle node click
  const handleNodeClick = (node: GraphNode) => {
    setState(prev => ({ ...prev, selectedNode: node.id }));
    if (onNodeClick) {
      onNodeClick(node);
    }
  };

  // Handle node hover
  const handleNodeHover = (nodeId?: string) => {
    setState(prev => ({ ...prev, hoveredNode: nodeId }));
  };

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
        <g transform={`translate(${state.panX},${state.panY}) scale(${state.zoom})`}>
          {/* Draw links */}
          {state.links.map((link, index) => {
            const sourceNode = typeof link.source === 'string' 
              ? state.nodes.find(n => n.id === link.source)
              : link.source;
            const targetNode = typeof link.target === 'string' 
              ? state.nodes.find(n => n.id === link.target)
              : link.target;

            if (!sourceNode || !targetNode) return null;

            return (
              <motion.line
                key={`link-${index}`}
                x1={sourceNode.x || 0}
                y1={sourceNode.y || 0}
                x2={targetNode.x || 0}
                y2={targetNode.y || 0}
                stroke={COLORS.link}
                strokeWidth={2}
                opacity={0.6}
                initial={{ pathLength: 0, opacity: 0 }}
                animate={{ 
                  pathLength: 1, 
                  opacity: 0.6,
                  stroke: link.type === 'domain' ? COLORS.entity : COLORS.link
                }}
                transition={{ duration: 0.5 }}
              />
            );
          })}

          {/* Draw nodes */}
          {state.nodes.map((node) => {
            const isSelected = state.selectedNode === node.id;
            const isHovered = state.hoveredNode === node.id;
            const opacity = isSelected ? 1 : isHovered ? 0.8 : 0.6;
            const strokeWidth = isSelected || isHovered ? 3 : 2;

            return (
              <g
                key={node.id}
                transform={`translate(${node.x || 0},${node.y || 0})`}
                onClick={() => handleNodeClick(node)}
                onMouseEnter={() => handleNodeHover(node.id)}
                onMouseLeave={() => handleNodeHover(undefined)}
                style={{ cursor: 'pointer' }}
              >
                {/* Node circle */}
                <motion.circle
                  r={node.size || getNodeSize(node.type, node.value)}
                  fill={getNodeColor(node.type)}
                  stroke="#fff"
                  strokeWidth={strokeWidth}
                  initial={{ scale: 0 }}
                  animate={{ scale: 1 }}
                  transition={{ duration: 0.3 }}
                />

                {/* Node label */}
                <text
                  dy={node.size || getNodeSize(node.type, node.value) + 15}
                  textAnchor="middle"
                  fill="#fff"
                  fontSize="12"
                  fontWeight={isSelected ? 'bold' : 'normal'}
                >
                  {node.label}
                </text>
              </g>
            );
          })}
        </g>

        {/* Zoom controls */}
        <g transform="translate(20, 20)">
          <rect width="40" height="120" rx="5" fill="rgba(0,0,0,0.5)" />
          
          <text x="20" y="30" textAnchor="middle" fill="#fff" fontSize="14">Zoom</text>
          <text x="20" y="60" textAnchor="middle" fill="#fff" fontSize="12">
            {state.zoom.toFixed(2)}x
          </text>
          
          <rect 
            x="5" 
            y="75" 
            width="30" 
            height="20" 
            rx="3" 
            fill={state.zoom > 1 ? "rgba(76,175,80,0.8)" : "rgba(255,255,255,0.2)"}
            onClick={() => {
              setState(prev => ({ ...prev, zoom: Math.min(prev.zoom * 1.5, 4) }));
              if (onZoomChange) onZoomChange(Math.min(state.zoom * 1.5, 4));
            }}
            style={{ cursor: 'pointer' }}
          />
          <text x="20" y="88" textAnchor="middle" fill="#fff" fontSize="10">+</text>
          
          <rect 
            x="5" 
            y="105" 
            width="30" 
            height="20" 
            rx="3" 
            fill={state.zoom < 2 ? "rgba(76,175,80,0.8)" : "rgba(255,255,255,0.2)"}
            onClick={() => {
              setState(prev => ({ ...prev, zoom: Math.max(prev.zoom / 1.5, 0.1) }));
              if (onZoomChange) onZoomChange(Math.max(state.zoom / 1.5, 0.1));
            }}
            style={{ cursor: 'pointer' }}
          />
          <text x="20" y="118" textAnchor="middle" fill="#fff" fontSize="10">-</text>
        </g>

        {/* Legend */}
        <g transform="translate(20, height - 150)" className="brain-graph-legend">
          {Object.entries(COLORS).filter(([key]) => key !== 'link').map(([type, color], index) => (
            <g key={type} transform={`translate(0, ${index * 25})`}>
              <circle r="8" fill={color} />
              <text x="15" y="5" fill="#fff" fontSize="12">
                {type.charAt(0).toUpperCase() + type.slice(1)}
              </text>
            </g>
          ))}
        </g>
      </svg>
    </div>
  );
};

// Mood Context Component
interface MoodContextProps {
  mood: MoodState;
  onEmotionSelect?: (emotion: string) => void;
}

export const MoodContext: React.FC<MoodContextProps> = ({ mood, onEmotionSelect }) => {
  const [expanded, setExpanded] = useState(false);

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
  neurons: NeuronState[];
  onSelectNeuron?: (neuron: NeuronState) => void;
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
  zones: HabitusZone[];
  selectedZone?: string;
  onSelectZone?: (zone: HabitusZone) => void;
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
  mood?: MoodState;
  neurons?: NeuronState[];
  zones?: HabitusZone[];
}

export const Visualization: React.FC<VisualizationProps> = ({
  nodes,
  links,
  mood,
  neurons,
  zones
}) => {
  const [selectedNode, setSelectedNode] = useState<string>();
  const [zoom, setZoom] = useState(1);

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
            onZoomChange={setZoom}
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

// CSS Styles
const styles = `
.brain-graph-container {
  position: relative;
  background: #1a1a2e;
  border-radius: 8px;
  overflow: hidden;
}

.brain-graph-svg {
  display: block;
}

.brain-graph-legend {
  position: absolute;
  bottom: 20px;
  left: 20px;
  background: rgba(0,0,0,0.5);
  padding: 10px;
  border-radius: 8px;
}

.mood-context {
  background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
  border-radius: 8px;
  padding: 20px;
  color: #fff;
}

.mood-header {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 20px;
}

.mood-icon {
  font-size: 48px;
}

.mood-title {
  font-size: 24px;
  margin: 0;
  font-weight: 600;
}

.mood-meta {
  display: flex;
  gap: 16px;
  font-size: 14px;
  color: #aaa;
}

.confidence, .timestamp {
  color: #888;
}

.emotions {
  margin-top: 20px;
}

.emotions-title {
  font-size: 14px;
  color: #aaa;
  margin-bottom: 12px;
}

.emotions-grid {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.emotion-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px;
  background: rgba(255,255,255,0.1);
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.emotion-bar {
  flex: 1;
  height: 8px;
  background: rgba(0,0,0,0.3);
  border-radius: 4px;
  overflow: hidden;
}

.emotion-fill {
  height: 100%;
  background: linear-gradient(90deg, #FF9800, #FF5722);
  border-radius: 4px;
  transition: width 0.3s ease;
}

.emotion-name {
  width: 100px;
  font-size: 14px;
}

.emotion-value {
  width: 50px;
  text-align: right;
  font-size: 14px;
  font-weight: 500;
}

.neuron-status {
  background: linear-gradient(135deg, #1a1a2e 0%, #1e3c72 100%);
  border-radius: 8px;
  padding: 20px;
  color: #fff;
}

.neuron-header {
  margin-bottom: 20px;
}

.neuron-title {
  font-size: 18px;
  margin: 0 0 16px 0;
}

.neuron-stats {
  display: flex;
  gap: 24px;
}

.stat-item {
  text-align: center;
}

.stat-value {
  display: block;
  font-size: 24px;
  font-weight: bold;
  color: #4CAF50;
}

.stat-label {
  font-size: 12px;
  color: #aaa;
}

.neuron-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
  gap: 12px;
}

.neuron-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background: rgba(255,255,255,0.05);
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.neuron-item.active {
  background: rgba(76,175,80,0.1);
  border: 1px solid #4CAF50;
}

.neuron-icon {
  font-size: 20px;
}

.neuron-name {
  font-size: 14px;
  font-weight: 500;
  margin-bottom: 4px;
}

.neuron-details {
  font-size: 12px;
  color: #888;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.habitus-zone {
  background: linear-gradient(135deg, #1a1a2e 0%, #2a1a3e 100%);
  border-radius: 8px;
  padding: 20px;
  color: #fff;
}

.zone-selector {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 20px;
}

.zone-btn {
  padding: 8px 16px;
  background: rgba(255,255,255,0.1);
  border: 1px solid rgba(255,255,255,0.2);
  border-radius: 20px;
  cursor: pointer;
  font-size: 14px;
  color: #fff;
  transition: all 0.3s ease;
}

.zone-btn.active {
  background: #9C27B0;
  border-color: #9C27B0;
}

.zone-content {
  margin-bottom: 20px;
}

.zone-header {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 16px;
}

.zone-icon {
  font-size: 32px;
}

.zone-name {
  font-size: 20px;
  font-weight: bold;
  margin: 0;
}

.zone-description {
  font-size: 14px;
  color: #aaa;
  margin: 0;
}

.zone-settings {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: 16px;
  margin-bottom: 16px;
}

.setting {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.setting-label {
  font-size: 12px;
  color: #888;
}

.setting-value {
  font-size: 14px;
  font-weight: 500;
}

.zone-mood {
  margin-top: 16px;
}

.mood-label {
  font-size: 14px;
  color: #888;
  margin-bottom: 8px;
}

.mood-bar {
  height: 8px;
  background: rgba(255,255,255,0.1);
  border-radius: 4px;
  overflow: hidden;
  margin-bottom: 8px;
}

.mood-fill {
  height: 100%;
  background: linear-gradient(90deg, #9C27B0, #E91E63);
  border-radius: 4px;
  transition: width 0.3s ease;
}

.mood-text {
  font-size: 14px;
  color: #fff;
  font-weight: 500;
}

.visualization-container {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.visualization-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.visualization-title {
  font-size: 24px;
  margin: 0;
}

.visualization-controls {
  display: flex;
  gap: 12px;
}

.control-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  background: #2196F3;
  border: none;
  border-radius: 4px;
  color: #fff;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.3s ease;
}

.control-btn:hover {
  background: #1976D2;
}

.visualization-content {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
}

.left-panel {
  background: #1a1a2e;
  border-radius: 8px;
  padding: 16px;
}

.right-panel {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.panel-grid {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.panel-item {
  flex: 1;
}

.icon {
  font-size: 16px;
}

@media (max-width: 1200px) {
  .visualization-content {
    grid-template-columns: 1fr;
  }
  
  .left-panel {
    max-height: 500px;
  }
}
`;

// Inject styles
const styleSheet = document.createElement("style");
styleSheet.innerText = styles;
document.head.appendChild(styleSheet);
