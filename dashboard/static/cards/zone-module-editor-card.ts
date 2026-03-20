/**
 * PS-198/200: Zone Module Editor Card
 *
 * Editor schema for configuring zone modules with a fixed set of 7 module types:
 * - LIGHT
 * - AUDIO
 * - CLIMATE
 * - COVER
 * - ENERGY
 * - SCENE
 * - SECURITY
 *
 * Uses:
 * - PS-198 card-form-helper.ts for HaFormSchema generation
 * - PS-200 editor-schema-validation.ts for optional config schema validation
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

export type ZoneModuleType =
  | 'LIGHT'
  | 'AUDIO'
  | 'CLIMATE'
  | 'COVER'
  | 'ENERGY'
  | 'SCENE'
  | 'SECURITY';

export const ZONE_MODULE_TYPES: readonly ZoneModuleType[] = [
  'LIGHT',
  'AUDIO',
  'CLIMATE',
  'COVER',
  'ENERGY',
  'SCENE',
  'SECURITY',
] as const;

export interface ZoneModuleEditorCardConfig extends Record<string, unknown> {
  zone_id: string;
  zone_name: string;
  module_type: ZoneModuleType;

  light_entity?: string;
  audio_entity?: string;
  climate_entity?: string;
  cover_entity?: string;
  energy_entity?: string;
  scene_entity?: string;
  security_entity?: string;

  light_filter_entity?: string;
  climate_filter_entity?: string;
  cover_filter_entity?: string;

  show_grid: boolean;
  compact_mode: boolean;

  // --- Secondary Zone States (PS-165/PS-137) ---
  /** Zone ist im Dunkel-Modus (Lichtsensor/Sonne unter Schwelle) */
  dark?: boolean;
  /** Zone ist im Sleep-Modus (manueller Switch-Override) */
  sleep?: boolean;
  /** Zone hat Zeitlimit überschritten (extended mode) */
  extended?: boolean;
}

const BASE_FIELDS: HaFormFieldDescriptor[] = [
  {
    name: 'zone_id',
    type: 'text',
    title: 'Zone-ID',
    description: 'Zonen-ID aus dem Core/Zone-Store',
    required: true,
  },
  {
    name: 'zone_name',
    type: 'text',
    title: 'Zonen-Name',
    description: 'Lesbarer Anzeigename der Zone',
    required: false,
  },
  {
    name: 'module_type',
    type: 'text',
    title: 'Modultyp',
    description: 'Erlaubt: LIGHT, AUDIO, CLIMATE, COVER, ENERGY, SCENE, SECURITY',
    required: true,
    defaultValue: 'LIGHT',
  },
  {
    name: 'show_grid',
    type: 'boolean',
    title: 'Grid anzeigen',
    description: 'Grid-Layout für die Modulform verwenden',
    required: false,
    defaultValue: true,
  },
  {
    name: 'compact_mode',
    type: 'boolean',
    title: 'Kompaktmodus',
    description: 'Formularfelder kompakt darstellen',
    required: false,
    defaultValue: false,
  },

  // --- Secondary Zone States (PS-165/PS-137) ---
  {
    name: 'dark',
    type: 'boolean',
    title: '🌙 Dunkel-Modus',
    description: 'Zone dunkel (Lichtsensor/Sonne unter Schwelle)',
    required: false,
    defaultValue: false,
  },
  {
    name: 'sleep',
    type: 'boolean',
    title: '😴 Sleep-Modus',
    description: 'Zone im Sleep (manueller Switch-Override)',
    required: false,
    defaultValue: false,
  },
  {
    name: 'extended',
    type: 'boolean',
    title: '⏱ Extended',
    description: 'Zone hat Zeitlimit überschritten',
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
    description: 'Filter-Entity für Licht-Filterung',
    required: false,
    domain: ['input_boolean', 'binary_sensor'],
    context: { filter_entity: 'light_filter_entity' },
  },
];

const AUDIO_FIELDS: HaFormFieldDescriptor[] = [
  {
    name: 'audio_entity',
    type: 'entity',
    title: 'Audio-Entity',
    description: 'Media-Player für Musik/Wiedergabe',
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
    description: 'Thermostat/Klimaanlage für diese Zone',
    required: false,
    domain: ['climate'],
  },
  {
    name: 'climate_filter_entity',
    type: 'entity',
    title: 'Klima-Filter',
    description: 'Filter-Entity für temperaturbezogene Auswahl',
    required: false,
    domain: ['input_boolean', 'binary_sensor', 'sensor'],
    context: { filter_entity: 'climate_filter_entity' },
  },
];

const COVER_FIELDS: HaFormFieldDescriptor[] = [
  {
    name: 'cover_entity',
    type: 'entity',
    title: 'Cover-Entity',
    description: 'Rollladen/Markise-Entity für diese Zone',
    required: false,
    domain: ['cover'],
  },
  {
    name: 'cover_filter_entity',
    type: 'entity',
    title: 'Cover-Filter',
    description: 'Filter-Entity für Cover-Auswahl',
    required: false,
    domain: ['input_boolean', 'binary_sensor'],
    context: { filter_entity: 'cover_filter_entity' },
  },
];

const ENERGY_FIELDS: HaFormFieldDescriptor[] = [
  {
    name: 'energy_entity',
    type: 'entity',
    title: 'Energie-Entity',
    description: 'Energie-/Stromsensor für diese Zone',
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
    description: 'Alarm-/Sensor-Entity (z. B. Tür, Bewegung, Smoke)',
    required: false,
    domain: ['alarm_control_panel', 'binary_sensor', 'sensor'],
    deviceClass: ['motion', 'opening', 'smoke', 'gas'],
  },
];

const MODULE_CONFIG_FIELDS: Record<ZoneModuleType, HaFormFieldDescriptor[]> = {
  LIGHT: LIGHT_FIELDS,
  AUDIO: AUDIO_FIELDS,
  CLIMATE: CLIMATE_FIELDS,
  COVER: COVER_FIELDS,
  ENERGY: ENERGY_FIELDS,
  SCENE: SCENE_FIELDS,
  SECURITY: SECURITY_FIELDS,
};

const FIELD_ORDER: ZoneModuleType[] = [...ZONE_MODULE_TYPES];
const ALL_MODULE_FIELDS = FIELD_ORDER.flatMap((moduleType) => MODULE_CONFIG_FIELDS[moduleType]);

const ZONE_MODULE_EDITOR_SCHEMA: HaFormSchema[] = buildHaFormSchema(
  [...BASE_FIELDS, ...ALL_MODULE_FIELDS],
  {
    gridName: 'zone-module-editor',
    gridTitle: 'Zone Module Editor',
    gridDescription: 'Konfiguriere Zone-Module in 7 Typen',
    flatten: true,
  },
);

const VALID_MODULE_TYPE_SET = new Set<string>(ZONE_MODULE_TYPES);

function assertModuleType(value: unknown): asserts value is ZoneModuleType {
  if (typeof value !== 'string' || !VALID_MODULE_TYPE_SET.has(value)) {
    throw new ConfigValidationError(
      `Ungültiger Modultyp '${String(value)}'. Erlaubt sind: ${ZONE_MODULE_TYPES.join(', ')}`,
      'module_type',
      `'${ZONE_MODULE_TYPES.join('|')}'`,
      typeof value,
    );
  }
}

const validateZoneModuleEditorConfig: (config: unknown) => asserts config is ZoneModuleEditorCardConfig =
  buildConfigValidator<ZoneModuleEditorCardConfig>(ZONE_MODULE_EDITOR_SCHEMA);

export class ZoneModuleEditorCard extends HTMLElement {
  static get type(): string {
    return 'zone-module-editor';
  }

  static get documentationURL(): string {
    return 'https://pilotsuite.io/docs/cards/zone-module-editor';
  }

  static async getConfigForm(): Promise<HaFormSchema[]> {
    return ZONE_MODULE_EDITOR_SCHEMA;
  }

  static getStubConfig(): Partial<ZoneModuleEditorCardConfig> {
    return {
      zone_id: 'zone_living',
      zone_name: 'Neue Zone',
      module_type: 'LIGHT',
      show_grid: true,
      compact_mode: false,
      dark: false,
      sleep: false,
      extended: false,
    };
  }

  /**
   * Validate a config object against the editor schema and enum constraints.
   */
  static validateConfig(config: unknown): void {
    validateZoneModuleEditorConfig(config as Record<string, unknown>);
    const cfg = config as ZoneModuleEditorCardConfig;
    assertModuleType(cfg?.module_type);
  }
}

// Register card with Home Assistant
registerCustomCard({
  type: ZoneModuleEditorCard.type,
  name: 'Zone Module Editor',
  description: 'Konfiguriere Module je Zone (LIGHT, AUDIO, CLIMATE, COVER, ENERGY, SCENE, SECURITY)',
  documentationURL: ZoneModuleEditorCard.documentationURL,
  preview: true,
  default: ZoneModuleEditorCard.getStubConfig(),
});

