---
name: groky-dev-check
description: Automated iterative development workflow for PilotSuite Styx HA add-on. Handles repo status checks, bug fixes, feature expansions, testing, releases, and status reports. Use when running consolidated dev checks for AI-Haushalt system, including cross-home sharing, autopilot runner, scenes/routines, MUPL, dashboard visualization. Triggers on cron schedules for P0/P1 tasks from VISION.md.
---

# Groky Dev Check

## Overview

This skill guides the Groky agent through a consolidated development check for the PilotSuite Styx project. It ensures HA-conformant iterative improvements, using a phased approach. Spawn sub-agents for speed where needed.

## Workflow

Follow these phases in order for each run.

### Phase 1: Repo Status and Preparation
- Fetch updates from origin.
- Switch to or create 'dev/groky-main' branch.
- Merge main into 'dev/groky-main' to stay up-to-date.
- Create backups (git bundle or zip) to workspace/backups/.
- Run automated updates if new versions available.
- Check for uncommitted changes and resolve.

### Phase 2: Bugfix Round (P0)
- Identify core problems (error isolation, connection pooling).
- Implement solutions.
- Optimize performance (caching, pooling, measure runtimes).
- Run security checks (bandit, git secrets).
- Learn from past errors (track in MEMORY.md).

### Phase 3: Feature Extension (P1/P2)
- Work through VISION.md step-by-step.
- Expand features: cross-home sharing, autopilot runner, scenes/routines patterns, MUPL, dashboard visu.
- Interact with external APIs/services to fetch data.
- Extend integrations with other tools (Zapier, IFTTT).
- Support internationalization (translations).
- Consider scalability (async, load balancing).
- Improve user interface (UI/UX, mobile-friendly, accessibility, themes, search function, offline capability).
- Involve community (post updates to forums/social via APIs).
- Add user feedback function (forms/issues).
- Incorporate learning component (from errors/feedback).

### Phase 4: Testing and Conformance
- Run automatic test-suite (pytest, HA-conformance checks).
- Check code quality (black, flake8).
- Ensure HA conformance (manifest.json, HACS structure).
- Run CI checks (gh run view); only proceed if all green.

### Phase 5: Release and Documentation
- Update docs/README regularly (README.md, VISION.md, etc.).
- Version control for documentation.
- Create/update PR to main with notes (gh pr create/edit).
- Keep PR up-to-date (rebase/push).
- Use issue-tracking for tasks and code reviews (gh issue, gh pr review).
- Integrate deployment pipeline (GH Actions).
- If green, merge PR (gh pr merge --auto).

### Phase 6: Status Report and Notifications
- Integrate logging for detailed reports (to logs/groky.log).
- Send status report to Telegram 1616970089.
- Add notifications for key events (via message tool).
- Make documentation interactive (search, FAQs, demos).
- Add custom configurations support.

## Resources

### scripts/
- Use for git operations, test running, backup creation, etc. (add as needed).

### references/
- VISION.md: Core vision for PilotSuite Styx.
- PILOTSUITE_DEVELOPMENT.md: P0/P1 tasks.
- (Add more references like API docs, schemas).

### assets/
- Templates for CHANGELOG.md, RELEASE_NOTES.md.
- UI templates for dashboards.

Follow progressive disclosure: Load references only when needed.