## [LRN-20260321-001] correction

**Logged**: 2026-03-21T21:57:19+01:00
**Priority**: high
**Status**: pending
**Area**: release

### Summary
Do not claim paired release/orderliness before live runtime, published releases, and architectural contract are all aligned.

### Details
The user correctly pointed out repeated unclean work: mixed HA/HACS vs Core/Add-on terminology, release truth lagging behind repo truth, and frontend/runtime claims being made before the actual live pairing was healthy. The correct workflow is: (1) establish canonical architecture, (2) align repo main truth, (3) align published release truth, (4) verify live runtime/ports/contracts, (5) only then claim clean paired status.

### Suggested Action
Use a stricter release gate for PilotSuite: no "paired/clean/live" wording unless repo, GitHub release, runtime health, and contract endpoints are all verified.

### Metadata
- Source: user_feedback
- Related Files: /config/clawd/.learnings/LEARNINGS.md
- Tags: release, pairing, terminology, verification

---
## [LRN-20260321-002] correction

**Logged**: 2026-03-21T23:04:10+01:00
**Priority**: critical
**Status**: pending
**Area**: reporting

### Summary
For PilotSuite, always state channel + version together: HA means HACS release; Core means Add-on release; git/main is a separate lane.

### Details
The user explicitly reinforced that the team must remember the distinction and stop re-explaining or re-mixing it. Reporting must use the exact schema: HA/HACS version, Core/Add-on version, Git state, live verified yes/no. Never imply a HACS version from a Core release or a live state from git/main.

### Suggested Action
Use the 4-line reporting format by default for PilotSuite status replies and broadcast the distinction to all active team lanes.

### Metadata
- Source: user_feedback
- Related Files: /config/clawd/.learnings/LEARNINGS.md, /config/clawd/memory/2026-03-21.md
- Tags: reporting, versioning, pilot-suite, correction

---
## [LRN-20260321-003] correction

**Logged**: 2026-03-21T23:14:00+01:00
**Priority**: critical
**Status**: pending
**Area**: reporting

### Summary
Never mention Core intermediate versions like 15.0.2 in a HACS/integration context.

### Details
The user pointed out the exact failure mode: when the assistant mentions `v15.0.2` while discussing the integration/HACS surface, it immediately creates version confusion because HACS can only use HA integration releases. Core intermediate releases must stay in the Core/Add-on lane only.

### Suggested Action
In PilotSuite reporting, forbid cross-surface version mentions: HA/HACS numbers may only refer to the integration repo; Core numbers may only refer to the add-on repo.

### Metadata
- Source: user_feedback
- Related Files: /config/clawd/.learnings/LEARNINGS.md, /config/clawd/memory/2026-03-21.md
- Tags: reporting, versioning, haxs, core, correction

---
## [LRN-20260322-005] correction

**Logged**: 2026-03-22T03:57:00+01:00
**Priority**: critical
**Status**: pending
**Area**: reporting

### Summary
Never call a PilotSuite integration version "HACS-usable" unless it is actually installable and usable through HACS.

### Details
I treated `v15.0.5` as a usable HACS path without proof that HACS could actually use it. The user explicitly corrected that this version cannot be used with HACS and told me to abort. In PilotSuite reporting, git tag existence, release existence, and actual HACS usability are separate facts.

### Suggested Action
Only describe a version as HACS-usable when installability through HACS is confirmed. Otherwise label it clearly as git/release-only or unusable via HACS.

### Metadata
- Source: user_feedback
- Related Files: /config/clawd/.learnings/LEARNINGS.md
- Tags: reporting, hacs, release, correction, pilot-suite
- See Also: LRN-20260321-001, LRN-20260321-002, LRN-20260321-003

---
## [LRN-20260322-006] correction

**Logged**: 2026-03-22T03:58:00+01:00
**Priority**: high
**Status**: pending
**Area**: reporting

### Summary
Do not treat copied text containing imperative words like "ABBRECHEN" as a live user instruction without checking whether it was quoted/copied context.

### Details
I interpreted a copied `ABBRECHEN` line as an active instruction to abort the HACS 15.0.5 line. The user corrected that the text was copied, not an abort command. In group debugging/reporting contexts, quoted or pasted status text must be separated from actual instructions.

### Suggested Action
When a message may contain pasted/copied text, explicitly distinguish quoted content from the user's live instruction before acting on imperative words.

### Metadata
- Source: user_feedback
- Related Files: /config/clawd/.learnings/LEARNINGS.md
- Tags: reporting, correction, copied-text, instruction-parsing, pilot-suite
- See Also: LRN-20260322-005

---
