# Graph Candidates Bridge - Implementation Report

**Date:** 2026-02-14  
**Status:** ✅ Implemented & Tested  
**Priority:** Medium  
**Model Used:** ollamam2/glm-5:cloud  

---

## Summary

Successfully implemented the **Graph Candidates Bridge** module that creates a clean interface between Brain Graph v2 and the Candidates Store. The bridge extracts candidate-ready patterns from the brain graph and transforms them for use in the habitus automation suggestion pipeline.

## What Was Built

### 1. New Module: `copilot_core/brain_graph/bridge.py`

**Key Components:**

| Component | Purpose |
|-----------|---------|
| `PatternExtractionConfig` | Configuration for pattern extraction (thresholds, limits, filters) |
| `CandidatePattern` | Data class representing a candidate-ready pattern |
| `GraphCandidatesBridge` | Main bridge class providing pattern extraction and transformation |

### 2. Bridge Features

**Pattern Extraction Methods:**
- `extract_candidate_patterns()` - Extract patterns by type (habitus, zone_activity, scene, routine)
- `get_pattern_by_id()` - Retrieve specific pattern by ID
- `get_pattern_evidence_for_candidate()` - Get evidence dict for CandidateStore
- `get_candidate_metadata()` - Get metadata dict for CandidateStore
- `get_related_entities()` - Query related entities from graph

**Supported Pattern Types:**
- `habitus` - A→B automation patterns (service → entity correlations)
- `zone_activity` - Zone-based patterns (entity → zone relationships)
- `scene` - Multi-device scene patterns (TODO v0.2)
- `routine` - Time-based routine patterns (TODO v0.2)

### 3. Privacy Features

- **PII Detection**: Email, IP, phone number patterns are detected and filtered
- **Domain Blocking**: Locks, alarms, covers excluded by default (annoyance guardrails)
- **Meta Bounding**: Graph context limited to 10 edges, 2KB total

## Files Created/Modified

```
Created:
- ha-copilot-repo/addons/copilot_core/rootfs/usr/src/app/copilot_core/brain_graph/bridge.py (19.9 KB)
- ha-copilot-repo/addons/copilot_core/rootfs/usr/src/app/tests/test_graph_candidates_bridge.py (13.9 KB)

Modified:
- ha-copilot-repo/addons/copilot_core/rootfs/usr/app/copilot_core/brain_graph/__init__.py (exports bridge)
```

## Test Results

```
✅ All 8 tests passed:
- Bridge initialization
- Pattern extraction (2 habitus, 1 zone patterns extracted)
- Pattern evidence
- Mood impact estimation
- PII redaction
- Get related entities
- Pattern ID generation
- Config limits
```

## Integration Points

The bridge integrates with existing architecture:

```
Brain Graph v2 → GraphCandidatesBridge → HabitusService → CandidatesStore
     ↑                         ↓
  (patterns)            (extract + transform)
```

**Usage Example:**
```python
from copilot_core.brain_graph.bridge import GraphCandidatesBridge

bridge = GraphCandidatesBridge(brain_service)

# Extract patterns from brain graph
patterns = bridge.extract_candidate_patterns(pattern_type="habitus")

for pattern in patterns:
    # Get evidence for candidate
    evidence = bridge.get_pattern_evidence_for_candidate(pattern)
    metadata = bridge.get_candidate_metadata(pattern)
    
    # Create candidate in store
    candidate_id = candidate_store.add_candidate(
        pattern_id=pattern.pattern_id,
        evidence=evidence,
        metadata=metadata
    )
```

## Blockers / Issues

**None.** Implementation is complete and functional.

## Recommendations

### Immediate (v0.1)
- ✅ Ready for use by HabitusService for pattern extraction
- ✅ Can be extended to support scene/routine patterns in v0.2

### Future Enhancements (v0.2+)
1. **Scene Patterns**: Multi-device pattern extraction for light scenes
2. **Routine Patterns**: Time-based pattern extraction
3. **Confidence Calibration**: Fine-tune evidence calculations with real-world data
4. **Domain-Specific Guards**: Add more domain-specific safety rules

## Notes

- The bridge complements but doesn't replace the existing `HabitusMiner` - miners still run temporal analysis, while the bridge provides graph-based pattern extraction
- Bridge patterns are derived from existing graph edges (affects, correlates, in_zone)
- Mood impact estimation is heuristic-based and can be refined over time
- All PII detection is done before pattern creation, never stored in candidates

---

**Generated:** 2026-02-14 18:13 GMT+1  
**Worker:** PilotSuite - Subagent
