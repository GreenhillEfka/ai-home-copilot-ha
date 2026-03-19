# PS-174 — Card Editor documentationURL Standard

## Overview
This document defines the `documentationURL` standard for all PilotSuite custom cards. Every card must expose a `documentationURL` in its `window.customCards` registration entry.

## Implementation

### Central Helper
All cards should use the central registration helper:

```typescript
import { registerCustomCard } from '../utils/card-registration';

registerCustomCard({
  type: 'styx-zone-creator-card',
  name: 'Styx Zone Creator',
  description: 'Create and manage Habitus zones',
  documentationURL: '/docs/cards/styx-zone-creator',
  icon: 'mdi:map-marker-radius',
});
```

### Default Behavior
If `documentationURL` is not provided, the helper defaults to:
- `/docs/cards/{card-type}` (internal docs path)

### URL Formats
Supported URL formats:
- **Internal:** `/docs/cards/*` (relative path to internal documentation)
- **External:** `https://github.com/.../wiki/*` (external repo wiki)
- **Absolute:** `https://docs.pilotsuite.io/cards/*` (external docs site)

## Affected Cards

### Core Cards
| Card Type | documentationURL | Status |
|-----------|------------------|--------|
| `styx-zone-creator-card` | `/docs/cards/styx-zone-creator` | ✅ Implemented |
| `module-config-editor` | `/docs/cards/module-config` | 🔄 Pending |
| `habitus-dashboard-card` | `/docs/cards/habitus-dashboard` | 🔄 Pending |

### Future Cards
All new cards must include `documentationURL` in their registration.

## Validation

### Runtime Check
The `card-registration.ts` helper auto-validates on module load:
- Logs warning for cards missing `documentationURL`
- Returns array of missing card types via `validateCardDocumentation()`

### Manual Verification
```typescript
// Check if card has documentationURL
const url = getCardDocumentationURL('styx-zone-creator-card');
console.log(url); // '/docs/cards/styx-zone-creator'

// Validate all cards
const missing = validateCardDocumentation();
console.log(missing); // [] if all OK
```

## Documentation Content

Each `documentationURL` should point to a page containing:
1. **Card Overview** — Purpose and use cases
2. **Configuration Options** — All available properties
3. **Examples** — YAML/JavaScript usage examples
4. **Troubleshooting** — Common issues and solutions
5. **API Reference** — Methods and events (if applicable)

## Migration Path

For existing cards without `documentationURL`:

1. **Phase 1:** Add `card-registration.ts` helper to codebase
2. **Phase 2:** Update each card to call `registerCustomCard()`
3. **Phase 3:** Create documentation pages for each card
4. **Phase 4:** Enable validation gate in build pipeline

## See Also

- PS-173: Module-Config-Editor HaFormSchema-Grid-Pattern
- PS-172: Styx-Zone-Creator-Card getConfigForm-HaFormSchema-Pattern
- PS-178: Area-to-Zone-Mapping-Registry

---
*Document Version: 1.0*
*Last Updated: 2026-03-19*
*PS-REL-031: card-documentation-url-standard*
