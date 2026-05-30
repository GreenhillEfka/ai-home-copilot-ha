# 2026-04-24 — Next exact pull: RAG-RESILIENCE-307

**Stand:** 2026-04-24 Europe/Berlin
**Status:** queued behind `DELIVERY-CONTEXT-306-B`
**Owner:** PilotClaw
**Why next:** the 2026-04-22 concept review explicitly called out retrieval resilience as the next strengthening area after context, delivery durability, and structured observability. Current Core RAG already has BM25 + semantic paths, but degraded semantic state is still mostly implicit via warnings. The next bounded step is to make fallback truth explicit and machine-checkable without widening the search family.

## Goal
Make degraded retrieval state explicit on the existing Core RAG search seam so memory/research support remains deterministic when semantic retrieval is unavailable or failing.

## Canonical user-visible object
`answerable local search even when semantic retrieval is degraded`

## Exact seam
Stay inside the current Core RAG family only:
- `POST /api/v1/rag/search`
- `POST /api/v1/rag/search/enhanced`

## Exact files
- `/config/clawd/team/worktrees/pilotsuite-styx-core-current/addons/pilotsuite/app/copilot_core/api/v1/rag.py`
- `/config/clawd/team/worktrees/pilotsuite-styx-core-current/tests/test_rag_search_contract.py`
- `/config/clawd/team/worktrees/pilotsuite-styx-core-current/tests/test_rag_resilience_307_contract.py`

## Required behavior
1. Hybrid/local retrieval must expose structured fallback truth:
   - `effective_mode`
   - `degraded`
   - `degraded_reason`
2. If semantic retrieval is unavailable or fails and lexical retrieval is allowed, the request must still return BM25-backed results on the same endpoint family.
3. Degraded fallback must be machine-checkable, not only encoded as free-text warnings.
4. Explicit semantic-only requests must not silently widen into a different contract.
5. No new search endpoint family is introduced.

## Focused task breakdown
- add one helper-level degradation reason path for semantic-unavailable / semantic-failed cases
- surface effective retrieval mode on hybrid response payloads
- keep warnings for human diagnosis, but add structured degraded truth for machines
- add contract tests for:
  - semantic backend missing
  - semantic backend exception
  - healthy hybrid path remains non-degraded
  - semantic-only request does not silently widen

## Focused proof ring
```bash
cd /config/clawd/team/worktrees/pilotsuite-styx-core-current
python3 -m py_compile \
  addons/pilotsuite/app/copilot_core/api/v1/rag.py

/config/clawd/.venv_smoke_gate/bin/python -m pytest -q \
  tests/test_rag_search_contract.py \
  tests/test_rag_resilience_307_contract.py
```

## Done means
- degraded retrieval truth is explicit in the existing response contract
- hybrid/local search stays useful under semantic degradation
- semantic-only requests stay bounded and honest
- proof ring green
- commit landed with a short closeout packet
- next exact pull advances to `FAST-LANE-CONTINUITY-308`

## Non-goals
- no new vector store backend
- no full retrieval redesign
- no dashboard or HA consumer packet
- no web-search strategy rewrite
- no broad conversation API rewrite

## Next exact pull after landing
- `FAST-LANE-CONTINUITY-308` — immediately cut the next bounded wave from fresh landed truth
