/* PilotStack Zone Cards Bundle | Do not edit – built from TS sources */

// static/utils/card-form-helper.ts
function buildHaFormSchema(fields, options = {}) {
  const schema = [];
  schema.push({
    type: "grid",
    name: options.gridName ?? "card",
    title: options.gridTitle ?? "Card configuration",
    description: options.gridDescription,
    flatten: options.flatten ?? true
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
function isMissingFieldValue(field, value) {
  if (value === void 0 || value === null) {
    return true;
  }
  if (allowsStringArray(field) || isMultipleField(field)) {
    if (Array.isArray(value)) {
      return value.length === 0;
    }
  }
  if (typeof value === "string") {
    return value.trim() === "";
  }
  return false;
}
function isValidFieldValue(field, value) {
  switch (field.type) {
    case "boolean":
      return typeof value === "boolean";
    case "number":
      return isMultipleField(field) ? isNumberArray(value) : isFiniteNumber(value);
    case "entity":
    case "icon":
    case "attribute":
      return isMultipleField(field) ? isStringArray(value) : typeof value === "string";
    case "text":
      if (isMultipleField(field)) {
        return isStringArray(value);
      }
      if (allowsStringArray(field)) {
        return typeof value === "string" || isStringArray(value);
      }
      return typeof value === "string";
  }
}
function describeFieldValueType(field) {
  const multiple = isMultipleField(field);
  switch (field.type) {
    case "boolean":
      return "boolean";
    case "number":
      return multiple ? "number[]" : "number";
    case "entity":
    case "icon":
    case "attribute":
      return multiple ? "string[]" : "string";
    case "text":
      if (multiple) {
        return "string[]";
      }
      return allowsStringArray(field) ? "string | string[]" : "string";
  }
}
function assertFieldSchemaConsistency(field) {
  if (field.type === "boolean" && isMultipleField(field)) {
    throw new Error(`[PS-198] Field '${field.name}' cannot be both boolean and multiple`);
  }
  if (field.default !== void 0 && field.default !== null && !isValidFieldValue(field, field.default)) {
    throw new Error(
      `[PS-198] Field '${field.name}' default must be ${describeFieldValueType(field)}`
    );
  }
}
function buildHaFormFieldSchema(field) {
  const builtField = {
    type: field.type,
    name: field.name,
    title: field.title,
    description: field.description,
    required: field.required,
    default: field.defaultValue,
    selector: selectorForField(field),
    ...field.context ? { context: field.context } : {},
    ...isMultipleField(field) ? { multiple: true } : {}
  };
  assertFieldSchemaConsistency(builtField);
  return builtField;
}
function selectorForField(field) {
  switch (field.type) {
    case "entity":
      return {
        entity: {
          filter: {
            ...field.domain ? { domain: field.domain } : {},
            ...field.deviceClass ? { device_class: field.deviceClass } : {}
          }
        }
      };
    case "boolean":
      return {
        boolean: {}
      };
    case "text":
      return {
        text: {
          ...field.multiline ? { multiline: true } : {}
        }
      };
    case "number":
      return {
        number: {
          ...field.min !== void 0 ? { min: field.min } : {},
          ...field.max !== void 0 ? { max: field.max } : {},
          ...field.step !== void 0 ? { step: field.step } : {}
        }
      };
    case "icon":
      return {
        icon: {
          ...field.iconPlaceholder ? { placeholder: field.iconPlaceholder } : {}
        }
      };
    case "attribute": {
      const entityId = resolveAttributeEntityId(field.attributeEntityId);
      return {
        attribute: {
          ...entityId ? { entity_id: entityId } : {}
        }
      };
    }
  }
}
function resolveAttributeEntityId(attributeEntityId) {
  return normalizeNonEmptyString(attributeEntityId);
}
function isMultipleField(field) {
  if (field.multiple !== void 0) {
    return field.multiple;
  }
  if ("defaultValue" in field) {
    return Array.isArray(field.defaultValue);
  }
  return Array.isArray(field.default);
}
function allowsStringArray(field) {
  return field.type === "text" && field.selector.text?.multiline === true;
}
function isFiniteNumber(value) {
  return typeof value === "number" && Number.isFinite(value);
}
function isStringArray(value) {
  return Array.isArray(value) && value.every((item) => typeof item === "string");
}
function isNumberArray(value) {
  return Array.isArray(value) && value.every((item) => isFiniteNumber(item));
}
function normalizeNonEmptyString(value) {
  return typeof value === "string" && value.trim() !== "" ? value : void 0;
}
function isFieldSchema(field) {
  return field.type !== void 0 && field.selector !== void 0;
}

// static/utils/editor-schema-validation.ts
var ConfigValidationError = class extends Error {
  constructor(message, field, expectedType, actualType) {
    super(message);
    this.field = field;
    this.expectedType = expectedType;
    this.actualType = actualType;
    this.name = "ConfigValidationError";
  }
};
function validateEditorSchema(config, schema, options = {}) {
  if (!config || typeof config !== "object") {
    throw new ConfigValidationError(
      "Config must be a non-null object",
      void 0,
      "object",
      typeof config
    );
  }
  const { strict = false, allowedExtraFields = [] } = options;
  const formFields = schema.filter(
    (entry) => entry.type !== "grid"
  );
  const fieldMap = new Map(
    formFields.map((f) => [f.name, f])
  );
  validateFieldDefinitions(formFields);
  for (const field of formFields) {
    if (field.required) {
      const value = config[field.name];
      if (isMissingFieldValue(field, value)) {
        throw new ConfigValidationError(
          `Required field '${field.name}' is missing or empty`,
          field.name,
          "present",
          String(value)
        );
      }
    }
  }
  for (const [fieldName, fieldValue] of Object.entries(config)) {
    const fieldSchema = fieldMap.get(fieldName);
    if (!fieldSchema) {
      if (strict && !allowedExtraFields.includes(fieldName)) {
        throw new ConfigValidationError(
          `Unexpected field '${fieldName}' in strict mode`,
          fieldName,
          "not present",
          "present"
        );
      }
      continue;
    }
    validateFieldType(fieldName, fieldValue, fieldSchema);
  }
  validateContextReferences(formFields, fieldMap);
}
function validateFieldType(fieldName, value, schema) {
  if (!schema.required && (value === void 0 || value === null)) {
    return;
  }
  if (!isValidFieldValue(schema, value)) {
    throw new ConfigValidationError(
      `Field '${fieldName}' must be ${describeFieldValueType(schema)}`,
      fieldName,
      describeFieldValueType(schema),
      describeActualValueType(value)
    );
  }
}
function validateFieldDefinitions(formFields) {
  for (const field of formFields) {
    try {
      assertFieldSchemaConsistency(field);
    } catch (error) {
      throw new ConfigValidationError(
        error instanceof Error ? error.message : String(error),
        field.name,
        describeFieldValueType(field),
        describeActualValueType(field.default)
      );
    }
  }
}
function validateContextReferences(formFields, fieldMap) {
  for (const field of formFields) {
    if (!field.context) {
      continue;
    }
    const { filter_entity: filterEntity, icon_entity: iconEntity } = field.context;
    if (filterEntity && !fieldMap.has(filterEntity)) {
      throw new ConfigValidationError(
        `Field '${field.name}' references non-existent context field '${filterEntity}'`,
        field.name,
        "valid context reference",
        `missing '${filterEntity}'`
      );
    }
    if (filterEntity && field.type === "attribute") {
      const referencedField = fieldMap.get(filterEntity);
      if (referencedField && referencedField.type !== "entity") {
        throw new ConfigValidationError(
          `Field '${field.name}' requires filter_entity '${filterEntity}' to reference an entity field`,
          field.name,
          "entity context reference",
          referencedField.type
        );
      }
    }
    if (iconEntity && !fieldMap.has(iconEntity)) {
      throw new ConfigValidationError(
        `Field '${field.name}' references non-existent context field '${iconEntity}'`,
        field.name,
        "valid context reference",
        `missing '${iconEntity}'`
      );
    }
  }
}
function describeActualValueType(value) {
  if (Array.isArray(value)) {
    if (value.every((item) => typeof item === "string")) {
      return "string[]";
    }
    if (value.every((item) => typeof item === "number" && Number.isFinite(item))) {
      return "number[]";
    }
    return "array";
  }
  if (value === null) {
    return "null";
  }
  return typeof value;
}
function buildConfigValidator(schema, options) {
  return (config) => {
    validateEditorSchema(config, schema, options);
  };
}

// static/utils/card-registration.ts
function registerCustomCard(card) {
  if (!card.documentationURL) {
    card.documentationURL = `/docs/cards/${card.type.replace(/-card$/, "")}`;
  }
  if (!card.documentationURL.startsWith("http") && !card.documentationURL.startsWith("/")) {
    console.warn(`[PS-174] Invalid documentationURL for ${card.type}: ${card.documentationURL}`);
    card.documentationURL = `/docs/cards/${card.type}`;
  }
  if (!window.customCards) {
    window.customCards = [];
  }
  const customCards = window.customCards;
  const existing = customCards.find((registeredCard) => registeredCard.type === card.type);
  if (existing) {
    Object.assign(existing, card);
    console.log(`[PS-174] Updated card registration: ${card.type}`);
  } else {
    customCards.push(card);
    console.log(`[PS-174] Registered card: ${card.type} \u2192 ${card.documentationURL}`);
  }
}
function validateCardDocumentation() {
  const missing = [];
  window.customCards?.forEach((registeredCard) => {
    if (!registeredCard.documentationURL) {
      missing.push(registeredCard.type);
    }
  });
  if (missing.length > 0) {
    console.warn(`[PS-174] ${missing.length} cards missing documentationURL:`, missing);
  }
  return missing;
}
if (typeof window !== "undefined" && window.customCards) {
  validateCardDocumentation();
}

// static/cards/styx-zone-creator-card.ts
var ZONE_CREATOR_MODULE_TYPES = [
  "LIGHT",
  "AUDIO",
  "CLIMATE",
  "COVER",
  "ENERGY",
  "SCENE",
  "SECURITY"
];
var ZONE_IDENTITY_FIELDS = [
  {
    name: "zone_name",
    type: "text",
    title: "Zonen-Name",
    description: "Name der Zone",
    required: true
  },
  {
    name: "zone_icon",
    type: "icon",
    title: "Zonen-Icon",
    description: "Icon f\xFCr die Zone",
    required: false,
    defaultValue: "mdi:room"
  }
];
var ACTIVE_MODULES_FIELD = {
  name: "active_modules",
  type: "text",
  title: "Aktive Module",
  description: `Aktivierte Module (kommasepariert): ${ZONE_CREATOR_MODULE_TYPES.join(", ")}`,
  required: false,
  defaultValue: "LIGHT"
};
var DISPLAY_FIELDS = [
  {
    name: "show_grid",
    type: "boolean",
    title: "Grid anzeigen",
    description: "Zeige Grid-Layout f\xFCr Module",
    required: false,
    defaultValue: true
  },
  {
    name: "compact_mode",
    type: "boolean",
    title: "Kompakt-Modus",
    description: "Reduzierte Darstellung",
    required: false,
    defaultValue: false
  }
];
var LIGHT_FIELDS = [
  {
    name: "light_entity",
    type: "entity",
    title: "Licht-Entity",
    description: "Licht-Entity f\xFCr diese Zone",
    required: false,
    domain: ["light"]
  },
  {
    name: "light_filter_entity",
    type: "entity",
    title: "Licht-Filter",
    description: "Entity deren Status die Licht-Auswahl beeinflusst",
    required: false,
    domain: ["input_boolean", "binary_sensor"],
    context: { filter_entity: "light_entity" }
  }
];
var AUDIO_FIELDS = [
  {
    name: "audio_entity",
    type: "entity",
    title: "Audio-Entity",
    description: "Media Player f\xFCr Musik-Wiedergabe",
    required: false,
    domain: ["media_player"],
    deviceClass: ["speaker"]
  }
];
var CLIMATE_FIELDS = [
  {
    name: "climate_entity",
    type: "entity",
    title: "Klima-Entity",
    description: "Thermostat / Klima-Entity f\xFCr diese Zone",
    required: false,
    domain: ["climate"]
  },
  {
    name: "climate_filter_entity",
    type: "entity",
    title: "Klima-Filter",
    description: "Entity deren Status die Klima-Auswahl beeinflusst",
    required: false,
    domain: ["input_boolean", "binary_sensor", "sensor"],
    context: { filter_entity: "climate_entity" }
  }
];
var COVER_FIELDS = [
  {
    name: "cover_entity",
    type: "entity",
    title: "Cover-Entity",
    description: "Rolll\xE4den / Markisen f\xFCr diese Zone",
    required: false,
    domain: ["cover"]
  },
  {
    name: "cover_filter_entity",
    type: "entity",
    title: "Cover-Filter",
    description: "Entity deren Status die Cover-Auswahl beeinflusst",
    required: false,
    domain: ["input_boolean", "binary_sensor"],
    context: { filter_entity: "cover_entity" }
  }
];
var ENERGY_FIELDS = [
  {
    name: "energy_entity",
    type: "entity",
    title: "Energie-Entity",
    description: "Energie- / Stromsensor f\xFCr diese Zone",
    required: false,
    domain: ["sensor"],
    deviceClass: ["power", "energy"]
  }
];
var SCENE_FIELDS = [
  {
    name: "scene_entity",
    type: "entity",
    title: "Szenen-Entity",
    description: "Szene-Entity f\xFCr diese Zone",
    required: false,
    domain: ["scene"]
  }
];
var SECURITY_FIELDS = [
  {
    name: "security_entity",
    type: "entity",
    title: "Sicherheits-Entity",
    description: "Alarm / Sensor-Entity (T\xFCr, Bewegung, Smoke)",
    required: false,
    domain: ["alarm_control_panel", "binary_sensor", "sensor"],
    deviceClass: ["motion", "opening", "smoke", "gas"]
  }
];
var MODULE_FIELDS = {
  LIGHT: LIGHT_FIELDS,
  AUDIO: AUDIO_FIELDS,
  CLIMATE: CLIMATE_FIELDS,
  COVER: COVER_FIELDS,
  ENERGY: ENERGY_FIELDS,
  SCENE: SCENE_FIELDS,
  SECURITY: SECURITY_FIELDS
};
var ALL_MODULE_FIELDS = [...ZONE_CREATOR_MODULE_TYPES].flatMap(
  (mt) => MODULE_FIELDS[mt]
);
var ZONE_CREATOR_SCHEMA = buildHaFormSchema(
  [...ZONE_IDENTITY_FIELDS, ACTIVE_MODULES_FIELD, ...ALL_MODULE_FIELDS, ...DISPLAY_FIELDS],
  {
    gridName: "zone-creator",
    gridTitle: "Zone Creator",
    gridDescription: "Konfiguriere eine Zone mit bis zu 7 modularen Komponenten",
    flatten: true
  }
);
var VALID_MODULE_TYPE_SET = new Set(ZONE_CREATOR_MODULE_TYPES);
function parseAndValidateActiveModules(raw) {
  if (typeof raw === "string") {
    return raw.split(",").map((s) => s.trim().toUpperCase()).filter((s) => VALID_MODULE_TYPE_SET.has(s));
  }
  if (Array.isArray(raw)) {
    const modules = [];
    for (const item of raw) {
      if (typeof item !== "string" || !VALID_MODULE_TYPE_SET.has(item)) {
        throw new ConfigValidationError(
          `Ung\xFCltiger Modultyp '${item}'. Erlaubt: ${ZONE_CREATOR_MODULE_TYPES.join(", ")}`,
          "active_modules",
          "ZoneCreatorModuleType",
          typeof item
        );
      }
      modules.push(item);
    }
    return modules;
  }
  throw new ConfigValidationError(
    "active_modules muss ein String (kommasepariert) oder Array sein",
    "active_modules",
    "string | ZoneCreatorModuleType[]",
    typeof raw
  );
}
var validateZoneCreatorConfig = buildConfigValidator(ZONE_CREATOR_SCHEMA);
var StyxZoneCreatorCard = class extends HTMLElement {
  static get type() {
    return "styx-zone-creator";
  }
  static get documentationURL() {
    return "https://pilotsuite.io/docs/cards/zone-creator";
  }
  /**
   * HA-PR #16142 (2025-02): Returns the card config form schema.
   * Pure schema — no core logic, no state, no API calls.
   */
  static async getConfigForm() {
    return ZONE_CREATOR_SCHEMA;
  }
  static getStubConfig() {
    return {
      zone_name: "Neue Zone",
      zone_icon: "mdi:room",
      active_modules: "LIGHT",
      show_grid: true,
      compact_mode: false
    };
  }
  /**
   * Validate a config object against the card schema and module enum.
   * Core zone logic (CRUD, activation, routing) lives in Styx backend — NOT here.
   */
  static validateConfig(config) {
    validateZoneCreatorConfig(config);
    const cfg = config;
    parseAndValidateActiveModules(cfg?.active_modules);
  }
};
registerCustomCard({
  type: StyxZoneCreatorCard.type,
  name: "Styx Zone Creator",
  description: "Erstelle und konfiguriere Zonen mit bis zu 7 modularen Komponenten",
  documentationURL: StyxZoneCreatorCard.documentationURL,
  preview: true,
  default: StyxZoneCreatorCard.getStubConfig()
});

// static/cards/habitus-brain-card.ts
var BRAIN_CARD_FIELDS = [
  // --- Header ---
  {
    name: "title",
    type: "text",
    title: "Titel",
    description: "Titel der Brain-View Karte",
    required: true,
    defaultValue: "Brain View"
  },
  {
    name: "subtitle",
    type: "text",
    title: "Untertitel",
    description: "Optionaler Untertitel",
    required: false
  },
  // --- Zone Aggregation ---
  {
    name: "show_zone_aggregation",
    type: "boolean",
    title: "Zone-Aggregation anzeigen",
    description: "Aggregierte Zone-Zust\xE4nde im Header zeigen",
    required: false,
    defaultValue: true
  },
  {
    name: "zones",
    type: "text",
    title: "Zonen-Filter",
    description: "Zu \xFCberwachende Zonen (Mehrfachfeld, leer = alle)",
    required: false,
    multiple: true
  },
  {
    name: "aggregation_window",
    type: "text",
    title: "Aggregations-Intervall",
    description: "Update-Fenster: 5s | 30s | 5m",
    required: false,
    defaultValue: "30s"
  },
  {
    name: "show_stale_indicator",
    type: "boolean",
    title: "Stale-Indikator",
    description: "Zeige Warnung bei veralteten Daten",
    required: false,
    defaultValue: true
  },
  {
    name: "stale_threshold_seconds",
    type: "number",
    title: "Stale-Schwelle (Sekunden)",
    description: "Ab wann gelten Daten als veraltet",
    required: false,
    defaultValue: 60,
    min: 0,
    step: 1
  },
  // --- Module Status ---
  {
    name: "show_module_status",
    type: "boolean",
    title: "Modul-Status anzeigen",
    description: "Aktive Module als Status-Chips zeigen",
    required: false,
    defaultValue: true
  },
  {
    name: "monitored_modules",
    type: "attribute",
    title: "Monitorierte Module",
    description: "Light, Musik, Klima, Cover, Energie, Szene, Sicherheit",
    required: false,
    defaultValue: ["light", "climate", "music", "security"],
    multiple: true
  },
  {
    name: "show_module_health",
    type: "boolean",
    title: "Modul-Gesundheit",
    description: "Konsistenz-Score pro Modul anzeigen",
    required: false,
    defaultValue: true
  },
  {
    name: "show_module_confidence",
    type: "boolean",
    title: "Modul-Konfidenz",
    description: "Konfidenz-Score pro Modul anzeigen",
    required: false,
    defaultValue: true
  },
  // --- Mood Panels ---
  {
    name: "enable_mood_panel",
    type: "boolean",
    title: "Mood-Panel aktivieren",
    description: "Emotionales Zustandsmonitoring aktivieren",
    required: false,
    defaultValue: true
  },
  {
    name: "mood_panel_position",
    type: "text",
    title: "Mood-Panel Position",
    description: "top | bottom | sidebar",
    required: false,
    defaultValue: "top"
  },
  {
    name: "show_mood_valence",
    type: "boolean",
    title: "Mood-Valenz",
    description: "Positiv / Neutral / Negativ anzeigen",
    required: false,
    defaultValue: true
  },
  {
    name: "show_mood_activation",
    type: "boolean",
    title: "Mood-Aktivierung",
    description: "Ruhig / Moderat / Geladen anzeigen",
    required: false,
    defaultValue: true
  },
  {
    name: "show_mood_stability",
    type: "boolean",
    title: "Mood-Stabilit\xE4t",
    description: "Stabil / Wechselnd / Instabil anzeigen",
    required: false,
    defaultValue: true
  },
  {
    name: "show_mood_history",
    type: "boolean",
    title: "Mood-Historie",
    description: "Verlauf der letzten N Stunden zeigen",
    required: false,
    defaultValue: true
  },
  {
    name: "show_mood_factors",
    type: "boolean",
    title: "Mood-Faktoren",
    description: "Top-Contributor zum aktuellen Mood anzeigen",
    required: false,
    defaultValue: true
  },
  {
    name: "mood_history_hours",
    type: "number",
    title: "Mood-Historie (Stunden)",
    description: "Wie viele Stunden zur\xFCckschauen",
    required: false,
    defaultValue: 24,
    min: 1,
    step: 1
  },
  // --- Brain-View Display ---
  {
    name: "view_mode",
    type: "text",
    title: "Ansichtsmodus",
    description: "live | trend | drift",
    required: false,
    defaultValue: "live"
  },
  {
    name: "show_predictions",
    type: "boolean",
    title: "Vorhersagen",
    description: "Pr\xE4diktions-Overlays auf Knoten anzeigen",
    required: false,
    defaultValue: false
  },
  {
    name: "show_causal_breadcrumbs",
    type: "boolean",
    title: "Kausale Breadcrumbs",
    description: "Explainability-Pfad anzeigen (Ausl\xF6ser \u2192 Wirkung \u2192 Ergebnis)",
    required: false,
    defaultValue: true
  },
  {
    name: "incident_lens_mode",
    type: "boolean",
    title: "Incident-Lens Modus",
    description: "Fokusmodus bei Alarmzust\xE4nden (reduzierte visuelle Last)",
    required: false,
    defaultValue: false
  },
  // --- Real-Time Aggregation ---
  {
    name: "show_data_freshness",
    type: "boolean",
    title: "Daten-Frische",
    description: "Zeitstempel und Freshness-Indikator anzeigen",
    required: false,
    defaultValue: true
  },
  {
    name: "show_uncertainty_fog",
    type: "boolean",
    title: "Unsicherheits-Nebel",
    description: "Visuell unscharf bei niedriger Konfidenz",
    required: false,
    defaultValue: true
  },
  {
    name: "batch_updates",
    type: "boolean",
    title: "Batch-Updates",
    description: "Updates b\xFCndeln statt einzeln rendern",
    required: false,
    defaultValue: true
  },
  {
    name: "show_zone_match",
    type: "boolean",
    title: "Zone-Match",
    description: "Heat-Layer: passt aktueller Zustand zu gewohnten Mustern?",
    required: false,
    defaultValue: false
  },
  // --- Layout ---
  {
    name: "compact_mode",
    type: "boolean",
    title: "Kompakt-Modus",
    description: "Reduzierte Darstellung",
    required: false,
    defaultValue: false
  },
  {
    name: "show_actions",
    type: "boolean",
    title: "Aktionen anzeigen",
    description: "Quick-Action Buttons anzeigen",
    required: false,
    defaultValue: true
  }
];
var BRAIN_CARD_SCHEMA = buildHaFormSchema(BRAIN_CARD_FIELDS, {
  gridName: "brain",
  gridTitle: "Brain View",
  gridDescription: "Interaktiver Wissensraum mit Zone-Aggregation, Module-Status und Mood-Panels",
  flatten: true
});
var validateHabitusBrainCardConfig = buildConfigValidator(BRAIN_CARD_SCHEMA);
var HabitusBrainCard = class extends HTMLElement {
  static get type() {
    return "habitus-brain";
  }
  static get documentationURL() {
    return "https://pilotsuite.io/docs/cards/brain-view";
  }
  static async getConfigForm() {
    return BRAIN_CARD_SCHEMA;
  }
  static getStubConfig() {
    return {
      title: "Brain View",
      subtitle: "System-\xDCbersicht",
      show_zone_aggregation: true,
      aggregation_window: "30s",
      show_stale_indicator: true,
      stale_threshold_seconds: 60,
      show_module_status: true,
      monitored_modules: ["light", "climate", "music", "security"],
      show_module_health: true,
      show_module_confidence: true,
      enable_mood_panel: true,
      mood_panel_position: "top",
      show_mood_valence: true,
      show_mood_activation: true,
      show_mood_stability: true,
      show_mood_history: true,
      show_mood_factors: true,
      mood_history_hours: 24,
      view_mode: "live",
      show_predictions: false,
      show_causal_breadcrumbs: true,
      incident_lens_mode: false,
      show_data_freshness: true,
      show_uncertainty_fog: true,
      batch_updates: true,
      show_zone_match: false,
      compact_mode: false,
      show_actions: true
    };
  }
  static validateConfig(config) {
    validateHabitusBrainCardConfig(config);
  }
};
registerCustomCard({
  type: HabitusBrainCard.type,
  name: "Habitus Brain View",
  description: "Interaktiver Wissensraum mit Zone-Aggregation, Module-Status und Mood-Panels",
  documentationURL: HabitusBrainCard.documentationURL,
  preview: true,
  default: HabitusBrainCard.getStubConfig()
});

// static/cards/zone-module-editor-card.ts
var ZONE_MODULE_TYPES = [
  "LIGHT",
  "AUDIO",
  "CLIMATE",
  "COVER",
  "ENERGY",
  "SCENE",
  "SECURITY"
];
var BASE_FIELDS = [
  {
    name: "zone_id",
    type: "text",
    title: "Zone-ID",
    description: "Zonen-ID aus dem Core/Zone-Store",
    required: true
  },
  {
    name: "zone_name",
    type: "text",
    title: "Zonen-Name",
    description: "Lesbarer Anzeigename der Zone",
    required: false
  },
  {
    name: "module_type",
    type: "text",
    title: "Modultyp",
    description: "Erlaubt: LIGHT, AUDIO, CLIMATE, COVER, ENERGY, SCENE, SECURITY",
    required: true,
    defaultValue: "LIGHT"
  },
  {
    name: "show_grid",
    type: "boolean",
    title: "Grid anzeigen",
    description: "Grid-Layout f\xFCr die Modulform verwenden",
    required: false,
    defaultValue: true
  },
  {
    name: "compact_mode",
    type: "boolean",
    title: "Kompaktmodus",
    description: "Formularfelder kompakt darstellen",
    required: false,
    defaultValue: false
  },
  // --- Secondary Zone States (PS-165/PS-137) ---
  {
    name: "dark",
    type: "boolean",
    title: "\u{1F319} Dunkel-Modus",
    description: "Zone dunkel (Lichtsensor/Sonne unter Schwelle)",
    required: false,
    defaultValue: false
  },
  {
    name: "sleep",
    type: "boolean",
    title: "\u{1F634} Sleep-Modus",
    description: "Zone im Sleep (manueller Switch-Override)",
    required: false,
    defaultValue: false
  },
  {
    name: "extended",
    type: "boolean",
    title: "\u23F1 Extended",
    description: "Zone hat Zeitlimit \xFCberschritten",
    required: false,
    defaultValue: false
  }
];
var LIGHT_FIELDS2 = [
  {
    name: "light_entity",
    type: "entity",
    title: "Licht-Entity",
    description: "Licht-Entity f\xFCr diese Zone",
    required: false,
    domain: ["light"]
  },
  {
    name: "light_filter_entity",
    type: "entity",
    title: "Licht-Filter",
    description: "Filter-Entity f\xFCr Licht-Filterung",
    required: false,
    domain: ["input_boolean", "binary_sensor"],
    context: { filter_entity: "light_filter_entity" }
  }
];
var AUDIO_FIELDS2 = [
  {
    name: "audio_entity",
    type: "entity",
    title: "Audio-Entity",
    description: "Media-Player f\xFCr Musik/Wiedergabe",
    required: false,
    domain: ["media_player"],
    deviceClass: ["speaker"]
  }
];
var CLIMATE_FIELDS2 = [
  {
    name: "climate_entity",
    type: "entity",
    title: "Klima-Entity",
    description: "Thermostat/Klimaanlage f\xFCr diese Zone",
    required: false,
    domain: ["climate"]
  },
  {
    name: "climate_filter_entity",
    type: "entity",
    title: "Klima-Filter",
    description: "Filter-Entity f\xFCr temperaturbezogene Auswahl",
    required: false,
    domain: ["input_boolean", "binary_sensor", "sensor"],
    context: { filter_entity: "climate_filter_entity" }
  }
];
var COVER_FIELDS2 = [
  {
    name: "cover_entity",
    type: "entity",
    title: "Cover-Entity",
    description: "Rollladen/Markise-Entity f\xFCr diese Zone",
    required: false,
    domain: ["cover"]
  },
  {
    name: "cover_filter_entity",
    type: "entity",
    title: "Cover-Filter",
    description: "Filter-Entity f\xFCr Cover-Auswahl",
    required: false,
    domain: ["input_boolean", "binary_sensor"],
    context: { filter_entity: "cover_filter_entity" }
  }
];
var ENERGY_FIELDS2 = [
  {
    name: "energy_entity",
    type: "entity",
    title: "Energie-Entity",
    description: "Energie-/Stromsensor f\xFCr diese Zone",
    required: false,
    domain: ["sensor"],
    deviceClass: ["power", "energy"]
  }
];
var SCENE_FIELDS2 = [
  {
    name: "scene_entity",
    type: "entity",
    title: "Szenen-Entity",
    description: "Szene-Entity f\xFCr diese Zone",
    required: false,
    domain: ["scene"]
  }
];
var SECURITY_FIELDS2 = [
  {
    name: "security_entity",
    type: "entity",
    title: "Sicherheits-Entity",
    description: "Alarm-/Sensor-Entity (z. B. T\xFCr, Bewegung, Smoke)",
    required: false,
    domain: ["alarm_control_panel", "binary_sensor", "sensor"],
    deviceClass: ["motion", "opening", "smoke", "gas"]
  }
];
var MODULE_CONFIG_FIELDS = {
  LIGHT: LIGHT_FIELDS2,
  AUDIO: AUDIO_FIELDS2,
  CLIMATE: CLIMATE_FIELDS2,
  COVER: COVER_FIELDS2,
  ENERGY: ENERGY_FIELDS2,
  SCENE: SCENE_FIELDS2,
  SECURITY: SECURITY_FIELDS2
};
var FIELD_ORDER = [...ZONE_MODULE_TYPES];
var ALL_MODULE_FIELDS2 = FIELD_ORDER.flatMap((moduleType) => MODULE_CONFIG_FIELDS[moduleType]);
var ZONE_MODULE_EDITOR_SCHEMA = buildHaFormSchema(
  [...BASE_FIELDS, ...ALL_MODULE_FIELDS2],
  {
    gridName: "zone-module-editor",
    gridTitle: "Zone Module Editor",
    gridDescription: "Konfiguriere Zone-Module in 7 Typen",
    flatten: true
  }
);
var VALID_MODULE_TYPE_SET2 = new Set(ZONE_MODULE_TYPES);
function assertModuleType(value) {
  if (typeof value !== "string" || !VALID_MODULE_TYPE_SET2.has(value)) {
    throw new ConfigValidationError(
      `Ung\xFCltiger Modultyp '${String(value)}'. Erlaubt sind: ${ZONE_MODULE_TYPES.join(", ")}`,
      "module_type",
      `'${ZONE_MODULE_TYPES.join("|")}'`,
      typeof value
    );
  }
}
var validateZoneModuleEditorConfig = buildConfigValidator(ZONE_MODULE_EDITOR_SCHEMA);
var ZoneModuleEditorCard = class extends HTMLElement {
  static get type() {
    return "zone-module-editor";
  }
  static get documentationURL() {
    return "https://pilotsuite.io/docs/cards/zone-module-editor";
  }
  static async getConfigForm() {
    return ZONE_MODULE_EDITOR_SCHEMA;
  }
  static getStubConfig() {
    return {
      zone_id: "zone_living",
      zone_name: "Neue Zone",
      module_type: "LIGHT",
      show_grid: true,
      compact_mode: false,
      dark: false,
      sleep: false,
      extended: false
    };
  }
  /**
   * Validate a config object against the editor schema and enum constraints.
   */
  static validateConfig(config) {
    validateZoneModuleEditorConfig(config);
    const cfg = config;
    assertModuleType(cfg?.module_type);
  }
};
registerCustomCard({
  type: ZoneModuleEditorCard.type,
  name: "Zone Module Editor",
  description: "Konfiguriere Module je Zone (LIGHT, AUDIO, CLIMATE, COVER, ENERGY, SCENE, SECURITY)",
  documentationURL: ZoneModuleEditorCard.documentationURL,
  preview: true,
  default: ZoneModuleEditorCard.getStubConfig()
});
export {
  HabitusBrainCard,
  StyxZoneCreatorCard,
  ZoneModuleEditorCard
};
