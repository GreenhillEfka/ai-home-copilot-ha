/**
 * PS-108: Zone Editor API Client
 *
 * TypeScript client for HA Dashboard → Core zone-editor CRUD operations.
 * Used by styx-zone-creator-card.ts (PS-199) for zone create/update/delete
 * and by dashboard.js for inline CRUD actions.
 *
 * Endpoints (HA Dashboard proxy → Core zone-editor):
 *   POST   /api/v1/dashboard/zone-editor/zones
 *   PUT    /api/v1/dashboard/zone-editor/zones/<zone_id>
 *   DELETE /api/v1/dashboard/zone-editor/zones/<zone_id>
 *   POST   /api/v1/dashboard/zone-editor/zones/<zone_id>/rooms
 *   DELETE /api/v1/dashboard/zone-editor/zones/<zone_id>/rooms/<room_id>
 *   GET    /api/v1/dashboard/zone-editor/rooms
 *   GET    /api/v1/dashboard/zone-editor/templates
 *
 * Also supports direct Core mode (when dashboard acts as passthrough).
 */

import type { StyxZoneCreatorCardConfig } from '../cards/styx-zone-creator-card.js';

// ── Error type ────────────────────────────────────────────────────────────────

export class ZoneEditorApiError extends Error {
  constructor(
    message: string,
    public statusCode: number | undefined,
    public zoneId: string | undefined
  ) {
    super(message);
    this.name = 'ZoneEditorApiError';
  }
}

// ── URL resolution ────────────────────────────────────────────────────────────

/**
 * Resolve the zone-editor API base URL.
 * In HA dashboard context: use relative path (dashboard proxy).
 * In direct/Core context: use window.location or explicit coreBase.
 */
export function resolveZoneEditorUrl(coreBase?: string): string {
  if (coreBase) return coreBase;
  // Dashboard proxy mode (default)
  return '/api/v1/dashboard/zone-editor';
}

// ── Zone payload mappers ─────────────────────────────────────────────────────

function moduleStringToArray(modules: string): string[] {
  if (!modules) return [];
  return modules
    .split(',')
    .map((m) => m.trim().toUpperCase())
    .filter(Boolean);
}

/**
 * Map StyxZoneCreatorCardConfig (card form) → Core zone-editor create payload.
 * Used by POST /zones.
 */
export function cardConfigToCreatePayload(
  config: StyxZoneCreatorCardConfig,
  rooms: string[] = []
): Record<string, unknown> {
  return {
    name: config.zone_name,
    icon: config.zone_icon || 'mdi:home',
    active_modules: moduleStringToArray(config.active_modules),
    entities: {
      light: config.light_entity,
      audio: config.audio_entity,
      climate: config.climate_entity,
      cover: config.cover_entity,
      energy: config.energy_entity,
      scene: config.scene_entity,
      security: config.security_entity,
    },
    rooms,
    show_grid: config.show_grid ?? true,
    compact_mode: config.compact_mode ?? false,
  };
}

/**
 * Map StyxZoneCreatorCardConfig → Core zone-editor update payload.
 * Used by PUT /zones/<zone_id>.
 */
export function cardConfigToUpdatePayload(
  config: Partial<StyxZoneCreatorCardConfig>
): Record<string, unknown> {
  const payload: Record<string, unknown> = {};
  if (config.zone_name !== undefined) payload.name = config.zone_name;
  if (config.zone_icon !== undefined) payload.icon = config.zone_icon;
  if (config.active_modules !== undefined)
    payload.active_modules = moduleStringToArray(config.active_modules);
  if (config.entities !== undefined) payload.entities = config.entities;
  payload.show_grid = config.show_grid ?? true;
  payload.compact_mode = config.compact_mode ?? false;
  return payload;
}

// ── API Client ───────────────────────────────────────────────────────────────

export interface ZonePayload {
  id?: string;
  name: string;
  icon?: string;
  active_modules?: string[];
  entities?: Record<string, string | undefined>;
  rooms?: string[];
  show_grid?: boolean;
  compact_mode?: boolean;
}

export interface RoomPayload {
  id?: string;
  name: string;
  zone_id?: string;
}

const DEFAULT_TIMEOUT_MS = 8000;

export class ZoneEditorApiClient {
  constructor(private baseUrl: string = resolveZoneEditorUrl()) {}

  private async request<T>(
    method: string,
    path: string,
    body?: unknown,
    timeout = DEFAULT_TIMEOUT_MS
  ): Promise<T> {
    const url = `${this.baseUrl}${path}`;
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), timeout);

    try {
      const resp = await fetch(url, {
        method,
        headers: {
          'Content-Type': 'application/json',
          ...(window.dashboard?.authToken
            ? { Authorization: `Bearer ${window.dashboard.authToken}` }
            : {}),
        },
        body: body != null ? JSON.stringify(body) : undefined,
        signal: controller.signal,
      });

      clearTimeout(timer);

      if (resp.status >= 400) {
        let errBody: string | undefined;
        try {
          errBody = await resp.text();
        } catch {}
        const zoneId = path.split('/').pop();
        throw new ZoneEditorApiError(
          `ZoneEditor API ${method} ${path} failed (${resp.status}): ${errBody}`,
          resp.status,
          zoneId
        );
      }

      // 204 No Content
      if (resp.status === 204 || resp.headers.get('content-length') === '0') {
        return {} as T;
      }

      return (await resp.json()) as T;
    } catch (e) {
      clearTimeout(timer);
      if (e instanceof ZoneEditorApiError) throw e;
      if (e instanceof DOMException && e.name === 'AbortError') {
        throw new ZoneEditorApiError('ZoneEditor API timeout', undefined, path.split('/').pop());
      }
      throw new ZoneEditorApiError(
        `ZoneEditor API ${method} ${path} network error: ${String(e)}`,
        undefined,
        path.split('/').pop()
      );
    }
  }

  // Zone CRUD
  async listZones(): Promise<{ zones: ZonePayload[] }> {
    return this.request<{ zones: ZonePayload[] }>('GET', '/zones');
  }

  async getZone(zoneId: string): Promise<ZonePayload> {
    return this.request<ZonePayload>('GET', `/zones/${zoneId}`);
  }

  async createZone(payload: ZonePayload): Promise<ZonePayload> {
    return this.request<ZonePayload>('POST', '/zones', payload);
  }

  async updateZone(zoneId: string, payload: Partial<ZonePayload>): Promise<ZonePayload> {
    return this.request<ZonePayload>('PUT', `/zones/${zoneId}`, payload);
  }

  async deleteZone(zoneId: string): Promise<void> {
    await this.request<void>('DELETE', `/zones/${zoneId}`);
  }

  // Room management
  async listRooms(): Promise<{ rooms: RoomPayload[] }> {
    return this.request<{ rooms: RoomPayload[] }>('GET', '/rooms');
  }

  async addRoomToZone(zoneId: string, room: RoomPayload): Promise<RoomPayload> {
    return this.request<RoomPayload>('POST', `/zones/${zoneId}/rooms`, room);
  }

  async removeRoomFromZone(zoneId: string, roomId: string): Promise<void> {
    await this.request<void>('DELETE', `/zones/${zoneId}/rooms/${roomId}`);
  }

  // Templates
  async listTemplates(): Promise<unknown> {
    return this.request<unknown>('GET', '/templates');
  }
}

// ── Singleton export ─────────────────────────────────────────────────────────

export const zoneEditorApi = new ZoneEditorApiClient();
