# PilotSuite Entwicklungs-Workflow — FINAL (v3.0)

**Erstellt:** 1. März 2026, 15:40 Uhr  
**Status:** 🟢 **AKTIV — Klare Rollentrennung**  
**Iterations-Zyklus:** 15 Minuten (gestrafft!)

---

## 👥 Rollen & Verantwortlichkeiten (FINAL)

| Agent | Rolle | Hauptaufgabe | Werkzeug |
|-------|-------|--------------|----------|
| **@clawdya** 💋 | **Orchestrator & Koordinator** | - Gesamt-Koordination<br>- Full-Stack-Planung<br>- Final Review<br>- Official Release<br>- WhatsApp-Summary | Claude Code CLI |
| **@styx** 🤖 | **Integration Lead & Dev-Manager** | - Dev-Version zusammenführen<br>- Coding-Agents koordinieren<br>- Zuarbeit von allen sammeln<br>- Release-Candidate vorbereiten<br>- @clawdya zum Review übergeben | Claude Code CLI (pty:true) |
| **@groky** 🔍 | **Security & Quality Gate** | - Security Reviews<br>- CI/CD Checks<br>- GO/NO-GO Empfehlung<br>- P1-Blocker identifizieren | Claude Code CLI (pty:true) |
| **@cowdya** 💻 | **Lead Developer** | - Core-Features implementieren<br>- P1-Fixes<br>- Backend + Frontend | Claude Code CLI (pty:true) |
| **@viewona** 🎨 | **Visual UX & 3D Vision** | - Visuelle Excellence<br>- Eye-Candies<br>- 3D-Visualisierungen<br>- Custom HA UIs | Claude Code CLI (pty:true) |
| **@coder-1..4** 👨‍💻 | **Coding-Squad** | - Parallele Feature-Implementation<br>- Frontend/Backend-Spezialisierung<br>- Tests schreiben | Claude Code CLI (pty:true) |

---

## 🔄 Entwicklungs-Iteration (15-Minuten-Zyklus)

```
┌─────────────────────────────────────────────────────────────────┐
│  ITERATION START (@clawdya koordiniert)                         │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  PHASE 0: Full-Stack-Plan (@clawdya, 3 Min)                     │
│  @clawdya erstellt:                                             │
│  - Backend ↔ Frontend Mapping                                   │
│  - Integration-Tests definieren                                 │
│  - UX-Standards festlegen (@viewona konsultieren)               │
│  - Tasks für @styx vorbereiten                                  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  PHASE 1: Paralleles Coding (10 Min)                            │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  @styx koordiniert Coding-Agents:                        │   │
│  │  - @cowdya (Core-Features)                               │   │
│  │  - @coder-1 (Frontend)                                   │   │
│  │  - @coder-2 (Backend)                                    │   │
│  │  - @coder-3 (Testing)                                    │   │
│  │  - @coder-4 (Docs)                                       │   │
│  │  - @viewona (Visual UX)                                  │   │
│  │                                                          │   │
│  │  @groky parallel:                                        │   │
│  │  - Security Reviews                                      │   │
│  │  - CI/CD Checks                                          │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  PHASE 2: Integration (@styx, 5 Min)                            │
│  @styx sammelt alle Zuarbeiten:                                 │
│  - Code-Changes von @cowdya, @coder-*                           │
│  - Visual UX von @viewona                                       │
│  - Security-Status von @groky                                   │
│  - Dev-Version zusammenführen                                   │
│  - Release-Candidate erstellen                                  │
│  - An @clawdya zum Official Review übergeben                    │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  PHASE 3: Official Review (@clawdya, 2 Min)                     │
│  @clawdya prüft:                                                │
│  - Full-Stack-Complete? (Backend + Frontend + Integration)      │
│  - Security-Review von @groky (GO?)                             │
│  - UX-Standards von @viewona (erfüllt?)                         │
│  - Release-Candidate von @styx (bereit?)                        │
│  - GO/NO-GO Entscheidung                                        │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  PHASE 4: Official Release (@clawdya, 1 Min)                    │
│  Bei GO:                                                        │
│  - GitHub Release erstellen                                     │
│  - WhatsApp-Summary senden                                      │
│  - Nächste Iteration SOFORT starten                             │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📋 Detail-Aufgaben pro Agent

### **@clawdya (Orchestrator)**

**Phase 0 (Full-Stack-Plan):**
```bash
# Full-Stack-Plan erstellen
claude --effort high "
Erstelle Full-Stack-Plan für Iteration {version}:

1. Feature-Mapping:
   - Backend-APIs (welche Endpoints?)
   - Frontend-Components (welche UIs?)
   - Integration-Tests (API ↔ Frontend)

2. UX-Standards (mit @viewona abgestimmt):
   - Micro-Interactions
   - Animationen
   - Loading/Error-States
   - Eye-Candies

3. Task-Verteilung für @styx:
   - @cowdya: {Tasks}
   - @coder-1: {Tasks}
   - @coder-2: {Tasks}
   - @viewona: {Tasks}
"
```

**Phase 3 (Official Review):**
```bash
# Review von @styx Dev-Version
claude --effort high "
Reviewe Release-Candidate von @styx:

Checklist:
[ ] Full-Stack-Complete? (Backend + Frontend + Integration)
[ ] Security-Review von @groky (GO?)
[ ] UX-Standards erfüllt? (@viewona)
[ ] Alle Tests grün?
[ ] CHANGELOG aktuell?
[ ] VERSION bumped?

Output: GO/NO-GO mit Begründung
"
```

**Phase 4 (Official Release):**
```bash
# GitHub Release
gh release create v{version} --title "PilotSuite v{version}" --notes-file CHANGELOG.md

# WhatsApp-Summary
message to:+4917623565849 "💋✨ PilotSuite Release v{version} ist draußen! ..."
```

---

### **@styx (Integration Lead)**

**Phase 1 (Coding-Koordination):**
```bash
# Coding-Agents koordinieren
sessions_spawn task:"{@cowdya Tasks}" label:cowdya-feature
sessions_spawn task:"{@coder-1 Tasks}" label:coder1-frontend
sessions_spawn task:"{@coder-2 Tasks}" label:coder2-backend
sessions_spawn task:"{@coder-3 Tasks}" label:coder3-testing
sessions_spawn task:"{@viewona Tasks}" label:viewona-visual
```

**Phase 2 (Integration):**
```bash
# Dev-Version zusammenführen
claude --effort high --permission-mode acceptEdits "
Sammle alle Code-Changes:
- Von @cowdya (Core-Features)
- Von @coder-* (Frontend/Backend/Tests)
- Von @viewona (Visual UX)

Tasks:
1. Git-Merge auf dev-Branch
2. Konflikte lösen
3. VERSION bump
4. CHANGELOG update
5. Release-Candidate erstellen
6. An @clawdya zum Review übergeben

Output: Release-Candidate in /releases/v{version}-rc/
"
```

---

### **@groky (Security & Quality)**

**Phase 1 (Parallel zu Coding):**
```bash
# Security Reviews
claude --effort high --permission-mode plan "
Reviewe alle neuen APIs und Features:

Fokus:
- Authentication (alle Endpoints?)
- Authorization (Role-Based?)
- Input-Validation
- Error-Handling
- OWASP Top 10

Output: security_review_{timestamp}.md
        GO/NO-GO Empfehlung
"
```

---

### **@cowdya (Lead Developer)**

**Phase 1 (Core-Features):**
```bash
# Core-Features implementieren
claude --effort high --permission-mode acceptEdits "
Implementiere:
- {Feature 1} (Backend + Frontend)
- {Feature 2} (P1-Fixes)
- {Feature 3} (Integration)

Deliverables:
- Code (Git-Commits)
- Tests (20+ pro Feature)
- CHANGELOG-Eintrag
"
```

---

### **@viewona (Visual UX & 3D Vision)**

**Phase 1 (Visuelle Excellence):**
```bash
# Visual UX implementieren
claude --effort high --permission-mode acceptEdits "
Implementiere für {Feature}:

1. Micro-Interactions:
   - Hover-States
   - Focus-States (Accessibility!)
   - Active-States
   - Transitions

2. Animationen:
   - Fade-In bei Load
   - Pulse bei Events
   - Smooth Transitions

3. Loading/Error-States:
   - Skeleton Screens
   - User-Friendly Errors
   - Recovery-Options

4. Eye-Candies:
   - Particle-Effects (bei Success)
   - Gradients (dynamisch)
   - 3D-Transforms (wo sinnvoll)

Deliverables:
- CSS/JS für Animationen
- Component-Updates
- UX-Checklist (erfüllt?)
"
```

**3D-Vision Spezialaufgaben:**
```bash
# 3D-Visualisierungen
claude --effort high --permission-mode acceptEdits "
Erstelle 3D-Visualisierung für:
- Neuronen-Network (Force-Directed Graph)
- Zone-Mapping (3D-Floorplan)
- Entity-Relationships (Network-Graph)

Tech-Stack:
- D3.js v7 (Canvas/SVG)
- Three.js (für echte 3D)
- A-Frame (VR/AR ready)

Deliverables:
- 3D-Component
- Interaktion (Zoom, Pan, Click)
- Performance-optimiert
"
```

---

## 📊 Full-Stack-Integration (MANDATORY!)

### **Checklist VOR Release (@clawdya prüft):**

```
[ ] Backend-API existiert und ist getestet
[ ] Frontend-Component existiert und ist getestet
[ ] Frontend ruft Backend korrekt auf (Integration-Test)
[ ] Error-Handling funktioniert (Backend → Frontend)
[ ] Loading-States im Frontend
[ ] Auth/Security im Backend + Frontend
[ ] WebSocket-Updates (wo relevant)
[ ] UX-Standards erfüllt (@viewona)
[ ] Eye-Candies implementiert (@viewona)
[ ] Security-Review GO (@groky)
[ ] Dev-Version bereit (@styx)
```

### **GO/NO-GO Kriterien:**

| Kriterium | GO | NO-GO |
|-----------|----|----|
| **Full-Stack-Complete** | Backend + Frontend + Integration | Backend-only oder Frontend-only |
| **Security-Review** | @groky GO | @groky NO-GO (P1 offen) |
| **UX-Standards** | @viewona erfüllt | @viewona nicht erfüllt |
| **Tests** | Alle grün (>95% Coverage) | Tests rot oder <90% Coverage |
| **Integration** | @styx bereit | @styx Konflikte offen |

---

## 🎯 Aktuelle Iteration (v12.0.0)

### **Phase 0: Full-Stack-Plan (@clawdya)**

**Features für v12.0.0:**
| Feature | Backend | Frontend | Integration | Prio |
|---------|---------|----------|-------------|------|
| Neuronen-Dashboard | ✅ | ✅ | ⏳ | P0 |
| Security-Fixes | ✅ | N/A | ✅ | P0 |
| Zone-Editor | 🟢 Aktiv | 🟢 Aktiv | ❌ | P0 |
| RAG Search | ✅ | ❌ | ❌ | ⏮️ v12.1.0 |
| Zone-Dashboard | ✅ | ❌ | ❌ | ⏮️ v12.1.0 |

### **Phase 1: Coding (@styx koordiniert)**

| Agent | Task | Status |
|-------|------|--------|
| @cowdya | Security-Fixes (WebSocket Auth) | ✅ Fertig |
| @coder-1 | Neuronen-Dashboard Frontend | ✅ Fertig |
| @coder-2 | Zone-Editor Frontend | 🟢 Aktiv |
| @coder-3 | Test-Coverage (+50) | ✅ Fertig |
| @coder-4 | API-Dokumentation | ✅ Fertig |
| @viewona | Visual UX (Neuronen-Animationen) | ⏳ Pending |
| @groky | Security Review | ✅ GO |

### **Phase 2: Integration (@styx)**

**Tasks:**
- [ ] Alle Code-Changes sammeln
- [ ] Git-Merge auf dev
- [ ] VERSION=12.0.0
- [ ] CHANGELOG update
- [ ] Release-Candidate erstellen
- [ ] An @clawdya übergeben

### **Phase 3: Official Review (@clawdya)**

**Prüfung:**
- [ ] Full-Stack-Complete?
- [ ] Security-Review GO?
- [ ] UX-Standards erfüllt?
- [ ] Alle Tests grün?
- [ ] GO/NO-GO Entscheidung

### **Phase 4: Official Release (@clawdya)**

**Bei GO:**
- [ ] GitHub Release v12.0.0
- [ ] WhatsApp-Summary
- [ ] Nächste Iteration START!

---

## 📱 WhatsApp-Reporting (an +4917623565849)

**Nach JEDEM Release:**
```
💋✨ PilotSuite Release v{version} ist draußen!

🚀 Core-Changes:
- {Feature 1} (Full-Stack)
- {Feature 2} (Security)
- {Eye-Candy} (Visual UX by @viewona)

✅ Tests: {X} neu (alle grün)
🔒 Security: {GO/Review-Pass}
🎨 UX: {Standards erfüllt}
📦 Version: Core v{version} + HA v{version}

🕐 Nächste Iteration: SOFORT
```

---

## 🚀 Effizienz-Regeln

### **1. @clawdya koordiniert alles**
- Full-Stack-Planung
- Task-Verteilung an @styx
- Final Review
- Official Release

### **2. @styx integriert**
- Coding-Agents koordinieren
- Dev-Version zusammenführen
- Release-Candidate vorbereiten
- An @clawdya übergeben

### **3. @groky reviewt**
- Security-Reviews
- GO/NO-GO Empfehlung
- P1-Blocker identifizieren

### **4. @cowdya coded**
- Core-Features
- P1-Fixes
- Backend + Frontend

### **5. @viewona verschönert**
- Visual UX Excellence
- Eye-Candies
- 3D-Visualisierungen
- Custom HA UIs

### **6. Full-Stack PFLICHT!**
- KEINE Backend-only Releases
- KEINE Frontend-only Releases
- Integration-Tests MÜSSEN existieren

---

## 📈 Erfolgskriterien

| Metrik | Ziel | Messung |
|--------|------|---------|
| **Iterations-Dauer** | <15 Min | Start → Release |
| **Full-Stack-Coverage** | 100% | Kein Backend-only! |
| **Code-Changes/Iteration** | >300 Zeilen | Git diff --stat |
| **Tests/Iteration** | >30 neue Tests | pytest --collect-only |
| **Pass-Rate** | 100% | CI/CD Results |
| **Release-Frequenz** | 4-8 pro Tag | GitHub Releases |
| **UX-Standards** | 100% erfüllt | @viewona Check |
| **Eye-Candies** | 1+ pro Feature | Animationen, Effects |

---

**Erstellt:** 1. März 2026, 15:40 Uhr  
**Status:** 🟢 **AKTIV**  
**Nächste Iteration:** SOFORT nach Release

---

💋✨ **Klare Rollen, maximale Effizienz, Full-Stack PFLICHT!** 🚀
