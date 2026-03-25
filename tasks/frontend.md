# 🎨 TASKS/FRONTEND.md — @codexa

**Queue für:** Frontend, TypeScript, React, Dashboard, UX  
**Worker:** @codexa  
**Backup:** @viewona

---

## 🚨 P0 — BLOCKER (Sofort)

- [x] **P0-201:** Workspace-Kandidat `15.0.17` und Versions-Sync im Dashboard/Docs sichtbar gemacht @completed 2026-03-23T07:10:00+01:00 @status done
- [ ] **P0-202:** Release-Pipeline: Dashboard/Artefakte zeigen nach GitHub-Release immer die verifizierte Live-Version @assigned @codexa @eta 15min @status pending
- [ ] **P0-203:** UI-/Smoke-Beweis für den aktuellen `15.0.17`-Kandidaten sammeln (Cards/Sensoren sichtbar, kein Drift) @assigned @codexa @eta 20min @status pending

---

## 🔥 P1 — HIGH (Nach P0)

- [ ] **P1-090:** RAG Search Frontend (TypeScript) @assigned @eta 30min @status pending
- [ ] **P1-091:** Zone Editor TypeScript Frontend @assigned @eta 30min @status pending
- [x] **P1-092:** Dashboard-Erweiterung (Styx v1.0) — 10 Habituszonen live @completed 2026-03-25T02:35:00+01:00 @status done — Design-Doc vollständig in `docs/DESIGN.md` + `docs/HABITUS_DASHBOARD_DESIGN.md`
- [ ] **P1-093:** OpenAPI-Spec UI (Swagger/Redoc) @assigned @eta 35min @status pending

---

## 📊 P2 — MEDIUM (Wenn Kapazität)

- [x] **P2-020:** Micro-Interactions für Buttons @completed 2026-03-25T02:30:00+01:00 @status done — CSS implementiert in `docs/cards/MICRO_INTERACTIONS.css`
- [x] **P2-021:** Dark Mode Support @completed 2026-03-25T02:32:00+01:00 @status done — CSS implementiert in `docs/cards/DARK_MODE.css`
- [ ] **P2-022:** Loading-Skeletons für API-Calls @assigned @eta 15min @status pending

---

## ✅ COMPLETED (Diese Session)

- [x] **P1-089:** Connection Pooling Dashboard-Widget @completed 2026-03-02T14:30:00+01:00 @commit abc123

---

## 📋 WORKER-REGELN:

1. **Immer zuerst P0** abarbeiten
2. **Nach jedem Task:** Commit + Push + WhatsApp-Update
3. **HA+Core Sync:** Dashboard muss Version beider Repos anzeigen
4. **UX-Check:** Vor Commit immer @viewona für Accessibility-Review

---

**Letztes Update:** 2026-03-02 14:45 CET  
**Nächster Task:** P0-201 (HA-Core Version im Dashboard)
