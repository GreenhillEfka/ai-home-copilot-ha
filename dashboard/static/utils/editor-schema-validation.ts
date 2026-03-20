/**
 * PS-200: Card Editor Schema Validation Gate
 *
 * Provides runtime schema validation for card config editors.
 * Detects schema drift between form definitions and config interfaces.
 * Throws ConfigValidationError on mismatch.
 *
 * Integration:
 * - PS-198 (card-form-helper.ts): HaFormSchema types & validation helpers
 * - PS-199 (styx-zone-creator-card.ts): Example card implementation
 */

import type {
  HaFormSchema,
  HaFormFieldSchema,
} from './card-form-helper.js';
import {
  assertFieldSchemaConsistency,
  describeFieldValueType,
  isMissingFieldValue,
  isValidFieldValue,
} from './card-form-helper.js';

/**
 * Thrown when schema drift is detected between form schema and config interface.
 */
export class ConfigValidationError extends Error {
  constructor(
    message: string,
    public readonly field?: string,
    public readonly expectedType?: string,
    public readonly actualType?: string,
  ) {
    super(message);
    this.name = 'ConfigValidationError';
  }
}

/**
 * Validate that a card config object conforms to its editor schema.
 *
 * Checks:
 * - All required fields are present
 * - Field types match schema definitions
 * - No unexpected fields (strict mode)
 * - Context references are valid
 *
 * @param config - The config object to validate
 * @param schema - The HaFormSchema array from getConfigForm()
 * @param options - Validation options (strict mode, allowed extra fields)
 * @throws ConfigValidationError on schema drift
 */
export function validateEditorSchema(
  config: Record<string, unknown>,
  schema: HaFormSchema[],
  options: ValidateSchemaOptions = {},
): void {
  if (!config || typeof config !== 'object') {
    throw new ConfigValidationError(
      'Config must be a non-null object',
      undefined,
      'object',
      typeof config,
    );
  }

  const { strict = false, allowedExtraFields = [] } = options;

  // Extract form fields (skip grid containers)
  const formFields = schema.filter(
    (entry): entry is HaFormFieldSchema => entry.type !== 'grid',
  );

  const fieldMap = new Map<string, HaFormFieldSchema>(
    formFields.map((f) => [f.name, f]),
  );

  validateFieldDefinitions(formFields);

  // Check required fields
  for (const field of formFields) {
    if (field.required) {
      const value = config[field.name];
      if (isMissingFieldValue(field, value)) {
        throw new ConfigValidationError(
          `Required field '${field.name}' is missing or empty`,
          field.name,
          'present',
          String(value),
        );
      }
    }
  }

  // Validate field types
  for (const [fieldName, fieldValue] of Object.entries(config)) {
    const fieldSchema = fieldMap.get(fieldName);

    if (!fieldSchema) {
      if (strict && !allowedExtraFields.includes(fieldName)) {
        throw new ConfigValidationError(
          `Unexpected field '${fieldName}' in strict mode`,
          fieldName,
          'not present',
          'present',
        );
      }
      continue;
    }

    validateFieldType(fieldName, fieldValue, fieldSchema);
  }

  // Validate context references
  validateContextReferences(formFields, fieldMap);
}

/**
 * Validate a single field value against its schema type.
 */
function validateFieldType(
  fieldName: string,
  value: unknown,
  schema: HaFormFieldSchema,
): void {
  // Skip validation for optional fields that are undefined/null
  if (!schema.required && (value === undefined || value === null)) {
    return;
  }

  if (!isValidFieldValue(schema, value)) {
    throw new ConfigValidationError(
      `Field '${fieldName}' must be ${describeFieldValueType(schema)}`,
      fieldName,
      describeFieldValueType(schema),
      describeActualValueType(value),
    );
  }
}

/**
 * Validate field definitions before runtime config validation.
 */
function validateFieldDefinitions(formFields: HaFormFieldSchema[]): void {
  for (const field of formFields) {
    try {
      assertFieldSchemaConsistency(field);
    } catch (error) {
      throw new ConfigValidationError(
        error instanceof Error ? error.message : String(error),
        field.name,
        describeFieldValueType(field),
        describeActualValueType(field.default),
      );
    }
  }
}

/**
 * Validate that context references point to existing fields.
 */
function validateContextReferences(
  formFields: HaFormFieldSchema[],
  fieldMap: Map<string, HaFormFieldSchema>,
): void {
  for (const field of formFields) {
    if (!field.context) {
      continue;
    }

    const { filter_entity: filterEntity, icon_entity: iconEntity } = field.context;

    if (filterEntity && !fieldMap.has(filterEntity)) {
      throw new ConfigValidationError(
        `Field '${field.name}' references non-existent context field '${filterEntity}'`,
        field.name,
        'valid context reference',
        `missing '${filterEntity}'`,
      );
    }

    if (filterEntity && field.type === 'attribute') {
      const referencedField = fieldMap.get(filterEntity);
      if (referencedField && referencedField.type !== 'entity') {
        throw new ConfigValidationError(
          `Field '${field.name}' requires filter_entity '${filterEntity}' to reference an entity field`,
          field.name,
          'entity context reference',
          referencedField.type,
        );
      }
    }

    if (iconEntity && !fieldMap.has(iconEntity)) {
      throw new ConfigValidationError(
        `Field '${field.name}' references non-existent context field '${iconEntity}'`,
        field.name,
        'valid context reference',
        `missing '${iconEntity}'`,
      );
    }
  }
}

function describeActualValueType(value: unknown): string {
  if (Array.isArray(value)) {
    if (value.every((item) => typeof item === 'string')) {
      return 'string[]';
    }

    if (value.every((item) => typeof item === 'number' && Number.isFinite(item))) {
      return 'number[]';
    }

    return 'array';
  }

  if (value === null) {
    return 'null';
  }

  return typeof value;
}

/**
 * Type guard: check if value matches expected primitive type.
 */
export function isType(value: unknown, type: string): boolean {
  return typeof value === type;
}

/**
 * Assert that a condition is truthy, throw ConfigValidationError if not.
 */
export function assert(condition: boolean, message: string, field?: string): void {
  if (!condition) {
    throw new ConfigValidationError(message, field);
  }
}

/**
 * Validation options for validateEditorSchema().
 */
export interface ValidateSchemaOptions {
  /**
   * If true, reject any fields not defined in schema.
   * Default: false (allows extra fields).
   */
  strict?: boolean;

  /**
   * List of field names allowed even in strict mode.
   * Useful for legacy fields or metadata.
   */
  allowedExtraFields?: string[];
}

/**
 * Build a type validator for a specific config interface.
 *
 * Usage:
 *   const validateZoneConfig = buildConfigValidator<StyxZoneCreatorCardConfig>(zoneSchema);
 *   validateZoneConfig(config); // throws ConfigValidationError
 */
export function buildConfigValidator<T extends Record<string, unknown>>(
  schema: HaFormSchema[],
  options?: ValidateSchemaOptions,
): (config: unknown) => asserts config is T {
  return (config: unknown): asserts config is T => {
    validateEditorSchema(config as Record<string, unknown>, schema, options);
  };
}
