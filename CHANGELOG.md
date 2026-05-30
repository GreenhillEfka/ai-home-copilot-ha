# Changelog

## [20.0.8] - 2026-04-15

### Changed
- **BREAKING:** Domain renamed from `copilot_ha` to `pilotsuite` for consistency
- All internal imports updated to use `pilotsuite` namespace
- Version synchronized with PilotSuite Core (v20.0.8)

### Added
- Complete HACS integration structure
- manifest.json with domain: pilotsuite
- hacs.json for HACS discovery
- Comprehensive README.md

### Fixed
- Domain consistency across all files
- Import paths updated throughout codebase

### Migration Notes

**Upgrading from copilot_ha:**
1. Old entities will be automatically migrated
2. Entity IDs change from `sensor.copilot_ha_*` to `sensor.pilotsuite_*`
3. Update any automations referencing old entity IDs
4. Dashboard cards may need entity reference updates

---

## [1.0.0] - 2026-04-07

### Added
- Initial Platinum release
- 9 Lovelace cards
- Full sensor suite
- Config flow wizard

