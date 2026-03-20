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

