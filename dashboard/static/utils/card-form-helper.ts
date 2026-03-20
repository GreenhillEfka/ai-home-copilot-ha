/**
 * PS-198: Reusable Home Assistant form helper for card config editors.
 *
 * Provides:
 * - Grid-based HaFormSchema output (flattened)
 * - Supported selector types: entity / boolean / text / number / icon / attribute
 * - Context-filter support (filter_entity / icon_entity)
 * - Validation helpers for card config payloads
 */

export type HaFormSelectorType = 'entity' | 'boolean' | 'text' | 'number' | 'icon' | 'attribute' | 'array';

export interface HaFormContextFilter {
  filter_entity?: string;
  icon_entity?: string;
}

export interface HaFormGridSchema {
  type: 'grid';
  name: string;
  title: string;
  description?: string;
  flatten: boolean;
}

export interface HaFormFieldSchema {
  type: HaFormSelectorType;
  name: string;
  title: string;
  description?: string;
  required?: boolean;
  default?: unknown;
  selector: HaFormSelector;
  context?: HaFormContextFilter;
  multiple?: boolean;
}

export type HaFormSchema = HaFormGridSchema | HaFormFieldSchema;

export interface HaFormSelector {
  entity?: {
    filter?: {
      domain?: string[];
      device_class?: string[];
    };
  };
  boolean?: Record<string, never>;
  text?: {
    multiline?: boolean;
  };
  number?: {
    min?: number;
    max?: number;
    step?: number;
  };
  icon?: {
    placeholder?: string;
  };
  attribute?: {
    entity_id?: string;
  };
  array?: {
    max?: number;
  };
}

export interface HaFormFieldDescriptor {
  name: string;
  type: HaFormSelectorType;
  title: string;
  description?: string;
  required?: boolean;
  defaultValue?: unknown;

  // Entity selector filters.
  domain?: string[];
  deviceClass?: string[];

  // Text selector options.
  multiline?: boolean;

  // Number selector options.
  min?: number;
  max?: number;
  step?: number;

  // Icon selector options.
  iconPlaceholder?: string;

  // Attribute selector options.
  attributeEntityId?: string;

  // Array selector options.
  arrayMax?: number;

  // Multi-value support.
  multiple?: boolean;

  // Optional context filters for field coupling.
  context?: HaFormContextFilter;
}

export interface BuildHaFormSchemaOptions {
  gridName?: string;
  gridTitle?: string;
  gridDescription?: string;
  flatten?: boolean;
}

export type RawOrBuiltHaFormSchema = HaFormFieldDescriptor | HaFormFieldSchema;

/**
 * Build a Home Assistant HaFormSchema with a leading flattened grid container.
 */
export function buildHaFormSchema(
  fields: RawOrBuiltHaFormSchema[],
  options: BuildHaFormSchemaOptions = {},
): HaFormSchema[] {
  const schema: HaFormSchema[] = [];

  schema.push({
    type: 'grid',
    name: options.gridName ?? 'card',
    title: options.gridTitle ?? 'Card configuration',
    description: options.gridDescription,
    flatten: options.flatten ?? true,
  });

  for (const field of fields) {
    if (isFieldSchema(field)) {
      assertFieldSchemaConsistency(field);
      schema.push(field);
      continue;
    }

    schema.push(buildHaFormFieldSchema(field));
  }

  return schema;
}

/**
 * Validate a card config object against a schema built with this helper.
 */
export function validateCardConfig(
  config: Record<string, unknown>,
  schema: HaFormSchema[],
): boolean {
  if (!config || typeof config !== 'object') {
    return false;
  }

  const schemaByName = new Map<string, HaFormFieldSchema>(
    schema
      .filter((entry): entry is HaFormFieldSchema => entry.type !== 'grid')
      .map((entry) => [entry.name, entry]),
  );

  for (const field of schemaByName.values()) {
    try {
      assertFieldSchemaConsistency(field);
    } catch (error) {
      console.warn(
        `[PS-198] Invalid field schema '${field.name}':`,
        error instanceof Error ? error.message : error,
      );
      return false;
    }

    const value = config[field.name];

    if (field.required && isMissingFieldValue(field, value)) {
      console.warn(`[PS-198] Missing required field: ${field.name}`);
      return false;
    }

    if (value === undefined || value === null) {
      continue;
    }

    if (!isValidFieldValue(field, value)) {
      console.warn(
        `[PS-198] Invalid ${describeFieldValueType(field)} field '${field.name}':`,
        value,
      );
      return false;
    }
  }

  for (const field of schemaByName.values()) {
    if (!field.context) {
      continue;
    }

    const { filter_entity: filterEntity, icon_entity: iconEntity } = field.context;

    if (filterEntity && !schemaByName.has(filterEntity)) {
      console.warn(`[PS-198] filter_entity '${filterEntity}' referenced by '${field.name}' does not exist`);
      return false;
    }

    if (filterEntity && field.type === 'attribute') {
      const referencedField = schemaByName.get(filterEntity);
      if (referencedField && referencedField.type !== 'entity') {
        console.warn(
          `[PS-198] Attribute field '${field.name}' requires an entity field for filter_entity, got '${referencedField.type}'`,
        );
        return false;
      }
    }

    if (iconEntity && !schemaByName.has(iconEntity)) {
      console.warn(`[PS-198] icon_entity '${iconEntity}' referenced by '${field.name}' does not exist`);
      return false;
    }
  }

  return true;
}

/**
 * Throw if config does not validate.
 */
export function assertConfig(config: Record<string, unknown>, schema: HaFormSchema[]): void {
  if (!validateCardConfig(config, schema)) {
    throw new Error('[PS-198] Invalid card config');
  }
}

export function isMissingFieldValue(field: HaFormFieldSchema, value: unknown): boolean {
  if (value === undefined || value === null) {
    return true;
  }

  if (allowsStringArray(field) || isMultipleField(field)) {
    if (Array.isArray(value)) {
      return value.length === 0;
    }
  }

  if (typeof value === 'string') {
    return value.trim() === '';
  }

  return false;
}

export function isValidFieldValue(field: HaFormFieldSchema, value: unknown): boolean {
  switch (field.type) {
    case 'boolean':
      return typeof value === 'boolean';

    case 'number':
      return isMultipleField(field) ? isNumberArray(value) : isFiniteNumber(value);

    case 'entity':
    case 'icon':
    case 'attribute':
    case 'array':
      return isMultipleField(field) ? isStringArray(value) : typeof value === 'string';

    case 'text':
      if (isMultipleField(field)) {
        return isStringArray(value);
      }

      if (allowsStringArray(field)) {
        return typeof value === 'string' || isStringArray(value);
      }

      return typeof value === 'string';
  }
}

export function describeFieldValueType(field: Pick<HaFormFieldSchema, 'type' | 'multiple' | 'default' | 'selector'>): string {
  const multiple = isMultipleField(field);

  switch (field.type) {
    case 'boolean':
      return 'boolean';
    case 'number':
      return multiple ? 'number[]' : 'number';
    case 'entity':
    case 'icon':
    case 'attribute':
    case 'array':
      return multiple ? 'string[]' : 'string';
    case 'text':
      if (multiple) {
        return 'string[]';
      }

      return allowsStringArray(field) ? 'string | string[]' : 'string';
  }
}

export function assertFieldSchemaConsistency(field: HaFormFieldSchema): void {
  if (field.type === 'boolean' && isMultipleField(field)) {
    throw new Error(`[PS-198] Field '${field.name}' cannot be both boolean and multiple`);
  }

  if (field.default !== undefined && field.default !== null && !isValidFieldValue(field, field.default)) {
    throw new Error(
      `[PS-198] Field '${field.name}' default must be ${describeFieldValueType(field)}`,
    );
  }
}

function buildHaFormFieldSchema(field: HaFormFieldDescriptor): HaFormFieldSchema {
  const builtField: HaFormFieldSchema = {
    type: field.type,
    name: field.name,
    title: field.title,
    description: field.description,
    required: field.required,
    default: field.defaultValue,
    selector: selectorForField(field),
    ...(field.context ? { context: field.context } : {}),
    ...(isMultipleField(field) ? { multiple: true } : {}),
  };

  assertFieldSchemaConsistency(builtField);

  return builtField;
}

function selectorForField(field: HaFormFieldDescriptor): HaFormSelector {
  switch (field.type) {
    case 'entity':
      return {
        entity: {
          filter: {
            ...(field.domain ? { domain: field.domain } : {}),
            ...(field.deviceClass ? { device_class: field.deviceClass } : {}),
          },
        },
      };

    case 'boolean':
      return {
        boolean: {},
      };

    case 'text':
      return {
        text: {
          ...(field.multiline ? { multiline: true } : {}),
        },
      };

    case 'number':
      return {
        number: {
          ...(field.min !== undefined ? { min: field.min } : {}),
          ...(field.max !== undefined ? { max: field.max } : {}),
          ...(field.step !== undefined ? { step: field.step } : {}),
        },
      };

    case 'icon':
      return {
        icon: {
          ...(field.iconPlaceholder ? { placeholder: field.iconPlaceholder } : {}),
        },
      };

    case 'attribute': {
      const entityId = resolveAttributeEntityId(field.attributeEntityId);

      return {
        attribute: {
          ...(entityId ? { entity_id: entityId } : {}),
        },
      };
    }

    case 'array':
      return {
        array: {
          ...(field.arrayMax !== undefined ? { max: field.arrayMax } : {}),
        },
      };
  }
}

function resolveAttributeEntityId(attributeEntityId: string | undefined): string | undefined {
  return normalizeNonEmptyString(attributeEntityId);
}

function isMultipleField(field: Pick<HaFormFieldSchema, 'multiple' | 'default'> | Pick<HaFormFieldDescriptor, 'multiple' | 'defaultValue'>): boolean {
  if (field.multiple !== undefined) {
    return field.multiple;
  }

  if ('defaultValue' in field) {
    return Array.isArray(field.defaultValue);
  }

  return Array.isArray((field as Pick<HaFormFieldSchema, 'default'>).default);
}

function allowsStringArray(
  field: Pick<HaFormFieldSchema, 'type' | 'selector' | 'multiple' | 'default'>,
): boolean {
  return field.type === 'text' && field.selector.text?.multiline === true;
}

function isFiniteNumber(value: unknown): value is number {
  return typeof value === 'number' && Number.isFinite(value);
}

function isStringArray(value: unknown): value is string[] {
  return Array.isArray(value) && value.every((item) => typeof item === 'string');
}

function isNumberArray(value: unknown): value is number[] {
  return Array.isArray(value) && value.every((item) => isFiniteNumber(item));
}

function normalizeNonEmptyString(value: unknown): string | undefined {
  return typeof value === 'string' && value.trim() !== '' ? value : undefined;
}

function isFieldSchema(field: RawOrBuiltHaFormSchema): field is HaFormFieldSchema {
  return (field as HaFormFieldSchema).type !== undefined && (field as HaFormFieldSchema).selector !== undefined;
}

// ---------------------------------------------------------------------------
// Window adapter — exposes CardFormHelper to window.customCards[] cards
// ---------------------------------------------------------------------------

declare global {
  interface Window {
    CardFormHelper?: typeof CardFormHelper;
  }
}

/**
 * Stateless adapter so cards registered via window.customCards[]
 * can call `window.CardFormHelper.buildHaFormSchema(fields)` without
 * importing the module directly.
 *
 * Usage in card class:
 *   static async getConfigForm() {
 *     return window.CardFormHelper!.buildHaFormSchema(MY_FIELDS);
 *   }
 */
export const CardFormHelper = {
  buildHaFormSchema,
  validateCardConfig,
  assertConfig,
} as const;

if (typeof window !== 'undefined') {
  window.CardFormHelper = CardFormHelper;
}
