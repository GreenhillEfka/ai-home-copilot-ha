# Handoff: Lead → PilotClaw — Slice 135 Entscheidung

**Datum:** 2026-04-06 21:32 Europe/Berlin  
**Von:** Orakel (Lead-Lane)  
**An:** PilotClaw (Core-Lane)  
**Priorität:** HIGH (Blocker-Auflösung)

---

## Ausgangslage

PilotClaw hat Slice 134 (Backend-UI Performance-Baseline) am 2026-04-05 abgeschlossen. Seitdem steht die Lane an der Slice-135-Entscheidung:

> **Next Exact Task:** Slice 135 — Entscheidung über nächste Lane (HACS-Integration oder Neuron-Auth-Härtung)

Das ist kein technischer Blocker, sondern eine **Lead-Entscheidung**, die hiermit getroffen wird.

---

## Entscheidung (bindend)

**Slice 135 = Neuron-Auth-Härtung**

**Begründung:**

1. **Core-First:** PilotSuite-Core muss auth/permission-semantik intern stabil haben, bevor HACS-Integration externe Surface erweitert.
2. **Security-Baseline:** Neuron-Auth ist eine Sicherheitsgrenze — ohne klare Auth-Semantik driftet Core gegen HA/UX.
3. **HACS kann warten:** HACS-Integration ist wertvoll, aber blockiert keinen internen Core-Fortschritt. Neuron-Auth blockiert dagegen alle zukünftigen Permission-/Capability-Slices.
4. **Konsistenz mit Lead-Prinzip:** Canonicality / Product-Runtime-Rebaseline hat Vorrang vor externer Integration.

---

## Slice 135 — Exakter Auftrag

**Thema:** Neuron-Auth-Härtung  
**Ziel:** Neuron-level Auth/Permission-Semantik im Core verankern  
**Artefakt-Pfad:** `/config/clawd/team/worktrees/pilotsuite-styx-core-current/`  
**Erwartet:**
- Tasklog-Eintrag mit Slice-135-Start
- Klare Contract-Definition (welche Endpoints, welche Auth-Grenzen)
- Test-Beleg (auch wenn nur Contract-Tests initial)
- Commit auf führenden Core-Branch

---

## Success Signal

- PilotClaw-Tasklog zeigt Slice-135-Start innerhalb 15 Minuten
- Slice-135-Artefakt liegt unter docs/analysis/ oder direkt im Code-Worktree
- Kein weiterer Entscheidungs-Blocker — Builder fährt autonom

---

## Escalation

Wenn Slice 135 nicht innerhalb 24h startet → Lead eskaliert an Andreas mit konkretem Blocker-Bericht.
