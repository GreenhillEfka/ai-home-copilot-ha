/**
 * PS-173 + PS-220: Module Config Editor with HaFormSchema Grid + getConfigForm.
 *
 * Migrates module configuration editor to Home Assistant HaFormSchema grid pattern.
 * Supports:
 * - Grid layout with flatten: true for modules-per-zone
 * - Entity, boolean, text, icon, attribute selectors
 * - Context filters (filter_entity, icon_entity)
 * - static async getConfigForm() (PS-220) for HA Card Editor integration
 *
 * Usage:
 *   const schema = buildModuleConfigSchema(zoneId, modules);
 *   // or via getConfigForm() for HA card editor:
 *   const schema = await MyModuleEditor.getConfigForm();
 */

import { HomeAssistant } from '../types/ha';
import { HabitusZoneV2 } from '../types/zones';
import { buildConfigValidator, ConfigValidationError } from '../utils/editor-schema-validation.js';

/** HaFormSchema return type — matches HA's internal schema format */
export type HaFormSchema = {
  type: string;
  name: string;
  title?: string;
  description?: string;
  required?: boolean;
  default?: unknown;
  selector?: Record<string, unknown>;
  context?: Record<string, unknown>;
  flatten?: boolean;
};

/**
 * Module configuration schema builder.
 * Builds HaFormSchema array for module-per-zone configuration.
 */
export interface ModuleConfigSchema {
  type: 'grid' | 'expandable' | 'entity' | 'boolean' | 'text' | 'icon' | 'attribute';
  name: string;
  title?: string;
  description?: string;
  required?: boolean;
  default?: any;
  selector?: {
    entity?: { filter?: { domain?: string[]; device_class?: string[] } };
    boolean?: Record<string, never>;
    text?: { multiline?: boolean };
    icon?: { placeholder?: string };
    attribute?: { entity_id?: string };
  };
  context?: {
    filter_entity?: string;
    icon_entity?: string;
  };
  flatten?: boolean;
}

/**
 * Module types supported by the editor.
 */
export type ModuleType = 
  | 'licht'
  | 'bewegung'
  | 'musik'
  | 'lautstaerke'
  | 'tv'
  | 'klima'
  | 'kamera'
  | 'cover'
  | 'fan'
  | 'szene'
  | 'sicherheit';

/**
 * Build HaFormSchema for module configuration.
 *
 * @param zoneId - Zone identifier
 * @param modules - Array of module types to configure
 * @param hass - Home Assistant instance for entity lookups
 * @returns HaFormSchema array for grid-based module config
 */
export function buildModuleConfigSchema(
  zoneId: string,
  modules: ModuleType[],
  hass?: HomeAssistant,
): ModuleConfigSchema[] {
  const schema: ModuleConfigSchema[] = [];

  // Grid container for all modules
  schema.push({
    type: 'grid',
    name: 'modules',
    title: 'Module pro Zone',
    description: `Konfiguriere Module für Zone ${zoneId}`,
    flatten: true,
  });

  // Add module-specific fields
  modules.forEach((moduleType) => {
    const moduleSchema = buildModuleFieldSchema(moduleType, zoneId, hass);
    schema.push(...moduleSchema);
  });

  return schema;
}

/**
 * Build HaFormSchema for a single module type.
 *
 * @param moduleType - Type of module (licht, bewegung, etc.)
 * @param zoneId - Zone identifier
 * @param hass - Home Assistant instance
 * @returns Array of field schemas for this module
 */
function buildModuleFieldSchema(
  moduleType: ModuleType,
  zoneId: string,
  hass?: HomeAssistant,
): ModuleConfigSchema[] {
  const fields: ModuleConfigSchema[] = [];

  switch (moduleType) {
    case 'licht':
      fields.push(
        {
          type: 'entity',
          name: `${zoneId}_licht_main`,
          title: 'Hauptlicht',
          required: false,
          selector: {
            entity: {
              filter: {
                domain: ['light'],
              },
            },
          },
          context: {
            filter_entity: `${zoneId}_licht_main`,
          },
        },
        {
          type: 'entity',
          name: `${zoneId}_licht_ambient`,
          title: 'Ambientebeleuchtung',
          required: false,
          selector: {
            entity: {
              filter: {
                domain: ['light'],
              },
            },
          },
        },
        {
          type: 'boolean',
          name: `${zoneId}_licht_auto`,
          title: 'Automatik',
          description: 'Automatische Lichtsteuerung aktivieren',
          default: true,
          selector: {
            boolean: {},
          },
        },
      );
      break;

    case 'bewegung':
      fields.push(
        {
          type: 'entity',
          name: `${zoneId}_bewegung_sensor`,
          title: 'Bewegungssensor',
          required: false,
          selector: {
            entity: {
              filter: {
                domain: ['binary_sensor'],
                device_class: ['motion'],
              },
            },
          },
        },
        {
          type: 'attribute',
          name: `${zoneId}_bewegung_timeout`,
          title: 'Timeout (Sekunden)',
          description: 'Zeit bis Bewegung als inaktiv markiert wird',
          default: 30,
          selector: {
            attribute: {
              entity_id: `${zoneId}_bewegung_sensor`,
            },
          },
        },
      );
      break;

    case 'musik':
      fields.push(
        {
          type: 'entity',
          name: `${zoneId}_musik_player`,
          title: 'Musikplayer',
          required: false,
          selector: {
            entity: {
              filter: {
                domain: ['media_player'],
              },
            },
          },
        },
        {
          type: 'text',
          name: `${zoneId}_musik_playlist`,
          title: 'Playlist URL',
          description: 'Spotify/Apple Music Playlist URL',
          required: false,
          selector: {
            text: {
              multiline: false,
            },
          },
        },
      );
      break;

    case 'klima':
      fields.push(
        {
          type: 'entity',
          name: `${zoneId}_klima_thermostat`,
          title: 'Thermostat',
          required: false,
          selector: {
            entity: {
              filter: {
                domain: ['climate'],
              },
            },
          },
        },
        {
          type: 'entity',
          name: `${zoneId}_klima_temperatur`,
          title: 'Temperatursensor',
          required: false,
          selector: {
            entity: {
              filter: {
                domain: ['sensor'],
                device_class: ['temperature'],
              },
            },
          },
        },
        {
          type: 'text',
          name: `${zoneId}_klima_target_temp`,
          title: 'Zieltemperatur (°C)',
          default: '21',
          selector: {
            text: {
              multiline: false,
            },
          },
        },
      );
      break;

    case 'kamera':
      fields.push(
        {
          type: 'entity',
          name: `${zoneId}_kamera_main`,
          title: 'Hauptkamera',
          required: false,
          selector: {
            entity: {
              filter: {
                domain: ['camera'],
              },
            },
          },
        },
        {
          type: 'boolean',
          name: `${zoneId}_kamera_recording`,
          title: 'Aufnahme aktivieren',
          default: false,
          selector: {
            boolean: {},
          },
        },
      );
      break;

    case 'cover':
      fields.push(
        {
          type: 'entity',
          name: `${zoneId}_cover_main`,
          title: 'Rolladen/Markise',
          required: false,
          selector: {
            entity: {
              filter: {
                domain: ['cover'],
              },
            },
          },
        },
        {
          type: 'icon',
          name: `${zoneId}_cover_icon`,
          title: 'Icon',
          default: 'mdi:blinds',
          selector: {
            icon: {
              placeholder: 'mdi:blinds',
            },
          },
        },
      );
      break;

    default:
      // Generic fallback for unknown module types
      fields.push({
        type: 'text',
        name: `${zoneId}_${moduleType}_config`,
        title: `${moduleType} Konfiguration`,
        required: false,
        selector: {
          text: {
            multiline: true,
          },
        },
      });
  }

  return fields;
}

/**
 * Get available module types for a zone.
 *
 * @param zone - Zone configuration
 * @returns Array of available module types
 */
export function getAvailableModulesForZone(zone: HabitusZoneV2): ModuleType[] {
  const modules: ModuleType[] = [];

  // Infer modules from zone entities
  if (zone.entities?.licht) modules.push('licht');
  if (zone.entities?.bewegung) modules.push('bewegung');
  if (zone.entities?.musik) modules.push('musik');
  if (zone.entities?.klima) modules.push('klima');
  if (zone.entities?.kamera) modules.push('kamera');
  if (zone.entities?.cover) modules.push('cover');

  // Always include these base modules
  if (!modules.includes('licht')) modules.push('licht');
  if (!modules.includes('bewegung')) modules.push('bewegung');

  return modules;
}

/**
 * Validate module configuration against schema.
 * Uses ConfigValidationError for consistent error reporting.
 *
 * @param config - Configuration object to validate
 * @param schema - HaFormSchema array
 * @throws ConfigValidationError on validation failure
 */
export function validateModuleConfig(
  config: Record<string, any>,
  schema: HaFormSchema[],
): void {
  const requiredFields = schema.filter((field) => field.required);

  for (const field of requiredFields) {
    if (field.name === 'modules') continue; // grid container, not a real field
    const value = config[field.name];
    if (value === undefined || value === null || value === '') {
      throw new ConfigValidationError(
        `Missing required field: ${field.name}`,
        field.name,
        'non-empty value',
        String(value),
        'REQUIRED_FIELD_MISSING',
      );
    }
  }

  // Optional: validate selector types match
  for (const field of schema) {
    if (field.name === 'modules') continue;
    const value = config[field.name];
    if (value === undefined || value === null) continue;

    if (field.selector) {
      const selectorType = Object.keys(field.selector)[0];
      switch (selectorType) {
        case 'entity':
          if (typeof value !== 'string' && !Array.isArray(value)) {
            throw new ConfigValidationError(
              `Expected entity ID (string), got ${typeof value}`,
              field.name,
              'string | string[]',
              typeof value,
              'SCHEMA_DRIFT',
            );
          }
          break;
        case 'boolean':
          if (typeof value !== 'boolean') {
            throw new ConfigValidationError(
              `Expected boolean, got ${typeof value}`,
              field.name,
              'boolean',
              typeof value,
              'SCHEMA_DRIFT',
            );
          }
          break;
        case 'number':
          if (typeof value !== 'number' && !Array.isArray(value)) {
            throw new ConfigValidationError(
              `Expected number, got ${typeof value}`,
              field.name,
              'number | number[]',
              typeof value,
              'SCHEMA_DRIFT',
            );
          }
          break;
      }
    }
  }
}

// ── HA Card Editor integration (PS-220) ───────────────────────────────────────

/**
 * PS-220: ModuleConfigEditor — HA Card Editor integration via getConfigForm().
 *
 * Provides HA-PR #16142 `static async getConfigForm()` for the module config editor.
 * Used by the HA card editor UI to render the configuration form.
 */
export class ModuleConfigEditor {
  /**
   * HA Card Editor integration point.
   * Returns HaFormSchema[] for the given zone configuration.
   */
  static async getConfigForm(zoneId: string, modules: ModuleType[]): Promise<HaFormSchema[]> {
    // buildModuleConfigSchema already returns the right shape, just cast
    return buildModuleConfigSchema(zoneId, modules) as HaFormSchema[];
  }
}

