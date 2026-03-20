# PS-180 — Zone Taxonomy Specification

## Overview
This document defines the canonical zone taxonomy for PilotSuite smart home deployments. Zones provide the semantic boundary between physical spaces (areas) and logical automation scopes.

## Hierarchy Levels

### Level 1: Zone (Highest)
A **Zone** represents a logical automation boundary that may span multiple physical areas.

**Attributes:**
- `zone_id`: Unique identifier (e.g., `climate_north`, `security_perimeter`)
- `zone_type`: Classification (`climate`, `security`, `lighting`, `energy`, `comfort`)
- `priority`: Automation priority (0-10, 10 = highest)
- `active`: Boolean flag for runtime activation

**Examples:**
- `climate_zones`: Heating/cooling boundaries
- `security_zones`: Alarm/motion detection perimeters
- `lighting_zones`: Scene-based lighting groups

### Level 2: Area (Physical)
An **Area** represents a physical space within a Zone.

**Attributes:**
- `area_id`: Home Assistant area ID
- `zone_id`: Parent zone reference
- `floor`: Floor level (optional)
- `square_meters`: Approximate area size

**Examples:**
- `living_room` → `comfort_zone`
- `kitchen` → `energy_zone`
- `hallway` → `security_zone`

### Level 3: Entity (Device)
An **Entity** is a Home Assistant entity assigned to an Area.

**Attributes:**
- `entity_id`: HA entity ID (e.g., `light.living_room_main`)
- `area_id`: Parent area reference
- `entity_type`: Device type (`light`, `sensor`, `switch`, `climate`)
- `zone_id`: Inherited from area

## Mapping Registry

The Area→Zone mapping is stored in `/config/clawd/team/repos/pilotsuite-styx-ha/custom_components/copilot_ha/core/zone_mapping.json`:

```json
{
  "version": 1,
  "mappings": [
    {
      "area_id": "living_room",
      "zone_id": "comfort_zone",
      "zone_type": "comfort",
      "priority": 7
    },
    {
      "area_id": "kitchen",
      "zone_id": "energy_zone",
      "zone_type": "energy",
      "priority": 5
    }
  ]
}
```

## Zone Types Reference

| Type | Description | Typical Entities | Priority Range |
|------|-------------|------------------|----------------|
| `climate` | HVAC boundaries | `climate.*`, `sensor.temperature` | 8-10 |
| `security` | Alarm/motion perimeters | `binary_sensor.*`, `alarm_control_panel` | 9-10 |
| `lighting` | Scene-based groups | `light.*`, `scene.*` | 4-6 |
| `energy` | Power monitoring | `sensor.power`, `switch.*` | 5-7 |
| `comfort` | Quality of life | `cover.*`, `fan.*`, `light.*` | 3-6 |

## Validation Rules

1. **Zone Uniqueness:** Each `zone_id` must be unique across the deployment
2. **Area Assignment:** Every Area must belong to exactly one Zone
3. **Entity Inheritance:** Entities inherit `zone_id` from their parent Area
4. **Priority Bounds:** Priority must be 0-10 (integer)
5. **Type Enumeration:** `zone_type` must be from the reference table

## Runtime Behavior

### Zone Activation
- Zones can be activated/deactivated at runtime
- Deactivated zones skip automation triggers
- State is preserved for reactivation

### Cross-Zone Conflicts
- Higher priority zones override lower priority zones
- Conflicts are logged to `/config/clawd/pilotsuite_ops/logs/zone_conflicts.log`
- Manual resolution required for same-priority conflicts

## Integration Points

### Home Assistant
- Zone mapping loaded at component startup
- Area→Zone lookup cached in memory
- Changes trigger config entry reload

### PilotSuite Core
- Zone taxonomy exposed via `/api/v1/zones` endpoint
- Zone state synchronized via WebSocket
- Zone conflicts reported via diagnostics

## Migration Path

For existing deployments without zone taxonomy:

1. **Phase 1:** Auto-create default zones (`climate`, `security`, `lighting`)
2. **Phase 2:** Assign areas to zones based on entity types
3. **Phase 3:** Refine priorities based on usage patterns
4. **Phase 4:** Enable zone-based automation rules

## See Also

- PS-178: Area-to-Zone Mapping Registry
- PS-179: Unmatched Entity Logger
- PS-139: HA-Config-Flow-Test-Fixture-Standardisierung

---
*Document Version: 1.0*
*Last Updated: 2026-03-19*
*PS-REL-022: zone-taxonomy-spec*
