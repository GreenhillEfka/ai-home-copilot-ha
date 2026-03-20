# PS-173 — Module Config Editor HaFormSchema Grid Pattern

## Overview
This document defines the HaFormSchema Grid Pattern for the PilotSuite Module Config Editor. All module-per-zone configurations use this pattern for consistent, type-safe editing.

## Implementation

### Schema Builder
The `buildModuleConfigSchema()` function generates HaFormSchema arrays:

```typescript
import { buildModuleConfigSchema, ModuleType } from '../editors/module-config-editor';

const schema = buildModuleConfigSchema('wohnbereich', ['licht', 'bewegung', 'klima']);
```

### Grid Pattern
All module configs use `type: 'grid'` with `flatten: true`:

```typescript
{
  type: 'grid',
  name: 'modules',
  title: 'Module pro Zone',
  flatten: true,
}
```

### Selector Types
Supported selector types:

| Type | Selector | Use Case |
|------|----------|----------|
| `entity` | `{ entity: { filter: {...} } }` | Entity selection with domain/device_class filters |
| `boolean` | `{ boolean: {} }` | Toggle switches |
| `text` | `{ text: { multiline: boolean } }` | Text input (single/multi-line) |
| `icon` | `{ icon: { placeholder: string } }` | Icon picker |
| `attribute` | `{ attribute: { entity_id: string } }` | Entity attribute access |

### Context Filters
Context filters enable cross-field entity filtering:

```typescript
{
  type: 'attribute',
  name: 'zone_bewegung_timeout',
  selector: {
    attribute: {
      entity_id: 'zone_bewegung_sensor', // References another field
    },
  },
  context: {
    filter_entity: 'zone_bewegung_sensor',
  },
}
```

## Module Types

### Supported Modules
| Module | Entities | Config Fields |
|--------|----------|---------------|
| `licht` | light.* | Hauptlicht, Ambiente, Automatik |
| `bewegung` | binary_sensor.* (motion) | Sensor, Timeout |
| `musik` | media_player.* | Player, Playlist URL |
| `klima` | climate.*, sensor.* (temperature) | Thermostat, Sensor, Zieltemp |
| `kamera` | camera.* | Kamera, Aufnahme-Flag |
| `cover` | cover.* | Rolladen, Icon |

### Auto-Detection
Modules are auto-detected from zone entities:
```typescript
const modules = getAvailableModulesForZone(zone);
// Returns ['licht', 'bewegung'] based on zone.entities
```

## Validation

### Runtime Validation
```typescript
const valid = validateModuleConfig(config, schema);
if (!valid) {
  console.warn('Invalid module config');
}
```

### Required Fields
Fields marked `required: true` must be present in config.

## Integration

### Card Integration
Cards should use the schema builder:
```typescript
import { buildModuleConfigSchema } from '../editors/module-config-editor';

async getConfigForm() {
  const modules = getAvailableModulesForZone(this.zone);
  return buildModuleConfigSchema(this.zone.zone_id, modules, this.hass);
}
```

### Form Rendering
Home Assistant renders the grid schema automatically:
- Grid layout with `flatten: true`
- Entity pickers with filters
- Boolean toggles
- Text inputs

## Migration Path

For existing configs without HaFormSchema:

1. **Phase 1:** Add `module-config-editor.ts` schema builder
2. **Phase 2:** Update cards to call `buildModuleConfigSchema()`
3. **Phase 3:** Enable validation in config flows
4. **Phase 4:** Migrate legacy configs to new schema format

## See Also

- PS-174: Card-Editor-DocumentationURL-Standard
- PS-172: Styx-Zone-Creator-Card getConfigForm-HaFormSchema-Pattern
- PS-178: Area-to-Zone-Mapping-Registry

---
*Document Version: 1.0*
*Last Updated: 2026-03-19*
*PS-REL-033: module-config-haformschema*
