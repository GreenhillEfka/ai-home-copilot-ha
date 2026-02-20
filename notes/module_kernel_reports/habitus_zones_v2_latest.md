# Habitus Zones v2 – Architektur-Report (Brain Graph Integration)

> **Datum:** 2026-02-14  
> **Autor:** Habitus Zones v2 Architect  
> **Version:** 1.0 (Draft)  
> **Status:** Zur Review

---

## 1. Executive Summary

Dieser Report beschreibt die detaillierte Planung für **Habitus Zones v2** mit vollständiger Integration in den **Brain Graph v0.1**. Die Analyse identifiziert Integration Points, definiert neue Schema-Erweiterungen und liefert konkrete Empfehlungen für API, State Machine und HA Entities.

**Kernergebnisse:**
- Zones werden als **First-Class Citizens** im Brain Graph behandelt
- 4 neue Edge-Types für Zone-Entity Relationships
- 5-State State Machine für Zone Dynamics
- 8 neue HA Entities für Zone Management
- Bidirektionale Sync-Strategie Zone ↔ Graph

---

## 2. Brain Graph v0.1 Analyse

### 2.1 Aktuelles Schema

| Komponente | Spezifikation |
|------------|---------------|
| **Node Types** | `entity`, `zone`, `device`, `person`, `concept`, `module`, `event` |
| **Edge Types** | `in_zone`, `controls`, `affects`, `correlates`, `triggered_by`, `observed_with`, `mentsions` |
| **Limits** | 500 Nodes, 1500 Edges |
| **Decay** | Exponential (Node: 24h, Edge: 12h half-life) |

### 2.2 Zone-Relevante Komponenten

```python
# Aktueller Zone Node (brain_graph_v0.1)
GraphNode(
    id="zone:wohnzimmer",           # namespaced
    kind="zone",                   # zone type
    label="Wohnzimmer",             # display name
    score=3.2,                     # salience (decays)
    domain="zone",                 # implicit
    meta={                         # bounded metadata
        "floor": "EG",
        "area_type": "living",
        "priority": 1
    }
)

# Aktueller Zone-Entity Edge
GraphEdge(
    id="e:light.wohnzimmer|in_zone|zone:wohnzimmer",
    from="ha.entity:light.wohnzimmer",
    to="zone:wohnzimmer",
    type="in_zone",
    weight=2.1,
    evidence={"kind": "rule"}
)
```

---

## 3. Zone Definitions (v2)

### 3.1 Hierarchisches Zone-Modell

```
🏠 Home
├── 🏗️ Floors (Stockwerke)
│   ├── EG (Erdgeschoss)
│   │   ├── Living Area
│   │   │   ├── Wohnzimmer (Zone)
│   │   │   ├── Küche (Zone)
│   │   │   └── Esszimmer (Zone)
│   │   └── Utility
│   │       ├── Bad (Zone)
│   │       └── Flur (Zone)
│   └── OG (Obergeschoss)
│       ├── Sleeping Area
│       │   ├── Schlafzimmer (Zone)
│       │       └── Ankleide (Zone)
│       └── Work Area
│           ├── Büro (Zone)
│           └── Gästezimmer (Zone)
└── 🌿 Outdoor
    ├── Garten (Zone)
    └── Terrasse (Zone)
```

### 3.2 Zone Dataclass (v2 Erweiterung)

```python
@dataclass(frozen=True, slots=True)
class HabitusZoneV2:
    """Habitus Zone v2 mit Brain Graph Integration."""
    # Core Identity
    zone_id: str                           # namespaced: "zone:wohnzimmer"
    name: str                              # Display-Name
    zone_type: str                        # "room", "area", "floor", "outdoor"

    # Entity Membership
    entity_ids: list[str]                  # Flat list (legacy compatibility)
    entities: dict[str, list[str]] | None   # Role-basiert (v2)

    # Hierarchy
    parent_zone_id: str | None             # "zone:living_area"
    child_zone_ids: list[str] = field(default_factory=list)
    floor: str | None                       # "EG", "OG", " UG"

    # Brain Graph Integration
    graph_node_id: str | None              # Auto-sync: "zone:wohnzimmer"
    in_edges: list[str] = field(default_factory=list)   # Entity-IDs in Zone
    out_edges: list[str] = field(default_factory=list)  # Zone→Entity Controls

    # State Machine
    current_state: str = "idle"            # idle, active, transitioning, error, disabled
    state_since: int | None                 # Timestamp (ms)

    # Metadata
    priority: int = 0                      # 0=niedrig, 10=hoch
    tags: list[str] = field(default_factory=list)
    metadata: dict[str, Any] | None = None
```

### 3.3 Role-System (v2)

| Role | Domain | Cardinality | Brain Graph Mapping |
|------|--------|-------------|-------------------|
| `motion` | binary_sensor, sensor | 1+ | Edge: `observed_with` |
| `lights` | light | 1+ | Edge: `controls` |
| `temperature` | sensor (device_class: temperature) | 1 | Edge: `observed_with` |
| `humidity` | sensor (device_class: humidity) | 0-1 | Edge: `observed_with` |
| `co2` | sensor (device_class: co2) | 0-1 | Edge: `observed_with` |
| `pressure` | sensor (device_class: pressure) | 0-1 | Edge: `observed_with` |
| `noise` | sensor (device_class: noise) | 0-1 | Edge: `observed_with` |
| `heating` | climate, switch, valve | 0-1 | Edge: `controls` |
| `door` | binary_sensor (device_class: door) | 0+ | Edge: `observed_with` |
| `window` | binary_sensor (device_class: window) | 0+ | Edge: `observed_with` |
| `cover` | cover | 0+ | Edge: `controls` |
| `lock` | lock | 0+ | Edge: `controls` |
| `media` | media_player | 0+ | Edge: `affects` |
| `power` | sensor (device_class: power) | 0-1 | Edge: `observed_with` |
| `energy` | sensor (device_class: energy) | 0-1 | Edge: `observed_with` |
| `brightness` | sensor (device_class: illuminance) | 0-1 | Edge: `observed_with` |

---

## 4. Brain Graph Integration

### 4.1 Node Schema Erweiterung

```python
@dataclass
class ZoneGraphNode:
    """Brain Graph Node für Zones (v2)."""
    # Base (GraphNode)
    id: str                              # "zone:wohnzimmer"
    kind: Literal["zone"] = "zone"
    label: str
    updated_at_ms: int
    score: float

    # Zone-spezifisch
    zone_type: str                       # "room", "area", "floor", "outdoor"
    floor: str | None
    hierarchy_level: int                 # 0=root, 1=area, 2=room
    parent_id: str | None
    child_ids: list[str] = field(default_factory=list)

    # Entity Counts (Aggregat)
    entity_count: int = 0
    role_counts: dict[str, int] = field(default_factory=dict)

    # State Machine Integration
    current_state: str = "idle"
    last_state_change_ms: int = 0
    state_duration_ms: int = 0

    # Habitus Patterns
    habitus_pattern_ids: list[str] = field(default_factory=list)
    mood_profile: dict[str, float] | None = None

    # Meta (bounded)
    meta: dict[str, Any] | None = None
```

### 4.2 Neue Edge-Types für Zones

| Edge Type | Von | Zu | Beschreibung | Gewichtung |
|-----------|-----|-----|--------------|------------|
| `zone_contains` | zone:parent | zone:child | Hierarchie-Beziehung | 5.0 (stabil) |
| `zone_controls` | zone | entity | Zone steuert Entity | 3.0 |
| `zone_monitors` | zone | entity | Zone beobachtet Entity | 1.5 |
| `zone_correlates` | zone | zone | Pattern-Korrelation | 2.0 |

### 4.3 Edge-Generation Regeln

```python
# Zone → Entity Edges (bei Entity-Assignment)
def generate_zone_entity_edges(zone: HabitusZoneV2) -> list[GraphEdge]:
    edges = []

    for entity_id in zone.entity_ids:
        # Default: in_zone (vorhanden)
        edges.append(GraphEdge(
            id=f"e:{entity_id}|in_zone|{zone.zone_id}",
            from=entity_id,
            to=zone.zone_id,
            type="in_zone",
            weight=2.0,
            updated_at_ms=now_ms()
        ))

        # Role-basiert
        if zone.entities:
            for role, entities in zone.entities.items():
                for eid in entities:
                    edge_type = ZONE_EDGE_TYPE_MAP.get(role, "zone_monitors")
                    edges.append(GraphEdge(
                        id=f"e:{eid}|{edge_type}|{zone.zone_id}",
                        from=eid,
                        to=zone.zone_id,
                        type=edge_type,
                        weight=ZONE_EDGE_WEIGHT_MAP.get(role, 1.5),
                        updated_at_ms=now_ms(),
                        meta={"role": role}
                    ))

    return edges

# Zone → Zone Edges (bei Hierarchy)
def generate_zone_zone_edges(zone: HabitusZoneV2) -> list[GraphEdge]:
    if zone.parent_zone_id:
        return [GraphEdge(
            id=f"e:{zone.zone_id}|zone_contains|{zone.parent_zone_id}",
            from=zone.zone_id,
            to=zone.parent_zone_id,
            type="zone_contains",  # child → parent
            weight=5.0,  # Stabil
            updated_at_ms=now_ms()
        )]
    return []
```

### 4.4 Bidirektionaler Sync

```
┌─────────────────┐         ┌─────────────────┐
│   HabitusZone   │◄───────►│  Brain Graph    │
│   Store v2      │   Sync  │   Node/Edge     │
└────────┬────────┘         └────────┬────────┘
         │                            │
         │ Zone Update                │ Graph Update
         ▼                            ▼
┌─────────────────────────────────────────────────┐
│              HabitusGraphSyncService            │
│  ┌───────────────────────────────────────────┐  │
│  │ sync_zone_to_graph(zone_id)              │  │
│  │ - Create/Update Node                      │  │
│  │ - Generate Edges (entity + hierarchy)     │  │
│  │ - Touch Node (score boost)                │  │
│  └───────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────┐  │
│  │ sync_graph_to_zone(node_id)              │  │
│  │ - Update metadata from graph              │  │
│  │ - Sync state from zone entity sensors     │  │
│  │ - Pull habitus patterns                   │  │
│  └───────────────────────────────────────────┘  │
└─────────────────────────────────────────────────┘
```

---

## 5. State Machine Design

### 5.1 Zone States

```
                    ┌──────────────┐
                    │   IDLE       │◄─────────────┐
                    │  (Ruhezustand)│              │
                    └──────┬───────┘              │
                           │                      │
         ┌─────────────────┼─────────────────┐     │
         │                 │                 │     │
         ▼                 ▼                 ▼     │
    ┌─────────┐     ┌───────────┐     ┌─────────┐│
    │ ACTIVE  │     │TRANSITION │     │DISABLED ││
    │(aktiv)  │────►│(Wechsel)  │────►│(deaktiv)││
    └────┬────┘     └─────┬─────┘     └────┬────┘│
         │                  │                │     │
         │                  │                │     └───────┐
         │                  ▼                │             │
         │           ┌───────────┐            │             │
         │           │ COMPLETED │            │             │
         │           │(abgeschlossen)│        │             │
         │           └─────┬─────┘            │             │
         │                 │                  │             │
         └─────────────────┴──────────────────┴─────────────┘
                              │
                              ▼
                        ┌─────────┐
                        │  ERROR  │
                        │(Fehler) │
                        └─────────┘
```

### 5.2 State Transitions

| Von | Nach | Trigger | Action |
|-----|------|---------|--------|
| IDLE | ACTIVE | Motion detected / Entity change | Boost score, start timer |
| ACTIVE | TRANSITION | No motion (timeout) | Check debounce |
| ACTIVE | IDLE | Explicit via API | Save duration |
| TRANSITION | ACTIVE | New motion | Cancel timeout |
| TRANSITION | IDLE | Timeout elapsed | Log transition |
| ANY | ERROR | Validation failed | Notify, fallback |
| ANY | DISABLED | Admin disable | Remove from graph |
| DISABLED | IDLE | Admin enable | Re-add to graph |

### 5.3 State Implementation

```python
class ZoneStateMachine:
    """State Machine für Habitus Zones."""

    STATES = ["idle", "active", "transitioning", "disabled", "error"]
    TRANSITIONS = {
        "idle": {"active", "disabled", "error"},
        "active": {"transitioning", "idle", "disabled", "error"},
        "transitioning": {"active", "idle", "disabled", "error"},
        "disabled": {"idle", "error"},
        "error": {"idle", "disabled"},
    }

    # Timeouts (konfigurierbar)
    ACTIVE_TIMEOUT_MS = 5 * 60 * 1000      # 5 Minuten Inaktivität
    TRANSITION_TIMEOUT_MS = 60 * 1000      # 1 Minute Debounce
    ERROR_RETRY_MS = 5 * 60 * 1000         # 5 Minuten Retry

    def __init__(self, zone: HabitusZoneV2):
        self.zone = zone
        self._state = zone.current_state or "idle"
        self._state_since_ms = zone.state_since or time_ms()
        self._transition_timer: asyncio.Timer | None = None

    @property
    def state(self) -> str:
        return self._state

    def transition(self, new_state: str, trigger: str | None = None) -> bool:
        """Führe State-Transition aus."""
        if new_state not in self.TRANSITIONS.get(self._state, set()):
            return False

        old_state = self._state
        self._state = new_state
        self._state_since_ms = time_ms()

        # Cancel pending timer
        if self._transition_timer:
            self._transition_timer.cancel()
            self._transition_timer = None

        # Schedule transition if needed
        if new_state == "transitioning":
            self._transition_timer = asyncio.create_task(
                self._delayed_transition("idle")
            )

        # Notify listeners
        self._notify_state_change(old_state, new_state, trigger)
        return True

    async def _delayed_transition(self, target_state: str):
        """Automatische Transition nach Timeout."""
        await asyncio.sleep(self.TRANSITION_TIMEOUT_MS / 1000)
        self.transition(target_state, timeout=True)

    def _notify_state_change(self, from_state: str, to_state: str, trigger: str | None):
        """Informiere über State-Change."""
        event = {
            "type": "zone_state_change",
            "zone_id": self.zone.zone_id,
            "from": from_state,
            "to": to_state,
            "trigger": trigger,
            "duration_ms": time_ms() - self._state_since_ms,
            "timestamp_ms": time_ms()
        }
        # Dispatch zu Brain Graph Service
        dispatch_event("zone_state_change", event)
```

---

## 6. API Endpoints

### 6.1 Zone Management API

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/zones` | List all zones |
| GET | `/api/v1/zones/{zone_id}` | Get single zone |
| POST | `/api/v1/zones` | Create zone |
| PUT | `/api/v1/zones/{zone_id}` | Update zone |
| DELETE | `/api/v1/zones/{zone_id}` | Delete zone |
| POST | `/api/v1/zones/{zone_id}/state` | Set state |
| GET | `/api/v1/zones/{zone_id}/state` | Get state |

### 6.2 Brain Graph Integration API

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/zones/{zone_id}/graph` | Get zone's graph representation |
| POST | `/api/v1/zones/{zone_id}/sync` | Sync zone to brain graph |
| GET | `/api/v1/zones/graph/neighborhood/{zone_id}` | Get zone + connected entities |
| GET | `/api/v1/zones/graph/topology` | Get zone hierarchy |

### 6.3 Response Schemas

```python
# GET /api/v1/zones/{zone_id}
ZoneResponse = {
    "zone_id": "zone:wohnzimmer",
    "name": "Wohnzimmer",
    "zone_type": "room",
    "floor": "EG",
    "parent_zone_id": "zone:living_area",
    "entity_ids": ["light.wohnzimmer", "sensor.motion_wohnzimmer"],
    "entities": {
        "motion": ["binary_sensor.motion_wohnzimmer"],
        "lights": ["light.wohnzimmer", "light.sofa"]
    },
    "current_state": "active",
    "state_since_ms": 1707923400000,
    "priority": 5,
    "tags": ["living", "entertainment"],
    "graph_node_id": "zone:wohnzimmer",
    "metadata": {
        "last_activity_ms": 1707923500000,
        "avg_duration_active": 3600000
    }
}

# GET /api/v1/zones/{zone_id}/graph
ZoneGraphResponse = {
    "node": {
        "id": "zone:wohnzimmer",
        "kind": "zone",
        "label": "Wohnzimmer",
        "score": 4.2,
        "zone_type": "room",
        "floor": "EG",
        "hierarchy_level": 2,
        "current_state": "active"
    },
    "edges": [
        {
            "id": "e:light.wohnzimmer|in_zone|zone:wohnzimmer",
            "from": "ha.entity:light.wohnzimmer",
            "to": "zone:wohnzimmer",
            "type": "in_zone",
            "weight": 2.0
        },
        {
            "id": "e:zone.wohnzimmer|zone_contains|zone.living_area",
            "from": "zone:wohnzimmer",
            "to": "zone:living_area",
            "type": "zone_contains",
            "weight": 5.0
        }
    ],
    "neighbors": {
        "entities": [...],
        "zones": [...]
    }
}
```

---

## 7. Home Assistant Entities Plan

### 7.1 Entities Liste

| Entity Type | Entity ID | Name | Purpose |
|-------------|-----------|------|---------|
| **Text** | `sensor.habitus_zones_v2_json` | PilotSuite habitus zones v2 (bulk editor) | Bulk-Zone-Editing (YAML/JSON) |
| **Button** | `button.habitus_zones_v2_validate` | PilotSuite validate habitus zones v2 | Validierung mit Details |
| **Button** | `button.habitus_zones_v2_sync_graph` | PilotSuite sync zones to brain graph | Manuelle Graph-Sync |
| **Sensor** | `sensor.habitus_zones_v2_count` | PilotSuite habitus zones v2 count | Anzahl konfigurierter Zones |
| **Sensor** | `sensor.habitus_zones_v2_health` | PilotSuite habitus zones v2 health | Gesamt-Health-Status |
| **Sensor** | `sensor.habitus_zones_v2_states` | PilotSuite habitus zones v2 states | Aggregierte State-Übersicht |
| **Select** | `select.habitus_zones_v2_global_state` | PilotSuite zones global state | Globaler Mode (auto/manual/disabled) |
| **Button** | `button.habitus_zones_v2_reload` | PilotSuite reload zones v2 | Reload + Re-sync |

### 7.2 Sensor: Zone States

```python
class HabitusZonesStatesSensor(CopilotBaseEntity, SensorEntity):
    """Aggregierte Zone States - v2 neue Entity."""

    _attr_name = "PilotSuite habitus zones v2 states"
    _attr_unique_id = "ai_home_copilot_habitus_zones_v2_states"
    _attr_icon = "mdi:state-machine"
    _attr_state_class = None

    async def async_update(self) -> None:
        zones = await async_get_zones_v2(self.hass, self._entry.entry_id)

        states = {"idle": 0, "active": 0, "transitioning": 0, "disabled": 0, "error": 0}
        for z in zones:
            state = getattr(z, "current_state", "idle")
            states[state] = states.get(state, 0) + 1

        # State = most common active state
        active_states = {k: v for k, v in states.items() if k in ("active", "transitioning")}
        most_common = max(active_states, key=active_states.get) if active_states else "idle"

        self._state = most_common
        self._attr_extra_state_attributes = {
            "zones_total": len(zones),
            "zones_by_state": states,
            "active_zones": [z.name for z in zones if getattr(z, "current_state") == "active"],
            "error_zones": [z.name for z in zones if getattr(z, "current_state") == "error"],
        }
```

### 7.3 Select: Global State

```python
class HabitusZonesGlobalStateSelect(CopilotBaseEntity, SelectEntity):
    """Globaler Zone Mode - v2 neue Entity."""

    _attr_name = "PilotSuite zones global state"
    _attr_unique_id = "ai_home_copilot_habitus_zones_v2_global_state"
    _attr_icon = "mdi:cog-transfer"
    _attr_options = ["auto", "manual", "disabled"]

    async def async_select_option(self, option: str) -> None:
        # Set global state
        await self._set_global_state(option)
        # Broadcast to all zones
        for zone in await async_get_zones_v2(self.hass, self._entry.entry_id):
            await self._broadcast_zone_state(zone.zone_id, option)
        self.async_write_ha_state()
```

### 7.4 Button: Graph Sync

```python
class HabitusZonesSyncGraphButton(CopilotBaseEntity, ButtonEntity):
    """Manuelle Sync zu Brain Graph - v2 neue Entity."""

    _attr_name = "PilotSuite sync zones to brain graph"
    _attr_unique_id = "ai_home_copilot_habitus_zones_v2_sync_graph"
    _attr_icon = "mdi:graph-outline"

    async def async_press(self) -> None:
        from .brain_graph import sync_service

        zones = await async_get_zones_v2(self.hass, self._entry.entry_id)
        results = []

        for zone in zones:
            result = await sync_service.sync_zone_to_graph(zone)
            results.append({
                "zone_id": zone.zone_id,
                "success": result.success,
                "nodes_created": result.nodes_created,
                "edges_created": result.edges_created,
            })

        # Summary notification
        success_count = sum(1 for r in results if r["success"])
        persistent_notification.async_create(
            self.hass,
            f"Brain Graph Sync:\n- Zones processed: {len(results)}\n- Success: {success_count}\n- Failed: {len(results) - success_count}",
            title="PilotSuite Zones → Brain Graph Sync",
            notification_id="habitus_zones_v2_graph_sync",
        )
```

---

## 8. Implementierungs-Roadmap

### Phase 1: Core Schema & Store
- [ ] `HabitusZoneV2` Dataclass mit Hierarchy
- [ ] Erweiterter `HabitusZonesStoreV2`
- [ ] Migration-Script v1 → v2
- [ ] Unit Tests für Schema

### Phase 2: Brain Graph Integration
- [ ] `ZoneGraphNode` Schema
- [ ] `HabitusGraphSyncService`
- [ ] Edge-Generation (entity + hierarchy)
- [ ] Bidirektionaler Sync
- [ ] Decay-Override für Zones

### Phase 3: State Machine
- [ ] `ZoneStateMachine` Implementierung
- [ ] Timeout-Handling
- [ ] Event-Dispatch
- [ ] State Persistence
- [ ] HA Entity Integration

### Phase 4: API & UX
- [ ] `/api/v1/zones/*` Endpoints
- [ ] `/api/v1/zones/*/graph` Endpoints
- [ ] Neue HA Entities (States, Global State, Sync)
- [ ] Lovelace Dashboard Cards

### Phase 5: Testing & Polish
- [ ] Integration Tests (Zone → Graph → Zone)
- [ ] Performance Tests (500+ Zones)
- [ ] Error Handling & Recovery
- [ ] Documentation

---

## 9. Offene Fragen & Empfehlungen

### 9.1 Offene Design-Entscheidungen

1. **Zone Decay Policy**: Soll Zone-Score unabhängig von Entity-Aktivität decayen?
   - Empfehlung: Separate Half-Life für Zones (48h) vs. Entities (24h)

2. **Cross-Zone Patterns**: Wie werden Muster über Zone-Grenzen hinweg erkannt?
   - Empfehlung: `zone_correlates` Edge mit separatem Pattern-Miner

3. **Person/Zone Assignment**: Soll `person:xyz|in_zone|zone:abc` Edges geben?
   - Empfehlung: Ja, für Anwesenheits-Tracking

4. **Graph Visualization**: Zones als Cluster oder hierarchisch?
   - Empfehlung: Nested Graph Layout (DOT mit `subgraph`)

### 9.2 Risiken

| Risiko | Impact | Mitigation |
|--------|--------|------------|
| Schema Breaking Change | Hoch | V2 Storage Version, Migrations-Pfad |
| Performance (500+ Zones) | Mittel | Pagination, Caching |
| Graph-Cycle Detection | Mittel | Acyclicity Check bei Hierarchy |

---

## 10. Anhang

### A. Konfigurations-Beispiel

```yaml
habitus_zones_v2:
  zones:
    - id: zone:wohnzimmer
      name: Wohnzimmer
      zone_type: room
      floor: EG
      parent: zone:living_area
      entities:
        motion:
          - binary_sensor.motion_wohnzimmer
        lights:
          - light.wohnzimmer
          - light.soffitte
        media:
          - media_player.wohnzimmer_tv
        temperature:
          - sensor.temperatur_wohnzimmer
      priority: 8
      tags: [living, entertainment]

  brain_graph:
    enabled: true
    sync_interval_ms: 30000
    node_decay_hours: 48
    edge_decay_hours: 24

  state_machine:
    active_timeout_ms: 300000  # 5 min
    transition_timeout_ms: 60000  # 1 min
    auto_mode: true
```

### B. Referenzen

| Document | Path |
|----------|------|
| Brain Graph v0.1 Spec | `docs/MODULE_brain_graph_v0.1.md` |
| Habitus Zones Store v2 | `ai_home_copilot_hacs_repo/.../habitus_zones_store_v2.py` |
| Habitus Zones Entities v2 | `ai_home_copilot_hacs_repo/.../habitus_zones_entities_v2.py` |
| Mood-Habitus-Synapse Concept | `docs/CONCEPT_v0.2_mood_habitus_synapse.md` |

---

*Report erstellt: 2026-02-14*  
*Nächste Schritte: Review durch Core Team, Phase 1 Implementierung*
