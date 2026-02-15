// AI Home CoPilot API Types
// Generated from OpenAPI spec v0.4.33

// ==================== Common ====================

export interface ErrorResponse {
  status: 'error';
  message: string;
  code?: string;
}

// ==================== Habitus ====================

export interface HabitusStatus {
  status: 'ok' | 'error';
  version: string;
  statistics: {
    total_rules: number;
    total_events: number;
    last_mining_ms?: number;
  };
  config: {
    windows: number[];
    min_support_A: number;
    min_hits: number;
    min_confidence: number;
    min_lift: number;
    max_rules: number;
  };
}

export interface Rule {
  A: string;
  B: string;
  dt_sec: number;
  nA: number;
  nB: number;
  nAB: number;
  confidence: number;
  confidence_lb: number;
  lift: number;
  leverage: number;
  score: number;
  observation_period_days?: number;
  created_at_ms?: number;
  evidence?: {
    hit_examples: Array<Record<string, unknown>>;
    miss_examples: Array<Record<string, unknown>>;
    latency_quantiles: number[];
  };
}

export interface RulesResponse {
  status: 'ok' | 'error';
  total_rules: number;
  rules: Rule[];
}

export interface MineRequest {
  events: Array<Record<string, unknown>>;
  config?: Partial<MiningConfig>;
}

export interface MiningConfig {
  windows: number[];
  min_support_A: number;
  min_support_B: number;
  min_hits: number;
  min_confidence: number;
  min_confidence_lb: number;
  min_lift: number;
  min_leverage: number;
  max_rules: number;
  max_evidence_examples: number;
  default_cooldown: number;
  context_features: string[];
  include_domains: string[];
  exclude_domains: string[];
  exclude_self_rules: boolean;
  exclude_same_entity: boolean;
  min_stability_days: number;
  anonymize_entity_ids: boolean;
}

export interface MineResponse {
  status: 'ok' | 'error';
  mining_time_sec: number;
  total_input_events: number;
  discovered_rules: number;
  top_rules: Array<{
    A: string;
    B: string;
    confidence: number;
    lift: number;
    dt_sec: number;
  }>;
}

export interface Zone {
  zone_id: string;
  name: string;
  entities: string[];
}

export interface ZonesResponse {
  status: 'ok' | 'error';
  zones: Zone[];
}

export interface DashboardCardsResponse {
  status: 'ok' | 'error';
  cards: Array<Record<string, unknown>>;
}

// ==================== Graph ====================

export interface GraphNode {
  id: string;
  type: string;
  label: string;
  domain?: string;
  score?: number;
}

export interface GraphEdge {
  source: string;
  target: string;
  type: string;
  weight: number;
}

export interface GraphState {
  status: 'ok' | 'error';
  nodes: GraphNode[];
  edges: GraphEdge[];
}

export interface GraphSyncRequest {
  entities: Array<Record<string, unknown>>;
  full_sync?: boolean;
}

export interface GraphSyncResponse {
  status: 'ok' | 'error';
  nodes_added: number;
  nodes_updated: number;
  nodes_removed: number;
  edges_added: number;
}

export interface PatternsResponse {
  status: 'ok' | 'error';
  patterns: Array<Record<string, unknown>>;
}

// ==================== Mood ====================

export interface MoodFactor {
  name: string;
  value: number;
  weight: number;
}

export interface MoodResponse {
  status: 'ok' | 'error';
  mood: {
    score: number;
    confidence: number;
    factors: MoodFactor[];
  };
  zone_id?: string;
  user_id?: string;
}

// ==================== Neurons ====================

export interface NeuronState {
  name: string;
  type: string;
  state: Record<string, unknown>;
  config?: Record<string, unknown>;
}

export interface NeuronsListResponse {
  success: boolean;
  data: {
    context: Record<string, unknown>;
    state: Record<string, unknown>;
    mood: Record<string, unknown>;
    total_count: number;
  };
}

export interface NeuronEvaluateRequest {
  states?: Record<string, unknown>;
  context?: Record<string, unknown>;
  trigger?: string;
}

export interface NeuronEvaluateResponse {
  success: boolean;
  data: {
    timestamp: string;
    context_values: Record<string, number>;
    state_values: Record<string, number>;
    mood_values: Record<string, number>;
    dominant_mood: string;
    mood_confidence: number;
    suggestions: string[];
    neuron_count: number;
  };
}

// ==================== Tags ====================

export interface Tag {
  tag_id: string;
  namespace: string;
  facet: string;
  key: string;
  description?: string;
  created_at?: string;
}

export interface TagsResponse {
  status: 'ok' | 'error';
  tags: Tag[];
}

export interface TagCreate {
  tag_id: string;
  description?: string;
}

export interface TagAssignment {
  tag_id: string;
  confidence?: number;
  source?: 'manual' | 'inferred' | 'learned';
}

export interface SubjectTagsResponse {
  status: 'ok' | 'error';
  subject_id: string;
  tags: Tag[];
}

// ==================== Events ====================

export interface EventIngest {
  type: string;
  text?: string;
  payload?: Record<string, unknown>;
  idempotency_key?: string;
  timestamp?: string;
}

export interface EventIngestResponse {
  ok: boolean;
  stored: boolean;
  deduped: boolean;
  event_id?: string;
}

// ==================== Candidates ====================

export interface Candidate {
  candidate_id: string;
  trigger: Record<string, unknown>;
  action: Record<string, unknown>;
  score: number;
  source: string;
}

export interface CandidatesResponse {
  status: 'ok' | 'error';
  candidates: Candidate[];
}

export interface CandidateStats {
  status: 'ok' | 'error';
  total: number;
  by_source: Record<string, number>;
  by_domain: Record<string, number>;
}

// ==================== Vector Store ====================

export interface VectorEntry {
  id: string;
  type: 'entity' | 'user_preference' | 'pattern';
  vector: number[];
  created_at?: string;
  updated_at?: string;
  metadata?: Record<string, unknown>;
}

export interface VectorEmbeddingRequest {
  type: 'entity' | 'user_preference' | 'pattern';
  id: string;
  domain?: string;
  area?: string;
  capabilities?: string[];
  tags?: string[];
  state?: Record<string, unknown>;
  preferences?: Record<string, unknown>;
  pattern_type?: string;
  entities?: string[];
  conditions?: Record<string, unknown>;
  confidence?: number;
  metadata?: Record<string, unknown>;
}

export interface VectorStatsResponse {
  ok: boolean;
  stats: {
    total_vectors: number;
    by_type: Record<string, number>;
    dimension: number;
  };
}

// ==================== System ====================

export interface SystemHealth {
  status: 'healthy' | 'degraded' | 'unhealthy';
  checks: {
    api: 'ok' | 'error';
    storage: 'ok' | 'error';
    ha_connection: 'ok' | 'error';
  };
  version: string;
  uptime_seconds: number;
}