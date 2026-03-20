/**
 * PS-200: Card-Editor Schema Validation Gate
 *
 * Browser-side CI-equivalent gate that validates Card-Config payloads
 * against their HaFormSchema before any save/submit/API call.
 *
 * - Catches schema drift (extra fields, missing required, wrong types)
 * - Throws ConfigValidationError with field-level detail
 * - Integrates with:
 *   - card-form-helper.ts (PS-198): schema source-of-truth
 *   - zone-editor-api-client.ts: pre-submit gate for zone saves
 *   - dashboard.js save handlers: per-button save gate
 *
 * Usage (card-level):
 *   import { buildConfigValidator, ConfigValidationError } from './editor-schema-validation.js';
 *   const validate = buildConfigValidator(MY_CARD_SCHEMA);
 *   validate(cfg); // throws ConfigValidationError on drift
 *
 * Usage (save handler):
 *   import { validateEditorSchema } from './editor-schema-validation.js';
 *   // before API call:
 *   validateEditorSchema(rawFormData, myCardSchema, 'StyxCard');
 *
 * Errors are serializable and safe to surface in UI toasts or HA error panels.
 */

import type { HaFormSchema } from './card-form-helper.js';
import { validateCardConfig } from './card-form-helper.js';

// ── ConfigValidationError ────────────────────────────────────────────────────

/**
 * Thrown by `buildConfigValidator()` and `validateEditorSchema()` when a
 * card config violates its HaFormSchema.
 *
 * Serializable — safe to JSON.stringify and pass to UI toast/title handlers.
 */
export class ConfigValidationError extends Error {
  constructor(
    /**
     * Human-readable summary of the validation failure.
     */
    public readonly message: string,
    /**
     * Field name that caused the failure (e.g. 'active_modules', 'zone_name').
     * 'undefined' for schema-level or cross-field failures.
     */
    public readonly field: string | undefined,
    /**
     * Expected type description (e.g. 'string', 'boolean', 'ZoneCreatorModuleType[]').
     */
    public readonly expected: string,
    /**
     * Actual type of the received value (e.g. 'number', 'object').
     */
    public readonly received: string,
    /**
     * Machine-readable error code for programmatic handling.
     */
    public readonly code: ConfigValidationErrorCode = 'SCHEMA_DRIFT',
    /**
     * Optional nested sub-errors (e.g. for batch field validation).
     */
    public readonly causes: ConfigValidationError[] = [],
  ) {
    super(message);
    this.name = 'ConfigValidationError';
    // Fix prototype chain for proper `instanceof` checks
    Object.setPrototypeOf(this, ConfigValidationError.prototype);
  }

  toJSON(): object {
    return {
      name: this.name,
      message: this.message,
      field: this.field,
      expected: this.expected,
      received: this.received,
      code: this.code,
      causes: this.causes.map((c) => c.toJSON()),
    };
  }

  /** Short one-line summary for toast/UI. */
  toShortString(): string {
    if (this.field) {
      return `${this.field}: ${this.message}`;
    }
    return this.message;
  }
}

export type ConfigValidationErrorCode =
  | 'SCHEMA_DRIFT'          // unexpected field or type mismatch
  | 'REQUIRED_FIELD_MISSING' // required field is null / undefined / empty string
  | 'INVALID_MODULE_TYPE'   // ZoneCreatorModuleType enum violation
  | 'CONTEXT_FILTER_BROKEN' // filter_entity / icon_entity points to non-existent field
  | 'SCHEMA_INTERNAL_ERROR' // schema itself is inconsistent (programming error)
  | 'UNKNOWN';              // fallback

// ── Field-level error accumulator ────────────────────────────────────────────

interface FieldValidationResult {
  ok: boolean;
  error?: ConfigValidationError;
  /** All field names that failed validation. */
  failedFields: string[];
  /** Sub-errors for each failed field. */
  causes: ConfigValidationError[];
}

/**
 * Validate a single field against its HaFormFieldSchema definition.
 * Returns an error with full type context.
 */
function validateFieldAgainstSchema(
  fieldName: string,
  fieldSchema: HaFormSchema & { type: string },
  rawValue: unknown,
): FieldValidationResult {
  const causes: ConfigValidationError[] = [];

  // Skip grid entries
  if (fieldSchema.type === 'grid') {
    return { ok: true, failedFields: [], causes: [] };
  }

  const received = receivedType(rawValue);

  // Required field: empty/null/undefined check
  if (fieldSchema.required) {
    if (
      rawValue === undefined ||
      rawValue === null ||
      (typeof rawValue === 'string' && rawValue.trim() === '')
    ) {
      return {
        ok: false,
        error: new ConfigValidationError(
          `Erforderliches Feld '${fieldName}' ist leer`,
          fieldName,
          describeExpectedType(fieldSchema),
          received,
          'REQUIRED_FIELD_MISSING',
        ),
        failedFields: [fieldName],
        causes: [],
      };
    }
  }

  // Type validation
  if (rawValue !== undefined && rawValue !== null) {
    if (!fieldValueMatchesType(fieldSchema, rawValue)) {
      return {
        ok: false,
        error: new ConfigValidationError(
          `Feld '${fieldName}' hat ungültigen Typ`,
          fieldName,
          describeExpectedType(fieldSchema),
          received,
          'SCHEMA_DRIFT',
        ),
        failedFields: [fieldName],
        causes: [],
      };
    }
  }

  return { ok: true, failedFields: [], causes: [] };
}

/**
 * Full config validation against a HaFormSchema[].
 * Accumulates all errors rather than failing on first.
 */
function validateConfigFields(
  config: Record<string, unknown>,
  schema: HaFormSchema[],
): FieldValidationResult {
  const allFailedFields: string[] = [];
  const allCauses: ConfigValidationError[] = [];

  for (const entry of schema) {
    if (entry.type === 'grid') continue;

    const fieldSchema = entry as HaFormSchema & { type: string };
    const rawValue = config[fieldSchema.name];

    const result = validateFieldAgainstSchema(fieldSchema.name, fieldSchema, rawValue);

    if (!result.ok && result.error) {
      allFailedFields.push(fieldSchema.name);
      allCauses.push(result.error);
    }
  }

  return {
    ok: allFailedFields.length === 0,
    failedFields: allFailedFields,
    causes: allCauses,
  };
}

/**
 * Check for unexpected keys in config that don't appear in schema.
 */
function detectUnexpectedFields(
  config: Record<string, unknown>,
  schema: HaFormSchema[],
): string[] {
  const schemaFieldNames = new Set(
    schema
      .filter((entry): entry is HaFormSchema & { name: string } => entry.type !== 'grid' && 'name' in entry)
      .map((entry) => entry.name),
  );

  const unexpected: string[] = [];
  for (const key of Object.keys(config)) {
    if (!schemaFieldNames.has(key)) {
      unexpected.push(key);
    }
  }
  return unexpected;
}

// ── Type description helpers ──────────────────────────────────────────────────

function receivedType(value: unknown): string {
  if (value === null) return 'null';
  if (value === undefined) return 'undefined';
  if (Array.isArray(value)) return 'array';
  return typeof value;
}

function describeExpectedType(field: HaFormSchema & { type: string }): string {
  if (field.type === 'grid') return 'grid';
  if (field.type === 'boolean') return 'boolean';
  if (field.type === 'number') return field.multiple ? 'number[]' : 'number';
  if (field.type === 'text') {
    if (field.multiple) return 'string[]';
    if ((field as { selector?: { text?: { multiline?: boolean } } }).selector?.text?.multiline) {
      return 'string | string[]';
    }
    return 'string';
  }
  return field.multiple ? 'string[]' : 'string';
}

function fieldValueMatchesType(
  field: HaFormSchema & { type: string },
  value: unknown,
): boolean {
  switch (field.type) {
    case 'boolean':
      return typeof value === 'boolean';
    case 'number':
      if (field.multiple) return Array.isArray(value) && value.every((v) => typeof v === 'number' && Number.isFinite(v));
      return typeof value === 'number' && Number.isFinite(value);
    case 'entity':
    case 'icon':
    case 'attribute':
    case 'array':
      if (field.multiple) return Array.isArray(value) && value.every((v) => typeof v === 'string');
      return typeof value === 'string';
    case 'text':
      if (field.multiple) return Array.isArray(value) && value.every((v) => typeof v === 'string');
      if ((field as { selector?: { text?: { multiline?: boolean } } }).selector?.text?.multiline) {
        return typeof value === 'string' || (Array.isArray(value) && value.every((v) => typeof v === 'string'));
      }
      return typeof value === 'string';
    default:
      return false;
  }
}

// ── Public API ───────────────────────────────────────────────────────────────

/**
 * Build a typed validator for a specific card schema.
 * The returned function throws ConfigValidationError on any schema drift.
 *
 * @example
 * const validate = buildConfigValidator(MY_CARD_SCHEMA);
 * validate(userSubmittedConfig); // throws or returns void
 *
 * @param schema - HaFormSchema[] from card-form-helper (PS-198)
 */
export function buildConfigValidator<T extends Record<string, unknown>>(
  schema: HaFormSchema[],
): (config: unknown) => asserts config is T {
  return function (config: unknown): asserts config is T {
    if (config === null || config === undefined || typeof config !== 'object') {
      throw new ConfigValidationError(
        'Konfiguration muss ein Objekt sein',
        undefined,
        'object',
        receivedType(config),
        'SCHEMA_DRIFT',
      );
    }

    const record = config as Record<string, unknown>;

    // 1. Check for unexpected fields (schema drift)
    const unexpected = detectUnexpectedFields(record, schema);
    if (unexpected.length > 0) {
      throw new ConfigValidationError(
        `Unbekannte Felder: ${unexpected.join(', ')}`,
        undefined,
        schemaFieldsSummary(schema),
        `unknown: ${unexpected.join(', ')}`,
        'SCHEMA_DRIFT',
        [],
      );
    }

    // 2. Validate via PS-198 helper (required fields, types, context filters)
    const ps198Valid = validateCardConfig(record, schema);
    if (!ps198Valid) {
      // Try to extract field-level errors from causes
      const fieldResult = validateConfigFields(record, schema);
      const topError = new ConfigValidationError(
        fieldResult.failedFields.length > 0
          ? `Validierungsfehler in: ${fieldResult.failedFields.join(', ')}`
          : 'Konfiguration entspricht nicht dem Schema',
        undefined,
        schemaFieldsSummary(schema),
        'object',
        'SCHEMA_DRIFT',
        fieldResult.causes,
      );
      throw topError;
    }

    // 3. Run any card-specific validation extensions
    const cardResult = validateConfigFields(record, schema);
    if (!cardResult.ok) {
      throw new ConfigValidationError(
        `Validierungsfehler in: ${cardResult.failedFields.join(', ')}`,
        undefined,
        schemaFieldsSummary(schema),
        'object',
        'SCHEMA_DRIFT',
        cardResult.causes,
      );
    }
  };
}

/**
 * Summarize schema field names for error messages.
 */
function schemaFieldsSummary(schema: HaFormSchema[]): string {
  const names = schema
    .filter((entry): entry is HaFormSchema & { name: string } => entry.type !== 'grid' && 'name' in entry)
    .map((entry) => entry.name);
  return names.length > 0 ? names.join(' | ') : 'unknown';
}

// ── Primary gate function ─────────────────────────────────────────────────────

/**
 * CI-equivalent validation gate.
 * Call this in every save/submit handler before sending data to the API.
 *
 * Integrates with:
 * - Card form helpers (PS-198) for schema-driven validation
 * - Zone editor API client for pre-submit zone saves
 * - Dashboard save handlers for inline edits
 *
 * @param config - Raw form / API payload to validate
 * @param schema - HaFormSchema[] (from card's ZONE_CREATOR_SCHEMA etc.)
 * @param cardName - Human-readable card name for error messages (e.g. 'StyxZoneCreator')
 * @throws ConfigValidationError on any drift
 *
 * @example
 * // In a save button handler:
 * try {
 *   const raw = getFormData();
 *   validateEditorSchema(raw, MY_CARD_SCHEMA, 'MyCard');
 *   await zoneEditorApi.createZone(raw);
 * } catch (err) {
 *   if (err instanceof ConfigValidationError) {
 *     showToast('Validierung fehlgeschlagen: ' + err.toShortString());
 *   }
 * }
 */
export function validateEditorSchema(
  config: unknown,
  schema: HaFormSchema[],
  cardName = 'Card',
): void {
  if (!schema || schema.length === 0) {
    throw new ConfigValidationError(
      `${cardName}: Kein Schema definiert — Validierung nicht möglich`,
      undefined,
      'HaFormSchema[]',
      receivedType(schema),
      'SCHEMA_INTERNAL_ERROR',
    );
  }

  if (config === null || config === undefined || typeof config !== 'object') {
    throw new ConfigValidationError(
      `${cardName}: Konfiguration muss ein Objekt sein`,
      undefined,
      'object',
      receivedType(config),
      'SCHEMA_DRIFT',
    );
  }

  const record = config as Record<string, unknown>;

  // Gate 1: unexpected fields
  const unexpected = detectUnexpectedFields(record, schema);
  if (unexpected.length > 0) {
    throw new ConfigValidationError(
      `${cardName}: Unbekannte Felder — mögliche Schema-Drift: ${unexpected.join(', ')}`,
      undefined,
      schemaFieldsSummary(schema),
      `extra: ${unexpected.join(', ')}`,
      'SCHEMA_DRIFT',
    );
  }

  // Gate 2: PS-198 validation pass
  if (!validateCardConfig(record, schema)) {
    const fieldResult = validateConfigFields(record, schema);
    const detail = fieldResult.failedFields.length > 0
      ? `Fehlgeschlagen: ${fieldResult.failedFields.join(', ')}`
      : 'Typ-/Pflichtfeld-Fehler';
    throw new ConfigValidationError(
      `${cardName}: ${detail}`,
      undefined,
      schemaFieldsSummary(schema),
      'object',
      'SCHEMA_DRIFT',
      fieldResult.causes,
    );
  }
}

// ── Integration helpers ──────────────────────────────────────────────────────

/**
 * Wrap a zone-editor API save operation with pre-validate.
 * Use this instead of calling zoneEditorApi.createZone / updateZone directly.
 *
 * @example
 * import { apiSaveWithValidation } from './editor-schema-validation.js';
 * await apiSaveWithValidation(
 *   zoneEditorApi.createZone.bind(zoneEditorApi),
 *   rawConfig,
 *   ZONE_CREATOR_SCHEMA,
 *   { name: rawConfig.zone_name },
 * );
 */
export async function apiSaveWithValidation<T extends Record<string, unknown>, R>(
  apiCall: (payload: T) => Promise<R>,
  rawConfig: unknown,
  schema: HaFormSchema[],
  payload: T,
  cardName = 'ZoneEditor',
): Promise<R> {
  // Browser-side gate — throws ConfigValidationError before any network call
  validateEditorSchema(rawConfig, schema, cardName);

  return apiCall(payload);
}

/**
 * Validate a partial config update (e.g. inline edit in dashboard grid).
 * Skips required-field checks for fields that are not being updated.
 */
export function validatePartialUpdate(
  currentConfig: Record<string, unknown>,
  partialUpdate: Partial<Record<string, unknown>>,
  schema: HaFormSchema[],
  cardName = 'Card',
): void {
  // Merge: apply partial, keep current for untouched fields
  const merged: Record<string, unknown> = { ...currentConfig, ...partialUpdate };

  // Validate merged config
  validateEditorSchema(merged, schema, cardName);
}

// ── Window export for non-module contexts ─────────────────────────────────────

declare global {
  interface Window {
    ConfigValidationError?: typeof ConfigValidationError;
    validateEditorSchema?: typeof validateEditorSchema;
    buildConfigValidator?: typeof buildConfigValidator;
    apiSaveWithValidation?: typeof apiSaveWithValidation;
  }
}

if (typeof window !== 'undefined') {
  window.ConfigValidationError = ConfigValidationError;
  window.validateEditorSchema = validateEditorSchema;
  window.buildConfigValidator = buildConfigValidator;
  window.apiSaveWithValidation = apiSaveWithValidation;
}
