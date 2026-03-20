/**
 * PS-199: Styx Zone Creator Card
 *
 * Card for creating and configuring zones in PilotSuite with modular support for:
 * - Licht (Light)
 * - Musik (Music)
 * - Klima (Climate)
 * - Cover (Shutter/Blind)
 * - Energie (Energy)
 * - Szene (Scene)
 * - Sicherheit (Security)
 *
 * Implements HA-PR #16142 (2025-02) `static async getConfigForm()` pattern.
 * Uses card-form-helper.ts (PS-198) for HaFormSchema generation with:
 * - entity-selector per module
 * - grid-layout for form structure
 * - context-filter for field coupling
 *
 * Core logic (zone CRUD, module activation) lives in the Styx backend — NOT here.
 */

import {
  buildHaFormSchema,
  HaFormSchema,
  HaFormFieldDescriptor,
} from '../utils/card-form-helper.js';
import {
  buildConfigValidator,
  ConfigValidationError,
} from '../utils/editor-schema-validation.js';
import { registerCustomCard } from '../utils/card-registration.js';
import {
  zoneEditorApi,
  ZoneEditorApiError,
  ZoneEditorZone,
} from '../utils/zone-editor-api-client.js';

/**
 * Zone module types — each maps to a set of entity selectors.
 */
export type ZoneCreatorModuleType =
  | 'LIGHT'
  | 'AUDIO'
  | 'CLIMATE'
  | 'COVER'
  | 'ENERGY'
  | 'SCENE'
  | 'SECURITY';

export const ZONE_CREATOR_MODULE_TYPES: readonly ZoneCreatorModuleType[] = [
  'LIGHT',
  'AUDIO',
  'CLIMATE',
  'COVER',
  'ENERGY',
  'SCENE',
  'SECURITY',
] as const;

export interface StyxZoneCreatorCardConfig {
  // Zone identity
  zone_name: string;
  zone_icon: string;

  // Which modules are active for this zone (comma-separated string, e.g. "LIGHT,CLIMATE")
  active_modules: string;

  // Module entity selections
  light_entity?: string;
  audio_entity?: string;
  climate_entity?: string;
  cover_entity?: string;
  energy_entity?: string;
  scene_entity?: string;
  security_entity?: string;

  // Context filters — entity drives which attributes are relevant
  light_filter_entity?: string;
  climate_filter_entity?: string;
  cover_filter_entity?: string;

  // Display options
  show_grid: boolean;
  compact_mode: boolean;
}

// ---------------------------------------------------------------------------
// Field descriptor groups per module
// ---------------------------------------------------------------------------

const ZONE_IDENTITY_FIELDS: HaFormFieldDescriptor[] = [
  {
    name: 'zone_name',
    type: 'text',
    title: 'Zonen-Name',
    description: 'Name der Zone',
    required: true,
  },
  {
    name: 'zone_icon',
    type: 'icon',
    title: 'Zonen-Icon',
    description: 'Icon für die Zone',
    required: false,
    defaultValue: 'mdi:room',
  },
];

const ACTIVE_MODULES_FIELD: HaFormFieldDescriptor = {
  name: 'active_modules',
  type: 'text',
  title: 'Aktive Module',
  description: `Aktivierte Module (kommasepariert): ${ZONE_CREATOR_MODULE_TYPES.join(', ')}`,
  required: false,
  defaultValue: 'LIGHT',
};

const DISPLAY_FIELDS: HaFormFieldDescriptor[] = [
  {
    name: 'show_grid',
    type: 'boolean',
    title: 'Grid anzeigen',
    description: 'Zeige Grid-Layout für Module',
    required: false,
    defaultValue: true,
  },
  {
    name: 'compact_mode',
    type: 'boolean',
    title: 'Kompakt-Modus',
    description: 'Reduzierte Darstellung',
    required: false,
    defaultValue: false,
  },
];

const LIGHT_FIELDS: HaFormFieldDescriptor[] = [
  {
    name: 'light_entity',
    type: 'entity',
    title: 'Licht-Entity',
    description: 'Licht-Entity für diese Zone',
    required: false,
    domain: ['light'],
  },
  {
    name: 'light_filter_entity',
    type: 'entity',
    title: 'Licht-Filter',
    description: 'Entity deren Status die Licht-Auswahl beeinflusst',
    required: false,
    domain: ['input_boolean', 'binary_sensor'],
    context: { filter_entity: 'light_entity' },
  },
];

const AUDIO_FIELDS: HaFormFieldDescriptor[] = [
  {
    name: 'audio_entity',
    type: 'entity',
    title: 'Audio-Entity',
    description: 'Media Player für Musik-Wiedergabe',
    required: false,
    domain: ['media_player'],
    deviceClass: ['speaker'],
  },
];

const CLIMATE_FIELDS: HaFormFieldDescriptor[] = [
  {
    name: 'climate_entity',
    type: 'entity',
    title: 'Klima-Entity',
    description: 'Thermostat / Klima-Entity für diese Zone',
    required: false,
    domain: ['climate'],
  },
  {
    name: 'climate_filter_entity',
    type: 'entity',
    title: 'Klima-Filter',
    description: 'Entity deren Status die Klima-Auswahl beeinflusst',
    required: false,
    domain: ['input_boolean', 'binary_sensor', 'sensor'],
    context: { filter_entity: 'climate_entity' },
  },
];

const COVER_FIELDS: HaFormFieldDescriptor[] = [
  {
    name: 'cover_entity',
    type: 'entity',
    title: 'Cover-Entity',
    description: 'Rollläden / Markisen für diese Zone',
    required: false,
    domain: ['cover'],
  },
  {
    name: 'cover_filter_entity',
    type: 'entity',
    title: 'Cover-Filter',
    description: 'Entity deren Status die Cover-Auswahl beeinflusst',
    required: false,
    domain: ['input_boolean', 'binary_sensor'],
    context: { filter_entity: 'cover_entity' },
  },
];

const ENERGY_FIELDS: HaFormFieldDescriptor[] = [
  {
    name: 'energy_entity',
    type: 'entity',
    title: 'Energie-Entity',
    description: 'Energie- / Stromsensor für diese Zone',
    required: false,
    domain: ['sensor'],
    deviceClass: ['power', 'energy'],
  },
];

const SCENE_FIELDS: HaFormFieldDescriptor[] = [
  {
    name: 'scene_entity',
    type: 'entity',
    title: 'Szenen-Entity',
    description: 'Szene-Entity für diese Zone',
    required: false,
    domain: ['scene'],
  },
];

const SECURITY_FIELDS: HaFormFieldDescriptor[] = [
  {
    name: 'security_entity',
    type: 'entity',
    title: 'Sicherheits-Entity',
    description: 'Alarm / Sensor-Entity (Tür, Bewegung, Smoke)',
    required: false,
    domain: ['alarm_control_panel', 'binary_sensor', 'sensor'],
    deviceClass: ['motion', 'opening', 'smoke', 'gas'],
  },
];

// ---------------------------------------------------------------------------
// Schema — built once at module level (HA-PR #16142 pattern)
// ---------------------------------------------------------------------------

const MODULE_FIELDS: Record<ZoneCreatorModuleType, HaFormFieldDescriptor[]> = {
  LIGHT: LIGHT_FIELDS,
  AUDIO: AUDIO_FIELDS,
  CLIMATE: CLIMATE_FIELDS,
  COVER: COVER_FIELDS,
  ENERGY: ENERGY_FIELDS,
  SCENE: SCENE_FIELDS,
  SECURITY: SECURITY_FIELDS,
};

const ALL_MODULE_FIELDS = [...ZONE_CREATOR_MODULE_TYPES].flatMap(
  (mt) => MODULE_FIELDS[mt],
);

const ZONE_CREATOR_SCHEMA: HaFormSchema[] = buildHaFormSchema(
  [...ZONE_IDENTITY_FIELDS, ACTIVE_MODULES_FIELD, ...ALL_MODULE_FIELDS, ...DISPLAY_FIELDS],
  {
    gridName: 'zone-creator',
    gridTitle: 'Zone Creator',
    gridDescription: 'Konfiguriere eine Zone mit bis zu 7 modularen Komponenten',
    flatten: true,
  },
);

// ---------------------------------------------------------------------------
// Validation
// ---------------------------------------------------------------------------

const VALID_MODULE_TYPE_SET = new Set<string>(ZONE_CREATOR_MODULE_TYPES);

function parseAndValidateActiveModules(
  raw: unknown,
): ZoneCreatorModuleType[] {
  if (typeof raw === 'string') {
    return raw
      .split(',')
      .map((s) => s.trim().toUpperCase() as ZoneCreatorModuleType)
      .filter((s) => VALID_MODULE_TYPE_SET.has(s));
  }
  if (Array.isArray(raw)) {
    const modules: ZoneCreatorModuleType[] = [];
    for (const item of raw) {
      if (typeof item !== 'string' || !VALID_MODULE_TYPE_SET.has(item)) {
        throw new ConfigValidationError(
          `Ungültiger Modultyp '${item}'. Erlaubt: ${ZONE_CREATOR_MODULE_TYPES.join(', ')}`,
          'active_modules',
          'ZoneCreatorModuleType',
          typeof item,
        );
      }
      modules.push(item as ZoneCreatorModuleType);
    }
    return modules;
  }
  throw new ConfigValidationError(
    'active_modules muss ein String (kommasepariert) oder Array sein',
    'active_modules',
    'string | ZoneCreatorModuleType[]',
    typeof raw,
  );
}

const validateZoneCreatorConfig: (
  config: unknown,
) => asserts config is StyxZoneCreatorCardConfig =
  buildConfigValidator<StyxZoneCreatorCardConfig>(ZONE_CREATOR_SCHEMA);

// ---------------------------------------------------------------------------
// Card class — HA-PR #16142 static async getConfigForm() pattern
// ---------------------------------------------------------------------------

export class StyxZoneCreatorCard extends HTMLElement {
  private _zoneId?: string;
  private _config?: StyxZoneCreatorCardConfig;
  private _saveBtn?: HTMLButtonElement;
  private _deleteBtn?: HTMLButtonElement;
  private _statusEl?: HTMLElement;

  static get type(): string {
    return 'styx-zone-creator';
  }

  static get documentationURL(): string {
    return 'https://pilotsuite.io/docs/cards/zone-creator';
  }

  /**
   * HA-PR #16142 (2025-02): Returns the card config form schema.
   * Pure schema — no core logic, no state, no API calls.
   */
  static async getConfigForm(): Promise<HaFormSchema[]> {
    return ZONE_CREATOR_SCHEMA;
  }

  static getStubConfig(): Partial<StyxZoneCreatorCardConfig> {
    return {
      zone_name: 'Neue Zone',
      zone_icon: 'mdi:room',
      active_modules: 'LIGHT',
      show_grid: true,
      compact_mode: false,
    };
  }

  /**
   * Validate a config object against the card schema and module enum.
   * Core zone logic (CRUD, activation, routing) lives in Styx backend — NOT here.
   */
  static validateConfig(config: unknown): void {
    validateZoneCreatorConfig(config as Record<string, unknown>);
    const cfg = config as StyxZoneCreatorCardConfig;
    // Throws ConfigValidationError on invalid module types
    parseAndValidateActiveModules(cfg?.active_modules);
  }

  setConfig(config: Record<string, unknown>): void {
    this._config = config as StyxZoneCreatorCardConfig;
    this._zoneId =
      (config.zone_name as string)
        ?.toLowerCase()
        .replace(/\s+/g, '_')
        .replace(/[^a-z0-9_]/g, '') ?? undefined;
    this._render();
  }

  connectedCallback(): void {
    this._render();
  }

  private _render(): void {
    if (!this.shadowRoot) {
      this.attachShadow({ mode: 'open' });
    }
    const cfg = this._config ?? ({} as StyxZoneCreatorCardConfig);
    const MODULES = ZONE_CREATOR_MODULE_TYPES.join(', ');

    this.shadowRoot!.innerHTML = `
      <style>
        :host { display: block; font-family: system-ui, sans-serif; }
        .card { background: #fff; border-radius: 12px; padding: 16px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }
        .header { display: flex; align-items: center; gap: 8px; margin-bottom: 16px; }
        .header i { font-size: 24px; color: #1976d2; }
        h3 { margin: 0; font-size: 16px; color: #222; }
        .field { margin-bottom: 12px; }
        label { display: block; font-size: 12px; color: #666; margin-bottom: 4px; }
        input[type="text"] { width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 6px; box-sizing: border-box; }
        .module-grid { display: flex; flex-wrap: wrap; gap: 6px; }
        .module-grid label { display: flex; align-items: center; gap: 4px; cursor: pointer; font-size: 12px; color: #333; }
        .actions { display: flex; gap: 8px; margin-top: 16px; }
        button { padding: 8px 16px; border: none; border-radius: 6px; cursor: pointer; font-size: 13px; }
        button:disabled { opacity: 0.6; cursor: not-allowed; }
        .btn-save { background: #1976d2; color: #fff; }
        .btn-save:hover:not(:disabled) { background: #1565c0; }
        .btn-delete { background: #d32f2f; color: #fff; }
        .btn-delete:hover:not(:disabled) { background: #b71c1c; }
        .btn-delete { display: ${this._zoneId ? 'inline-block' : 'none'}; }
        .status { font-size: 12px; margin-top: 8px; min-height: 16px; }
        .status.error { color: #d32f2f; }
        .status.success { color: #388e3c; }
      </style>
      <div class="card">
        <div class="header">
          <i class="mdi ${cfg.zone_icon ?? 'mdi:room'}"></i>
          <h3>${cfg.zone_name ?? 'Neue Zone'}</h3>
        </div>
        <div class="field">
          <label>Zonen-Name</label>
          <input type="text" id="zc-name" value="${cfg.zone_name ?? ''}" placeholder="z.B. Wohnzimmer">
        </div>
        <div class="field">
          <label>Icon (MDI)</label>
          <input type="text" id="zc-icon" value="${cfg.zone_icon ?? 'mdi:room'}" placeholder="mdi:room">
        </div>
        <div class="field">
          <label>Aktive Module</label>
          <div class="module-grid">
            ${ZONE_CREATOR_MODULE_TYPES.map(m => {
              const active = (cfg.active_modules ?? 'LIGHT')
                .split(',')
                .map((s: string) => s.trim().toUpperCase())
                .includes(m);
              return `<label><input type="checkbox" class="zc-module" value="${m}" ${active ? 'checked' : ''}> ${m}</label>`;
            }).join('')}
          </div>
          <small style="color:#999;font-size:11px;">Verfügbar: ${MODULES}</small>
        </div>
        <div class="actions">
          <button class="btn-save" id="zc-save">💾 Speichern</button>
          <button class="btn-delete" id="zc-delete">🗑 Löschen</button>
        </div>
        <p class="status" id="zc-status"></p>
      </div>`;

    this._saveBtn = this.shadowRoot!.querySelector('#zc-save')!;
    this._deleteBtn = this.shadowRoot!.querySelector('#zc-delete')!;
    this._statusEl = this.shadowRoot!.querySelector('#zc-status')!;

    this._saveBtn!.addEventListener('click', () => this._handleSave());
    this._deleteBtn!.addEventListener('click', () => this._handleDelete());
  }

  private _status(msg: string, kind: 'error' | 'success' | 'info' = 'info'): void {
    if (this._statusEl) {
      this._statusEl.textContent = msg;
      this._statusEl.className = `status ${kind}`;
    }
  }

  private _buttonsDisabled(disabled: boolean): void {
    if (this._saveBtn) this._saveBtn.disabled = disabled;
    if (this._deleteBtn) this._deleteBtn!.disabled = disabled;
  }

  private async _handleSave(): Promise<void> {
    const nameEl = this.shadowRoot!.querySelector<HTMLInputElement>('#zc-name')!;
    const iconEl = this.shadowRoot!.querySelector<HTMLInputElement>('#zc-icon')!;
    const moduleEls = this.shadowRoot!.querySelectorAll<HTMLInputElement>('.zc-module:checked');

    const name = nameEl.value.trim();
    if (!name) { this._status('Name erforderlich.', 'error'); return; }

    const modules = Array.from(moduleEls).map(el => el.value);
    const icon = iconEl.value.trim() || 'mdi:room';

    this._buttonsDisabled(true);
    this._status('… speichern', 'info');

    try {
      if (this._zoneId) {
        // Update existing zone
        const payload = {
          name,
          icon,
          active_modules: modules,
        };
        const result = await zoneEditorApi.updateZone(this._zoneId, payload);
        if (!result.ok) throw new Error(result.error ?? 'Update fehlgeschlagen');
        this._status('✓ Zone aktualisiert', 'success');
      } else {
        // Create new zone
        const payload = {
          zone_id: name
            .toLowerCase()
            .replace(/\s+/g, '_')
            .replace(/[^a-z0-9_]/g, ''),
          name,
          icon,
          active_modules: modules,
          enabled: true,
          priority: 10,
          rooms: [],
          entities: {},
        };
        const result = await zoneEditorApi.createZone(payload);
        if (!result.ok) throw new Error(result.error ?? 'Create fehlgeschlagen');
        this._zoneId = (result as { zone?: ZoneEditorZone }).zone?.zone_id;
        this._status('✓ Zone erstellt', 'success');
        // Show delete button after create
        if (this._deleteBtn) this._deleteBtn.style.display = 'inline-block';
      }

      // Invalidate socket cache
      if (typeof window !== 'undefined' && (window as Window & { dashboard?: { socket?: { emit?: (ev: string, d: unknown) => void } } }).dashboard?.socket?.emit) {
        (window as Window & { dashboard?: { socket?: { emit?: (ev: string, d: unknown) => void } } }).dashboard!.socket!.emit!('zone_update', { zones: [] });
      }
    } catch (err) {
      const msg = err instanceof ZoneEditorApiError ? err.message : (err instanceof Error ? err.message : String(err));
      this._status(`✗ ${msg}`, 'error');
    } finally {
      this._buttonsDisabled(false);
    }
  }

  private async _handleDelete(): Promise<void> {
    if (!this._zoneId) return;
    if (!confirm(`Zone "${this._zoneId}" wirklich löschen?`)) return;

    this._buttonsDisabled(true);
    this._status('… löschen', 'info');

    try {
      const result = await zoneEditorApi.deleteZone(this._zoneId);
      if (!result.ok) throw new Error(result.error ?? 'Delete fehlgeschlagen');
      this._status('✓ Zone gelöscht', 'success');
      this._zoneId = undefined;

      // Invalidate socket cache
      if (typeof window !== 'undefined' && (window as Window & { dashboard?: { socket?: { emit?: (ev: string, d: unknown) => void } } }).dashboard?.socket?.emit) {
        (window as Window & { dashboard?: { socket?: { emit?: (ev: string, d: unknown) => void } } }).dashboard!.socket!.emit!('zone_update', { zones: [] });
      }

      // Reset form
      const nameEl = this.shadowRoot!.querySelector<HTMLInputElement>('#zc-name')!;
      if (nameEl) nameEl.value = '';
      if (this._deleteBtn) this._deleteBtn.style.display = 'none';
    } catch (err) {
      const msg = err instanceof ZoneEditorApiError ? err.message : (err instanceof Error ? err.message : String(err));
      this._status(`✗ ${msg}`, 'error');
    } finally {
      this._buttonsDisabled(false);
    }
  }
}

// Register card with Home Assistant
registerCustomCard({
  type: StyxZoneCreatorCard.type,
  name: 'Styx Zone Creator',
  description: 'Erstelle und konfiguriere Zonen mit bis zu 7 modularen Komponenten',
  documentationURL: StyxZoneCreatorCard.documentationURL,
  preview: true,
  default: StyxZoneCreatorCard.getStubConfig(),
});

