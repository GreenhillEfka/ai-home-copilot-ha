# 2026-04-22 Status, release, and support-agent system

**Stand:** 2026-04-22 23:34 Europe/Berlin
**Trigger:** Andreas wants cleaner status reports in channel, more visible code effort, intermediate git/release checkpoints, and additional supporting agents.

## Why it did not happen cleanly before
Three gaps were real:
1. the system was optimized too hard for silent autonomous execution and exact pulls
2. there was no explicit status/report contract for `topic:1`
3. there was no dedicated support-agent layer for release packaging, visualization/config review, and proof/research gating

That combination increased code throughput in places, but it did not give Andreas the clean, current visibility he expects.

## New channel contract for `topic:1`
`topic:1` now gets **clean status cards only**, never stale queue prose and never raw tool noise.

### Allowed post types
1. **Landing card**
2. **Current work card**
3. **Intermediate release/checkpoint card**
4. **Real blocker card**
5. **Next exact pull card**

### Mandatory fields in every status card
- **Item**
- **Status** (`working`, `landed`, `release`, `blocked`)
- **When**
- **How** (files / seam / proof ring)
- **Implemented function**
- **Visualization/consumer status**
- **Configuration status**
- **Next exact pull**

### Anti-noise rule
Do not post:
- repeated old reports
- stale queue summaries
- raw exec output
- research notes without a direct execution consequence

## Intermediate git release cadence
Every 2 to 4 meaningful landings, or at a visible vertical-slice checkpoint, create an **intermediate git checkpoint / release card**.

### Release card must include
- checkpoint label
- included landed items
- commit range or exact commit ids
- proof summary
- what functions are now real
- what is visible/configurable already
- what remains for the next checkpoint

## Support-agent layer
These support agents exist to increase coding throughput without creating second writer drift.

### Hermes — status/release steward
**Job:** turn fresh file truth into clean status cards and intermediate release checkpoints.
**Scope:** status formatting, release notes, checkpoint bundles, commit/proof summaries.
**Non-goal:** no product-code writing.

### Athene — visualization/config bundle reviewer
**Job:** ensure meaningful features have honest visualization and configuration follow-through.
**Scope:** packet review, front-surface mapping, config/control-surface mapping.
**Non-goal:** no independent product writer path.

### Aegis — proof/research gate support
**Job:** tighten proof rings, edge-case checks, and bounded pre-code research packets behind the active builder seam.
**Scope:** exact seam analysis, proof strengthening, bundle readiness.
**Non-goal:** no queue hijack, no broad research chatter.

### Existing single writers remain unchanged
- **PilotClaw** = Core only
- **HomeClaw** = HA only
- **Orakel** = routing / packet readiness / clean reporting
- **DesignClaw** = support-only, exact-request sharpening

## Hand-in-hand execution rule
Before a feature is treated as done, the status card must say whether it has:
- backend truth
- visualization truth
- configuration truth

If one is still missing and required, the card must mark it as missing and the next pull must be named.

## Immediate rollout
### 1. Current queue reporting
For the active chain, channel reports must show:
- what is being worked now
- when it started/landed
- how it was proven
- what function is now implemented
- whether visualization exists
- whether configuration exists
- what exact next pull follows

### 2. Current release/checkpoint rule
When the next major chain segment lands, issue a clean intermediate checkpoint for:
- `HARDEN-208`
- `HARDEN-209`
- `AUTO-203-B`
- `HA-FOLLOW-DELIVERY`
if enough of that bundle is real

### 3. Current support focus
- Hermes supports status/release packaging
- Athene supports visualization/config completeness
- Aegis supports proof/research packet strength

## Success signal
This system is working when Andreas sees:
- clean current status cards instead of repeated old reports
- more visible development effort on actual code
- intermediate git/checkpoint releases at sensible milestones
- clearer visibility into what is implemented, what is visible, what is configurable, and what is next
