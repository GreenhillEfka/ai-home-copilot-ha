"""Pattern Proposal Store.

Append-only JSON Lines store for pattern observations and suggestion candidates.
"""
from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from .models import PatternObservation, SuggestionCandidate

_LOGGER = logging.getLogger(__name__)


class ProposalStore:
    """Append-only store for observations and candidates, per zone."""

    def __init__(self, storage_dir: str | Path) -> None:
        self.storage_dir = Path(storage_dir)
        self.observations_file = self.storage_dir / "observations.jsonl"
        self.candidates_file = self.storage_dir / "candidates.jsonl"
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self._candidates_cache: list[SuggestionCandidate] | None = None

    # ── Observations ──────────────────────────────────────────────────────────

    def record_observation(self, obs: PatternObservation) -> None:
        """Append a new observation."""
        with open(self.observations_file, "a", encoding="utf-8") as f:
            f.write(obs.model_dump_json() + "\n")

    def get_observations(
        self,
        zone_id: str,
        trigger: str | None = None,
        since: datetime | None = None,
    ) -> list[PatternObservation]:
        """Read observations for a zone, optionally filtered."""
        if not self.observations_file.exists():
            return []
        results: list[PatternObservation] = []
        with open(self.observations_file, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                obs = PatternObservation.model_validate_json(line)
                if obs.zone_id != zone_id:
                    continue
                if trigger is not None and obs.trigger != trigger:
                    continue
                if since is not None and obs.timestamp < since:
                    continue
                results.append(obs)
        return results

    # ── Candidates ────────────────────────────────────────────────────────────

    def save_candidate(self, candidate: SuggestionCandidate) -> None:
        """Persist a candidate."""
        self._candidates_cache = None
        with open(self.candidates_file, "a", encoding="utf-8") as f:
            f.write(candidate.model_dump_json() + "\n")

    def get_candidates(
        self,
        zone_id: str | None = None,
        dismissed: bool | None = None,
    ) -> list[SuggestionCandidate]:
        """Load all candidates, optionally filtered."""
        if not self.candidates_file.exists():
            return []
        if self._candidates_cache is None:
            self._candidates_cache = []
            with open(self.candidates_file, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    self._candidates_cache.append(
                        SuggestionCandidate.model_validate_json(line)
                    )
        results = list(self._candidates_cache)
        if zone_id is not None:
            results = [c for c in results if c.zone_id == zone_id]
        if dismissed is not None:
            results = [c for c in results if c.dismissed == dismissed]
        return results

    def accept_candidate(self, candidate_id: str) -> bool:
        """Mark a candidate as accepted."""
        return self._update_candidate(candidate_id, accepted=True)

    def dismiss_candidate(self, candidate_id: str) -> bool:
        """Mark a candidate as dismissed."""
        return self._update_candidate(candidate_id, dismissed=True)

    def _update_candidate(
        self, candidate_id: str, accepted: bool | None = None, dismissed: bool | None = None
    ) -> bool:
        """Rewrite candidates file with updated record."""
        if not self.candidates_file.exists():
            return False
        updated: list[dict[str, Any]] = []
        found = False
        with open(self.candidates_file, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                rec = json.loads(line)
                if rec.get("candidate_id") == candidate_id:
                    if accepted is not None:
                        rec["accepted"] = accepted
                    if dismissed is not None:
                        rec["dismissed"] = dismissed
                    found = True
                updated.append(rec)
        if not found:
            return False
        with open(self.candidates_file, "w", encoding="utf-8") as f:
            for rec in updated:
                f.write(json.dumps(rec) + "\n")
        self._candidates_cache = None
        return True

    def prune_old(self, max_age: timedelta = timedelta(days=7)) -> int:
        """Remove observations older than max_age. Returns count removed."""
        if not self.observations_file.exists():
            return 0
        cutoff = datetime.utcnow() - max_age
        kept: list[str] = []
        removed = 0
        with open(self.observations_file, encoding="utf-8") as f:
            for line in f:
                line_strip = line.strip()
                if not line_strip:
                    continue
                obs = PatternObservation.model_validate_json(line_strip)
                if obs.timestamp >= cutoff:
                    kept.append(line_strip)
                else:
                    removed += 1
        with open(self.observations_file, "w", encoding="utf-8") as f:
            f.write("\n".join(kept) + "\n")
        return removed
