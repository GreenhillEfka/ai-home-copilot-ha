# 2026-04-24 — Next exact pull: RAG-NEXT-309

**Stand:** 2026-04-24 21:42 Europe/Berlin
**Status:** active next pull after `FAST-LANE-CONTINUITY-308`
**Owner:** PilotClaw
**Why next:** the RAG seam after `RAG-RESILIENCE-307` has a natural next bounded strengthening: making result enrichment resilient to enrichment failures so degraded retrieval still returns useful structured hits even when enrichment partially fails.

## Goal
Make result enrichment resilient under partial failure so that degraded RAG responses remain structurally sound and machine-checkable at the result-entry level.

## Canonical user-visible object
`structured hit entries remain complete and machine-checkable even when text/metadata enrichment fails`

## Exact seam
- `POST /api/v1/rag/search`
- `POST /api/v1/rag/search/enhanced`
- `addons/pilotsuite/app/copilot_core/api/v1/rag.py`

## Exact files
- `/config/clawd/team/worktrees/pilotsuite-styx-core-current/addons/pilotsuite/app/copilot_core/api/v1/rag.py`
- `/config/clawd/team/worktrees/pilotsuite-styx-core-current/tests/test_rag_resilience_307_contract.py`
- `/config/clawd/team/worktrees/pilotsuite-styx-core-current/tests/test_rag_enrichment_resilience_309_contract.py` (new)

## Required behavior
1. `_enrich_results` and `_build_result_entry` must not crash and must not produce unparseable entries when partial enrichment data is missing.
2. When `include_text=False`, text enrichment failures must not invalidate the hit.
3. When `include_metadata=False`, metadata enrichment failures must not invalidate the hit.
4. Structured result entries must always be machine-checkable even under partial enrichment failure.
5. No new search mode, no new endpoint, no new response field outside the existing contract.

## Non-goals
- no new search family
- no RAG cache redesign
- no vector store backend
- no semantic-only hardening (covered by 307)

## Done means
- enrichment failures produce graceful nulls, not crashes
- result entries are always machine-parseable
- focused proof ring green (existing 307 tests + new 309 tests)
- commit landed + closeout packet written
- next exact pull is cut from fresh truth
