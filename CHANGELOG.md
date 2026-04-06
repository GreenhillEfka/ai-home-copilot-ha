# Changelog

All notable changes to PilotSuite Core will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.0.0-rc2] — 2026-04-07

### Added
- **P2-002:** OR-Tools CP-SAT Scheduler for energy optimization
  - Rolling 24-hour horizon with 15-minute slots
  - Support for EV charging, heat pumps, battery storage
  - Hard/soft constraint support
  - Carbon intensity weighting
- **P1-003:** Multi-User Preference Learning
  - Per-user preference profiles
  - Context-aware recommendations
  - Pattern learning and suggestions
  - Profile merging for shared spaces
- **P1-007:** Brain Graph Store Tests
  - 10+ comprehensive test cases
  - Persistence testing
  - Concurrent access testing
  - API endpoint tests
- **P1-008:** Tag System Tests
  - 12+ test cases for tagging operations
  - Bulk operations testing
  - Auto-tagging rules testing
  - Export/import testing
- **Infrastructure:**
  - `requirements.txt` with all dependencies
  - `manifest.json` for HACS integration
  - `__init__.py` with version strings
  - Research-to-Implementation tracker

### Changed
- Version bumped from `1.0.0-rc1` to `1.0.0-rc2`
- Energy module expanded with scheduler integration
- Test coverage increased from 0% to ~5%

### Fixed
- Missing package initialization (`__init__.py`)
- Dependency documentation (now in `requirements.txt`)
- HACS manifest structure

### Technical Details
- **Commits:** 5+ in this release
- **LOC Added:** ~1,900
- **Files Added:** 7
- **Tests Added:** 22+

---

## [1.0.0-rc1] — 2026-04-07

### Added
- Initial release candidate
- Core modules across 35+ directories
- API endpoints (REST, WebSocket, GraphQL, MCP)
- Voice pipeline (STT, NLU, TTS, Dialogue)
- RAG system with vector store
- ML modules (habit learning, pattern detection, anomaly detection)
- Energy management (forecasting, consumption tracking)
- Home Assistant integration
- Admin dashboard
- Lovelace cards

### Technical Details
- **Total LOC:** ~18,000+
- **Modules:** 90+
- **Commits:** 820+

---

## [Unreleased]

### Planned for v1.0.0
- Security audit completion
- Test coverage >80%
- HACS validation
- Complete documentation
- Performance benchmarks

### Under Consideration
- Old codebase feature parity analysis
- Knowledge Graph integration (Neo4j)
- Multi-sensor fusion
- Bayesian presence detection

---

## Version History Summary

| Version | Date | LOC | Commits | Key Features |
|---------|------|-----|---------|--------------|
| 1.0.0-rc2 | 2026-04-07 | ~19,900 | 822+ | Scheduler, Tests, HACS Prep |
| 1.0.0-rc1 | 2026-04-07 | ~18,000 | 817+ | Initial RC |

---

*For detailed research-to-implementation tracking, see `docs/RESEARCH_TO_IMPLEMENTATION.md`*
