# Brain Graph (N4) – Core module v0.1 (privacy-first, bounded)

> Source: alpha worker report `2026-02-08_0535_n4_brain_graph_core_module.md`.

## Goals / non-goals
**Goals**
- Maintain a *bounded*, *privacy-first* graph of “what matters recently” across entities, zones, people (optional), devices, and detected concepts.
- Support operator visualization (`snapshot.svg`) and stable state export (`/state`) for UI + debugging.
- Provide graph primitives that other modules can write to (habitus miner, repairs/suggestions, system health) without leaking raw event payloads.

**Non-goals (v0)**
- Full knowledge graph / long-term semantic memory.
- Cloud enrichment, embeddings, LLM-based extraction.
- Storing raw HA events or full attribute blobs.

## Storage model (bounded)
### Node
`GraphNode`

Required
- `id: string` — stable, namespaced (e.g. `ha.entity:light.kitchen`, `zone:wohnzimmer`, `concept:movie_mode`)
- `kind: 'entity'|'zone'|'device'|'person'|'concept'|'module'|'event'`
- `label: string`
- `updated_at_ms: number`
- `score: number` — salience (decays)

Optional (tight allowlist)
- `domain?: string` — for HA entities (light/sensor/media_player)
- `source?: { system: 'ha'|'core'|'module', name?: string }`
- `tags?: string[]`
- `meta?: object` — bounded; never raw attributes

Limits
- Max nodes `N_MAX` (default 500)
- Per-node `meta` max size (e.g. 2KB)

### Edge
`GraphEdge`

Required
- `id: string` — stable (hash of `from|type|to`)
- `from: string`
- `to: string`
- `type: 'in_zone'|'controls'|'affects'|'correlates'|'triggered_by'|'observed_with'|'mentions'`
- `updated_at_ms: number`
- `weight: number`

Optional (bounded)
- `evidence?: { kind: 'event'|'rule'|'manual', ref?: string }`
- `meta?: object`

Limits
- Max edges `E_MAX` (default 1500)

## Privacy-first rules
- No raw HA attributes stored in node/edge `meta` (only whitelisted scalars).
- Redaction: check string values against patterns (emails/phones/IPs/SSIDs/URLs) and truncate.
- People: store stable ids (e.g. `person:home_owner`) + display label from configuration; don’t derive from chat logs.
- Retention: bounded graph + decay + pruning.

## Scoring, decay, pruning
### Update primitives
- `touch_node(id, delta=+1, label?, kind?, meta_patch?)`
- `touch_edge(from, type, to, delta=+1, meta_patch?)`
- `link(from, type, to, weight=initial)`

### Decay
Exponential decay based on time since `updated_at_ms`.
- Node half-life default: 24h
- Edge half-life default: 12h

### Top-K pruning
1. Compute effective scores/weights at `now`.
2. Drop edges with `weight < EDGE_MIN`.
3. If `E > E_MAX`: keep top `E_MAX` edges by weight (ties by recency).
4. Drop nodes with `score < NODE_MIN` and no remaining edges.
5. If `N > N_MAX`: keep top `N_MAX` nodes by score (ties by recency). Remove incident edges.

## API v1 contracts
### `GET /api/v1/graph/state`
Query params (optional)
- `kind=entity|zone|...` (repeatable)
- `domain=light|sensor|...` (repeatable)
- `center=<nodeId>` — neighborhood mode
- `hops=1|2` (default 1)
- `limitNodes=...` / `limitEdges=...` (server-capped)

Response 200
```json
{
  "version": 1,
  "generated_at_ms": 0,
  "limits": {"nodes_max": 500, "edges_max": 1500},
  "nodes": [{"id":"ha.entity:light.kitchen","kind":"entity","label":"Kitchen Light","domain":"light","score":3.2,"updated_at_ms":0}],
  "edges": [{"id":"e:...","from":"ha.entity:light.kitchen","to":"zone:kitchen","type":"in_zone","weight":2.1,"updated_at_ms":0}]
}
```

### `GET /api/v1/graph/snapshot.svg`
- Supports same filters as `/state`
- `layout=dot|neato|fdp` (default `dot`)
- `theme=light|dark`
- `label=short|full` (default short)
- Hard caps: `N_RENDER_MAX` (e.g. 120), `E_RENDER_MAX` (e.g. 300) with top-K selection.

## Suggested module skeleton (copilot_core)
Package: `copilot_core/brain_graph/`
- `store.*` persistence + compaction
- `model.*` Node/Edge + validation + redaction
- `service.*` update primitives + decay/prune
- `api.*` handlers for `/state` + `/snapshot.svg`
- `render.*` DOT generation

## TODO
1. Choose persistence (sqlite recommended).
2. Implement allowlisted `meta` + redaction/truncation.
3. Decay + pruning routine (unit tests).
4. Wire update primitives into forwarder/miners.
5. `/state` filtering + neighborhood extraction.
6. DOT/SVG rendering with caps.
7. Metrics: counts, prune events, render time.
8. Governance knobs in config (N_MAX/E_MAX/half-life/min thresholds).
