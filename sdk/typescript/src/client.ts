import axios, { AxiosInstance, AxiosRequestConfig } from 'axios';
import {
  HabitusStatus,
  RulesResponse,
  MineRequest,
  MineResponse,
  ZonesResponse,
  DashboardCardsResponse,
  GraphState,
  GraphSyncRequest,
  GraphSyncResponse,
  PatternsResponse,
  MoodResponse,
  NeuronsListResponse,
  NeuronEvaluateRequest,
  NeuronEvaluateResponse,
  TagsResponse,
  TagCreate,
  Tag,
  SubjectTagsResponse,
  TagAssignment,
  EventIngest,
  EventIngestResponse,
  CandidatesResponse,
  CandidateStats,
  VectorEmbeddingRequest,
  VectorStatsResponse,
  VectorEntry,
  SystemHealth,
  ErrorResponse,
} from './types';

export interface CopilotClientConfig {
  baseUrl: string;
  authToken?: string;
  timeout?: number;
  headers?: Record<string, string>;
}

export class CopilotClient {
  private client: AxiosInstance;

  constructor(config: CopilotClientConfig) {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...config.headers,
    };

    if (config.authToken) {
      headers['X-Auth-Token'] = config.authToken;
    }

    this.client = axios.create({
      baseURL: config.baseUrl,
      timeout: config.timeout || 30000,
      headers,
    });
  }

  // ==================== Habitus API ====================

  habitus = {
    getStatus: async (): Promise<HabitusStatus> => {
      const response = await this.client.get('/api/v1/habitus/status');
      return response.data;
    },

    getRules: async (params?: {
      limit?: number;
      min_score?: number;
      a_filter?: string;
      b_filter?: string;
      domain_filter?: string;
    }): Promise<RulesResponse> => {
      const response = await this.client.get('/api/v1/habitus/rules', { params });
      return response.data;
    },

    mineRules: async (request: MineRequest): Promise<MineResponse> => {
      const response = await this.client.post('/api/v1/habitus/mine', request);
      return response.data;
    },

    getConfig: async (): Promise<Record<string, unknown>> => {
      const response = await this.client.get('/api/v1/habitus/config');
      return response.data;
    },

    updateConfig: async (config: Partial<Record<string, unknown>>): Promise<{ status: string }> => {
      const response = await this.client.post('/api/v1/habitus/config', config);
      return response.data;
    },

    reset: async (): Promise<{ status: string }> => {
      const response = await this.client.post('/api/v1/habitus/reset');
      return response.data;
    },

    getZones: async (): Promise<ZonesResponse> => {
      const response = await this.client.get('/api/v1/habitus/dashboard_cards/zones');
      return response.data;
    },

    getDashboardCards: async (): Promise<DashboardCardsResponse> => {
      const response = await this.client.get('/api/v1/habitus/dashboard_cards');
      return response.data;
    },
  };

  // ==================== Graph API ====================

  graph = {
    getState: async (params?: { max_nodes?: number; max_edges?: number }): Promise<GraphState> => {
      const response = await this.client.get('/api/v1/graph/state', { params });
      return response.data;
    },

    sync: async (request: GraphSyncRequest): Promise<GraphSyncResponse> => {
      const response = await this.client.post('/api/v1/graph/sync', request);
      return response.data;
    },

    getPatterns: async (): Promise<PatternsResponse> => {
      const response = await this.client.get('/api/v1/graph/patterns');
      return response.data;
    },

    getStats: async (): Promise<Record<string, unknown>> => {
      const response = await this.client.get('/api/v1/graph/stats');
      return response.data;
    },
  };

  // ==================== Neurons API ====================

  neurons = {
    list: async (): Promise<NeuronsListResponse> => {
      const response = await this.client.get('/api/v1/neurons');
      return response.data;
    },

    get: async (neuronId: string): Promise<{ success: boolean; data: Record<string, unknown> }> => {
      const response = await this.client.get(`/api/v1/neurons/${neuronId}`);
      return response.data;
    },

    evaluate: async (request?: NeuronEvaluateRequest): Promise<NeuronEvaluateResponse> => {
      const response = await this.client.post('/api/v1/neurons/evaluate', request || {});
      return response.data;
    },

    updateStates: async (states: Record<string, unknown>): Promise<{ success: boolean }> => {
      const response = await this.client.post('/api/v1/neurons/update', { states });
      return response.data;
    },

    getMood: async (params?: { zone_id?: string; user_id?: string }): Promise<MoodResponse> => {
      const response = await this.client.get('/api/v1/neurons/mood', { params });
      return response.data;
    },

    evaluateMood: async (request?: NeuronEvaluateRequest): Promise<NeuronEvaluateResponse> => {
      const response = await this.client.post('/api/v1/neurons/mood/evaluate', request || {});
      return response.data;
    },

    getMoodHistory: async (params?: { limit?: number }): Promise<{ success: boolean; data: { history: unknown[]; count: number } }> => {
      const response = await this.client.get('/api/v1/neurons/mood/history', { params });
      return response.data;
    },

    getSuggestions: async (): Promise<{ success: boolean; data: { suggestions: string[]; mood: string; timestamp: string } }> => {
      const response = await this.client.get('/api/v1/neurons/suggestions');
      return response.data;
    },
  };

  // ==================== Tags API ====================

  tags = {
    list: async (): Promise<TagsResponse> => {
      const response = await this.client.get('/api/v1/tags2/tags');
      return response.data;
    },

    create: async (tag: TagCreate): Promise<Tag> => {
      const response = await this.client.post('/api/v1/tags2/tags', tag);
      return response.data;
    },

    get: async (tagId: string): Promise<Tag> => {
      const response = await this.client.get(`/api/v1/tags2/tags/${tagId}`);
      return response.data;
    },

    getSubjectTags: async (subjectId: string): Promise<SubjectTagsResponse> => {
      const response = await this.client.get(`/api/v1/tags2/subjects/${subjectId}/tags`);
      return response.data;
    },

    assignTag: async (subjectId: string, assignment: TagAssignment): Promise<{ status: string }> => {
      const response = await this.client.post(`/api/v1/tags2/subjects/${subjectId}/tags`, assignment);
      return response.data;
    },

    getAssignments: async (): Promise<{ status: string; assignments: unknown[] }> => {
      const response = await this.client.get('/api/v1/tags2/assignments');
      return response.data;
    },

    createAssignment: async (assignment: { subject_id: string } & TagAssignment): Promise<{ status: string }> => {
      const response = await this.client.post('/api/v1/tags2/assignments', assignment);
      return response.data;
    },
  };

  // ==================== Events API ====================

  events = {
    ingest: async (event: EventIngest, idempotencyKey?: string): Promise<EventIngestResponse> => {
      const headers: Record<string, string> = {};
      if (idempotencyKey) {
        headers['Idempotency-Key'] = idempotencyKey;
      }
      const response = await this.client.post('/api/v1/events', event, { headers });
      return response.data;
    },

    list: async (params?: { limit?: number; type?: string }): Promise<{ status: string; events: unknown[] }> => {
      const response = await this.client.get('/api/v1/events', { params });
      return response.data;
    },

    getStats: async (): Promise<{ status: string; stats: Record<string, unknown> }> => {
      const response = await this.client.get('/api/v1/events/stats');
      return response.data;
    },
  };

  // ==================== Candidates API ====================

  candidates = {
    list: async (params?: { min_score?: number; limit?: number }): Promise<CandidatesResponse> => {
      const response = await this.client.get('/api/v1/candidates', { params });
      return response.data;
    },

    get: async (candidateId: string): Promise<{ status: string; candidate: unknown }> => {
      const response = await this.client.get(`/api/v1/candidates/${candidateId}`);
      return response.data;
    },

    delete: async (candidateId: string): Promise<{ status: string }> => {
      const response = await this.client.delete(`/api/v1/candidates/${candidateId}`);
      return response.data;
    },

    getStats: async (): Promise<CandidateStats> => {
      const response = await this.client.get('/api/v1/candidates/stats');
      return response.data;
    },

    getGraphCandidates: async (): Promise<{ status: string; candidates: unknown[] }> => {
      const response = await this.client.get('/api/v1/candidates/graph_candidates');
      return response.data;
    },
  };

  // ==================== Vector API ====================

  vector = {
    createEmbedding: async (request: VectorEmbeddingRequest): Promise<{ ok: boolean; entry: Partial<VectorEntry> }> => {
      const response = await this.client.post('/api/v1/vector/embeddings', request);
      return response.data;
    },

    createEmbeddingsBulk: async (request: {
      entities?: VectorEmbeddingRequest[];
      user_preferences?: VectorEmbeddingRequest[];
      patterns?: VectorEmbeddingRequest[];
    }): Promise<{ ok: boolean; results: Record<string, { created: number; failed: number }> }> => {
      const response = await this.client.post('/api/v1/vector/embeddings/bulk', request);
      return response.data;
    },

    findSimilar: async (entryId: string, params?: { type?: string; limit?: number; threshold?: number }): Promise<{
      ok: boolean;
      query_id: string;
      query_type: string;
      results: Array<{ id: string; similarity: number; type: string; metadata?: Record<string, unknown> }>;
      count: number;
    }> => {
      const response = await this.client.get(`/api/v1/vector/similar/${entryId}`, { params });
      return response.data;
    },

    list: async (params?: { type?: string; limit?: number }): Promise<{ ok: boolean; entries: Partial<VectorEntry>[]; count: number }> => {
      const response = await this.client.get('/api/v1/vector/vectors', { params });
      return response.data;
    },

    get: async (entryId: string): Promise<{ ok: boolean; entry: VectorEntry }> => {
      const response = await this.client.get(`/api/v1/vector/vectors/${entryId}`);
      return response.data;
    },

    delete: async (entryId: string): Promise<{ ok: boolean; deleted: string }> => {
      const response = await this.client.delete(`/api/v1/vector/vectors/${entryId}`);
      return response.data;
    },

    clear: async (params?: { type?: string }): Promise<{ ok: boolean; deleted_count: number; type: string }> => {
      const response = await this.client.delete('/api/v1/vector/vectors', { params });
      return response.data;
    },

    getStats: async (): Promise<VectorStatsResponse> => {
      const response = await this.client.get('/api/v1/vector/stats');
      return response.data;
    },

    computeSimilarity: async (request: { id1?: string; id2?: string; vector1?: number[]; vector2?: number[] }): Promise<{
      ok: boolean;
      similarity: number;
      dimension: number;
    }> => {
      const response = await this.client.post('/api/v1/vector/similarity', request);
      return response.data;
    },
  };

  // ==================== Weather API ====================

  weather = {
    get: async (): Promise<{ status: string; weather: Record<string, unknown> }> => {
      const response = await this.client.get('/api/v1/weather/');
      return response.data;
    },

    getForecast: async (params?: { days?: number }): Promise<{ status: string; forecast: unknown[] }> => {
      const response = await this.client.get('/api/v1/weather/forecast', { params });
      return response.data;
    },

    getPvRecommendations: async (): Promise<{ status: string; recommendations: unknown[] }> => {
      const response = await this.client.get('/api/v1/weather/pv-recommendations');
      return response.data;
    },
  };

  // ==================== Voice Context API ====================

  voiceContext = {
    get: async (): Promise<{ status: string; context: Record<string, unknown> }> => {
      const response = await this.client.get('/api/v1/voice/context');
      return response.data;
    },

    update: async (context: Record<string, unknown>): Promise<{ status: string }> => {
      const response = await this.client.post('/api/v1/voice/context', context);
      return response.data;
    },

    getPrompt: async (): Promise<{ status: string; prompt: string }> => {
      const response = await this.client.get('/api/v1/voice/prompt');
      return response.data;
    },

    getMoodHistory: async (): Promise<{ status: string; history: unknown[] }> => {
      const response = await this.client.get('/api/v1/voice/mood_history');
      return response.data;
    },

    getSuggestions: async (): Promise<{ status: string; suggestions: unknown[] }> => {
      const response = await this.client.get('/api/v1/voice/suggestions');
      return response.data;
    },
  };

  // ==================== Debug API ====================

  debug = {
    get: async (): Promise<{ status: string; debug: Record<string, unknown> }> => {
      const response = await this.client.get('/api/v1/debug');
      return response.data;
    },

    post: async (data: Record<string, unknown>): Promise<{ status: string }> => {
      const response = await this.client.post('/api/v1/debug', data);
      return response.data;
    },
  };

  // ==================== System Health ====================

  system = {
    health: async (): Promise<SystemHealth> => {
      const response = await this.client.get('/health');
      return response.data;
    },

    version: async (): Promise<{ version: string }> => {
      const response = await this.client.get('/version');
      return response.data;
    },
  };

  // ==================== Generic Request Methods ====================

  async get<T = unknown>(path: string, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.client.get(path, config);
    return response.data;
  }

  async post<T = unknown>(path: string, data?: unknown, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.client.post(path, data, config);
    return response.data;
  }

  async put<T = unknown>(path: string, data?: unknown, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.client.put(path, data, config);
    return response.data;
  }

  async delete<T = unknown>(path: string, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.client.delete(path, config);
    return response.data;
  }
}

export default CopilotClient;