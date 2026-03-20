/**
 * PS-108: Zone Editor API Client
 *
 * TypeScript client for the /api/v1/zone-editor CRUD endpoints.
 * Uses card-form-helper.ts (PS-198) HaFormSchema pattern for type safety.
 *
 * Endpoints (Core zone-editor API):
 *   GET    /api/v1/zone-editor/zones           → list all zones
 *   GET    /api/v1/zone-editor/zones/<zone_id> → get single zone
 *   POST   /api/v1/zone-editor/zones           → create zone
 *   PUT    /api/v1/zone-editor/zones/<zone_id> → update zone
 *   DELETE /api/v1/zone-editor/zones/<zone_id> → delete zone
 *   GET    /api/v1/zone-editor/rooms           → list rooms
 *   GET    /api/v1/zone-editor/templates       → list templates
 *
 * The HA dashboard proxies these via its own /api/v1/dashboard/* endpoints
 * so the frontend always talks to the same origin.  Pass resolveUrl() as
 * baseUrl when running inside the HA dashboard context, otherwise use the
 * Core base URL directly.
 */

import type { HaFormSchema } from './card-form-helper.js';

// ─── Types ───────────────────────────────────────────────────────────────────

export interface ZoneEditorZone {
  zone_id: string;
  name: string;
  icon: string;
  color?: string;
  enabled?: boolean;
  priority?: number;
  mode?: string;
  rooms?: string[];
  entities?: Record<string, unknown>;
}

export interface ZoneEditorRoom {
  room_id: string;
  name: string;
  zone?: string | null;
  entities?: string[];
}

export interface ZoneEditorTemplate {
  id: string;
  name: string;
  description?: string;
  icon?: string;
  modules?: string[];
}

export interface CreateZonePayload {
  zone_id: string;
  name: string;
  icon?: string;
  color?: string;
  priority?: number;
  rooms?: string[];
  enabled?: boolean;
  mode?: string;
  entities?: Record<string, unknown>;
}

export interface UpdateZonePayload {
  name?: string;
  icon?: string;
  color?: string;
  enabled?: boolean;
  priority?: number;
  mode?: string;
  rooms?: string[];
  entities?: Record<string, unknown>;
}

export interface ApiResponse<T = unknown> {
  ok: boolean;
  error?: string;
  zone?: T;
  zones?: T[];
  rooms?: ZoneEditorRoom[];
  templates?: ZoneEditorTemplate[];
  total?: number;
}

// ─── URL Resolution ───────────────────────────────────────────────────────────

/**
 * Resolve an API URL.  When running inside the HA dashboard, all requests
 * go to the same origin; otherwise fall back to the Core base URL.
 */
export function resolveZoneEditorUrl(
  path: string,
  baseUrl?: string,
): string {
  if (baseUrl) return `${baseUrl}${path}`;

  // Detect if we are inside the HA dashboard (Flask server on same host)
  const dashboardBase = (window as Window & { PILOTSUITE_DASHBOARD_BASE?: string })
    .PILOTSUITE_DASHBOARD_BASE;

  if (dashboardBase) return `${dashboardBase}${path}`;

  // Inside HA dashboard: same origin + /api/v1/dashboard prefix for proxy
  // We always proxy through the HA dashboard, never call Core directly
  return `/api/v1/dashboard${path.replace('/api/v1/zone-editor', '')}`;
}

// ─── Fetch Helper ─────────────────────────────────────────────────────────────

interface FetchOptions extends RequestInit {
  timeoutMs?: number;
}

async function apiFetch<T>(
  url: string,
  options: FetchOptions = {},
): Promise<T> {
  const { timeoutMs = 8000, ...fetchOpts } = options;

  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);

  try {
    const resp = await fetch(url, {
      ...fetchOpts,
      signal: controller.signal,
      headers: {
        'Content-Type': 'application/json',
        ...(fetchOpts.headers as Record<string, string>),
      },
    });

    if (!resp.ok) {
      let errorBody: string | unknown = resp.statusText;
      try {
        const json = await resp.json();
        errorBody = json.error || json;
      } catch {
        // ignore parse error
      }
      throw new ZoneEditorApiError(
        `HTTP ${resp.status}: ${resp.statusText}`,
        resp.status,
        errorBody,
      );
    }

    return (await resp.json()) as T;
  } finally {
    clearTimeout(timer);
  }
}

// ─── Custom Error ─────────────────────────────────────────────────────────────

export class ZoneEditorApiError extends Error {
  constructor(
    message: string,
    public readonly statusCode: number,
    public readonly body?: unknown,
  ) {
    super(message);
    this.name = 'ZoneEditorApiError';
  }
}

// ─── API Client ───────────────────────────────────────────────────────────────

export class ZoneEditorApiClient {
  constructor(private baseUrl?: string) {}

  // ── List ──────────────────────────────────────────────────────────────────

  /**
   * List all zones from the zone-editor store.
   */
  async listZones(): Promise<ApiResponse<ZoneEditorZone>> {
    const url = resolveZoneEditorUrl('/api/v1/zone-editor/zones', this.baseUrl);
    return apiFetch<ApiResponse<ZoneEditorZone>>(url);
  }

  /**
   * Get a single zone by ID.
   */
  async getZone(zoneId: string): Promise<ApiResponse<ZoneEditorZone>> {
    const url = resolveZoneEditorUrl(
      `/api/v1/zone-editor/zones/${encodeURIComponent(zoneId)}`,
      this.baseUrl,
    );
    return apiFetch<ApiResponse<ZoneEditorZone>>(url);
  }

  // ── Create ────────────────────────────────────────────────────────────────

  /**
   * Create a new zone.
   *
   * Payload shape is derived from the StyxZoneCreatorCardConfig fields
   * that are persisted to Core (zone_name, zone_icon, active_modules, etc.).
   */
  async createZone(payload: CreateZonePayload): Promise<ApiResponse<ZoneEditorZone>> {
    const url = resolveZoneEditorUrl('/api/v1/zone-editor/zones', this.baseUrl);
    return apiFetch<ApiResponse<ZoneEditorZone>>(url, {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  }

  // ── Update ───────────────────────────────────────────────────────────────

  /**
   * Update an existing zone (partial update — only send changed fields).
   */
  async updateZone(
    zoneId: string,
    payload: UpdateZonePayload,
  ): Promise<ApiResponse<ZoneEditorZone>> {
    const url = resolveZoneEditorUrl(
      `/api/v1/zone-editor/zones/${encodeURIComponent(zoneId)}`,
      this.baseUrl,
    );
    return apiFetch<ApiResponse<ZoneEditorZone>>(url, {
      method: 'PUT',
      body: JSON.stringify(payload),
    });
  }

  // ── Delete ───────────────────────────────────────────────────────────────

  /**
   * Delete a zone by ID.
   */
  async deleteZone(zoneId: string): Promise<ApiResponse> {
    const url = resolveZoneEditorUrl(
      `/api/v1/zone-editor/zones/${encodeURIComponent(zoneId)}`,
      this.baseUrl,
    );
    return apiFetch<ApiResponse>(url, {
      method: 'DELETE',
    });
  }

  // ── Rooms ───────────────────────────────────────────────────────────────

  /**
   * List all rooms (optionally filtered to unassigned only).
   */
  async listRooms(unassignedOnly = false): Promise<ApiResponse<ZoneEditorRoom>> {
    const url = resolveZoneEditorUrl(
      `/api/v1/zone-editor/rooms${unassignedOnly ? '?unassigned=true' : ''}`,
      this.baseUrl,
    );
    return apiFetch<ApiResponse<ZoneEditorRoom>>(url);
  }

  // ── Templates ────────────────────────────────────────────────────────────

  /**
   * List available zone templates.
   */
  async listTemplates(): Promise<ApiResponse<ZoneEditorTemplate>> {
    const url = resolveZoneEditorUrl('/api/v1/zone-editor/templates', this.baseUrl);
    return apiFetch<ApiResponse<ZoneEditorTemplate>>(url);
  }
}

// ─── Singleton (resolves URL per execution context) ───────────────────────────

export const zoneEditorApi = new ZoneEditorApiClient();

// ─── StyxZoneCreatorCard CRUD helpers ────────────────────────────────────────
// These functions bridge the card config schema (PS-199) to the API client.
// Card authors should import zoneEditorApi directly; these are for
// StyxZoneCreatorCard internal use only.

/**
 * Map a StyxZoneCreatorCardConfig to the CreateZonePayload expected by
 * /api/v1/zone-editor/zones (POST).
 */
export function cardConfigToCreatePayload(
  config: Record<string, unknown>,
): CreateZonePayload {
  return {
    zone_id: String(config.zone_name ?? '')
      .toLowerCase()
      .replace(/\s+/g, '_')
      .replace(/[^a-z0-9_]/g, ''),
    name: String(config.zone_name ?? ''),
    icon: String(config.zone_icon ?? 'mdi:room'),
    enabled: true,
    priority: 10,
    rooms: [],
    entities: {},
  };
}

/**
 * Map a StyxZoneCreatorCardConfig to the UpdateZonePayload expected by
 * /api/v1/zone-editor/zones/<zone_id> (PUT).
 */
export function cardConfigToUpdatePayload(
  zoneId: string,
  config: Record<string, unknown>,
): UpdateZonePayload {
  const payload: UpdateZonePayload = {
    name: String(config.zone_name ?? ''),
    icon: String(config.zone_icon ?? 'mdi:room'),
  };

  if (typeof config.active_modules === 'string') {
    const modules = config.active_modules
      .split(',')
      .map((s) => s.trim())
      .filter(Boolean);
    // Store active modules in entities for module activation
    payload.entities = { active_modules: modules };
  } else if (Array.isArray(config.active_modules)) {
    payload.entities = { active_modules: config.active_modules };
  }

  return payload;
}
