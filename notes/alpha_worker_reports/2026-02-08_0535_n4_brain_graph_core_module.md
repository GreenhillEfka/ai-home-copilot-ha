# Brain Graph (N4) — Core module skeleton + endpoint plan (privacy-first, bounded)

## Goals / non-goals
**Goals**
- Maintain a *bounded*, *privacy-first* graph of “what matters recently” across entities, zones, people (optional), devices, and detected concepts.
- Support operator visualization (snapshot.svg) and stable state export (/state) for UI + debugging.
- Provide graph primitives that other modules can write to (habitus miner, repairs/suggestions, system health) without leaking raw event payloads.

**Non-goals (v0)**
- Full knowledge graph / long-term semantic memory.
- Cloud enrichment, embeddings, LLM-based extraction.
- Storing raw HA events or full attribute blobs.

## Storage model (bounded)
### Node
`GraphNode` (stored in an on-disk store, e.g. sqlite or jsonl; v0 can be a single JSON file with compaction)

Required fields
- `id: string` — stable, namespaced (e.g. `ha.entity:light.kitchen`, `zone:wohnzimmer`, `concept:movie_mode`)
- `kind: 'entity'|'zone'|'device'|'person'|'concept'|'module'|'event'` (keep small)
- `label: string` — human readable
- `updated_at_ms: number`
- `score: number` — current “salience” (bounded, decays)

Optional fields (tight allowlist)
- `domain?: string` — for HA entities (light/sensor/media_player)
- `source?: { system: 'ha'|'core'|'module', name?: string }`
- `tags?: string[]` — short, no PII
- `meta?: object` — **bounded**: max keys, max bytes; never include raw attributes

Hard limits
- Max nodes: `N_MAX` (default 500)
- Per-node `meta` size: e.g. 2KB; strip otherwise

### Edge
`GraphEdge`

Required fields
- `id: string` — stable (hash of `from|type|to`)
- `from: string` (node id)
- `to: string` (node id)
- `type: 'in_zone'|'controls'|'affects'|'correlates'|'triggered_by'|'observed_with'|'mentions'` (bounded enum)
- `updated_at_ms: number`
- `weight: number` — current strength

Optional (bounded)
- `evidence?: { kind: 'event'|'rule'|'manual', ref?: string }` (no raw payload)
- `meta?: object` (bounded like nodes)

Hard limits
- Max edges: `E_MAX` (default 1500)

### Indices (in-memory)
- adjacency lists for fast neighborhood queries
- `nodes_by_kind`, `nodes_by_domain`

## Privacy-first rules
- **No raw HA attributes** stored in node/edge meta (only whitelisted scalars).
- **Redaction**: any string values must be checked against patterns (emails, phone numbers, IPs, SSIDs, URLs) and truncated.
- **Names**: for people, store stable ids (`person:home_owner`) + display label sourced from configuration; never derive from chat logs.
- **Retention**: graph is bounded and decays; old low-salience nodes/edges are pruned.

## Scoring, decay, and pruning
### Update operations
Provide only a few primitives other modules can call:
- `touch_node(id, delta=+1, label?, kind?, meta_patch?)`
- `touch_edge(from, type, to, delta=+1, meta_patch?)`
- `link(from, type, to, weight=initial)` (alias for touch_edge)

### Decay
Let `score` and `weight` decay exponentially with time since `updated_at_ms`.

- Node decay: `score(t) = score0 * exp(-λn * Δt_hours)`
- Edge decay: `weight(t) = weight0 * exp(-λe * Δt_hours)`

Defaults (tunable)
- Half-life nodes: 24h → `λn = ln(2)/24`
- Half-life edges: 12h → `λe = ln(2)/12`

Implementation notes
- Store “raw” score + `updated_at_ms`; compute effective score on read OR periodically renormalize during compaction.

### Top-K pruning
Run pruning on write/compaction or when limits exceeded.

1) Compute effective scores/weights at `now`.
2) Drop edges with `weight < EDGE_MIN` (e.g. 0.1) first.
3) If `E > E_MAX`: keep top `E_MAX` edges by weight (ties by recency).
4) Drop nodes with `score < NODE_MIN` (e.g. 0.1) and no remaining edges.
5) If `N > N_MAX`: keep top `N_MAX` nodes by score (ties by recency). Remove incident edges accordingly.

Stability
- Prefer pruning *least recent among low-salience* to reduce thrash.

## API contracts
Base: `copilot_core` HTTP service.

### GET /api/v1/graph/state
Purpose: machine-readable graph state for UI/debug; bounded.

Query params (optional)
- `kind=entity|zone|...` (repeatable)
- `domain=light|sensor|...` (repeatable)
- `center=<nodeId>` — if present, return only neighborhood
- `hops=1|2` (default 1)
- `limitNodes=...` (cap at server max)
- `limitEdges=...`

Response 200 (application/json)
```json
{
  "version": 1,
  "generated_at_ms": 0,
  "limits": {"nodes_max": 500, "edges_max": 1500},
  "nodes": [
    {"id":"ha.entity:light.kitchen","kind":"entity","label":"Kitchen Light","domain":"light","score":3.2,"updated_at_ms":0}
  ],
  "edges": [
    {"id":"e:...","from":"ha.entity:light.kitchen","to":"zone:kitchen","type":"in_zone","weight":2.1,"updated_at_ms":0}
  ]
}
```

Errors
- 400 invalid params
- 503 graph store unavailable

### GET /api/v1/graph/snapshot.svg
Purpose: operator-friendly visualization.

Query params (optional)
- Same filters as `/state`
- `layout=dot|neato|fdp` (default `dot`)
- `theme=light|dark`
- `label=short|full` (default short)

Response 200
- `Content-Type: image/svg+xml`
- SVG generated from DOT with bounded node/edge count.

Safety
- Server-enforced caps: never render more than `N_RENDER_MAX` (e.g. 120 nodes) / `E_RENDER_MAX` (e.g. 300 edges). If exceeded, apply top-K by salience.

## Module skeleton (copilot_core)
Suggested package: `copilot_core/brain_graph/`

Components
- `store.py` (or ts/go equivalent): persistence + compaction
- `model.py`: Node/Edge dataclasses + validation + redaction
- `service.py`: update primitives + decay/prune
- `api.py`: HTTP handlers for `/state` and `/snapshot.svg`
- `render.py`: DOT generator

## TODO list
1. Choose persistence (sqlite vs JSON file). Recommend **sqlite** with two tables + indices.
2. Implement allowlisted `meta` schema + redaction/truncation helpers.
3. Implement decay computation + pruning routine (unit tests for stability).
4. Add update primitives and wire into forwarder/miners.
5. Implement `/state` filtering + neighborhood extraction.
6. Implement DOT/SVG rendering with hard caps and theme support.
7. Add metrics: node/edge counts, prune events, render time.
8. Add governance knobs in config (N_MAX/E_MAX/half-life/min thresholds).
