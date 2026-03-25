# Frontend Roadmap — PilotSuite

**Stand:** 2026-03-25  
**Owner:** DesignClaw / PilotDesign  
**Lane:** Frontend, TypeScript, React, Dashboard, UX

---

## Prioritäten-Übersicht

| Priorität | Beschreibung | Beispiele |
|-----------|--------------|-----------|
| **P0** | BLOCKER — Blockiert Release oder Live-Betrieb | Version-Sync, Release-Pipeline |
| **P1** | HIGH — Kernfunktionalität, muss vor Release | Dashboard-Erweiterung, RAG Search |
| **P2** | MEDIUM — UX-Verbesserungen, parallel möglich | Micro-Interactions, Dark Mode |
| **P3** | LOW — Nice-to-have, nach Release | Animationen, Skeletons |

---

## 🚨 P0 — BLOCKER (Sofort)

| ID | Task | Status | Owner | ETA | Notes |
|----|------|--------|-------|-----|-------|
| **P0-201** | Workspace-Kandidat `15.0.17` und Versions-Sync im Dashboard/Docs sichtbar gemacht | ✅ DONE | @codexa | — | 2026-03-23 abgeschlossen |
| **P0-202** | Release-Pipeline: Dashboard/Artefakte zeigen nach GitHub-Release immer die verifizierte Live-Version | ⏳ PENDING | @codexa | 15min | Muss Release-Hygiene sicherstellen |
| **P0-203** | UI-/Smoke-Beweis für `15.0.17`-Kandidaten (Cards/Sensoren sichtbar, kein Drift) | ⏳ PENDING | @codexa | 20min | Live-Verification offen |

---

## 🔥 P1 — HIGH (Nach P0)

| ID | Task | Status | Owner | ETA | Notes |
|----|------|--------|-------|-----|-------|
| **P1-090** | RAG Search Frontend (TypeScript) | ⏳ PENDING | @codexa | 30min | Search-UI für Vektorstore |
| **P1-091** | Zone Editor TypeScript Frontend | ⏳ PENDING | @codexa | 30min | Zone-Configuration UI |
| **P1-092** | Dashboard-Erweiterung (Styx v1.0) — 10 Habituszonen live | ⏳ PENDING | @designclaw | 40min | **Design-Doc fertig** (siehe unten) |
| **P1-093** | OpenAPI-Spec UI (Swagger/Redoc) | ⏳ PENDING | @codexa | 35min | API-Dokumentation visualisieren |

---

## 📊 P2 — MEDIUM (Wenn Kapazität)

| ID | Task | Status | Owner | ETA | Notes |
|----|------|--------|-------|-----|-------|
| **P2-020** | Micro-Interactions für Buttons | ⏳ PENDING | @designclaw | 20min | **CSS/JS sofort machbar** (siehe unten) |
| **P2-021** | Dark Mode Support | ⏳ PENDING | @designclaw | 25min | **CSS sofort machbar** (siehe unten) |
| **P2-022** | Loading-Skeletons für API-Calls | ⏳ PENDING | @codexa | 15min | UX bei Ladezuständen |

---

## ✅ COMPLETED (Diese Session)

| ID | Task | Completed | Commit | Notes |
|----|------|-----------|--------|-------|
| **P1-089** | Connection Pooling Dashboard-Widget | 2026-03-02 14:30 | abc123 | — |
| **P0-201** | Versions-Sync im Dashboard | 2026-03-23 07:10 | — | Workspace-Kandidat sichtbar |

---

## Task-Details

### P1-092: Dashboard-Habituszonen-Design

**Ziel:** 10 Habituszonen im Dashboard visualisieren mit Modul-Matrix.

**Design-Doc:** `docs/DESIGN.md` (vollständig, siehe Abschnitt 1-3)

**Offene Punkte:**
- Zone-Entity-Mapping (HA-Entity → Zone)
- Tag-System: `zone:<type>` pro Raum
- Modul-Zuordnung pro Zone
- Brain-Graph-Visualisierung

**Success Signal:** Design-Doc vollständig, Implementierung ready.

---

### P2-020: Micro-Interactions für Buttons

**Ziel:** Hover/Active/Focus-States für alle UI-Buttons.

**CSS-Implementierung:**
```css
.btn {
  transition: all 0.2s ease;
}

.btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(124, 106, 239, 0.3);
}

.btn:active {
  transform: translateY(0);
  box-shadow: 0 2px 6px rgba(124, 106, 239, 0.2);
}

.btn:focus-visible {
  outline: 2px solid var(--accent);
  outline-offset: 2px;
}
```

**Kein Backend nötig** — reine CSS/JS-Arbeit.

---

### P2-021: Dark Mode Support

**Ziel:** Vollständige Dark-Theme-Unterstützung.

**CSS-Variablen (bereits in `docs/DESIGN.md` definiert):**
```css
:root {
  /* Backgrounds */
  --bg:        #0a0e14;
  --surface:   #12171f;
  --card:      #171d27;
  --border:    #1e2a3a;

  /* Text */
  --text:      #e0e6ed;
  --dim:       #6b7a8d;

  /* Accents */
  --accent:    #7c6aef;
  --accent2:   #9b8afb;

  /* States */
  --green:     #34d399;
  --yellow:    #fbbf24;
  --red:       #f87171;
  --blue:      #60a5fa;
  --cyan:      #22d3ee;
}
```

**Light-Theme (Optional, falls erweitert):**
```css
[data-theme="light"] {
  --bg:        #ffffff;
  --surface:   #f5f7fa;
  --card:      #ffffff;
  --border:    #e0e6ed;
  --text:      #1a202c;
  --dim:       #718096;
}
```

**Kein Backend nötig** — reine CSS-Arbeit.

---

## Worker-Regeln

1. **Immer zuerst P0** abarbeiten
2. **Nach jedem Task:** Commit + Push + Update
3. **HA+Core Sync:** Dashboard muss Version beider Repos anzeigen
4. **UX-Check:** Vor Commit Accessibility-Review

---

**Letztes Update:** 2026-03-25 02:25 CET  
**Nächster Task:** P2-020 (Micro-Interactions) → P2-021 (Dark Mode) → P1-092 (Design-Doc Finalisierung)
