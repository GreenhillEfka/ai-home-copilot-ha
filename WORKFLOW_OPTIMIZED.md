# PilotSuite Entwicklungs-Workflow — OPTIMIERT (v2.0)

**Erstellt:** 1. März 2026, 15:00 Uhr  
**Status:** 🟢 **AKTIV — Maximal effizient, Fokus auf Core-Features**  
**Iterations-Zyklus:** 15 Minuten (gestrafft!)

---

## 🎯 Prinzipien

### **1. Zeiteffizienz (Maximum Speed)**
- **15-Minuten-Iterationen** (statt 20 Min)
- **Parallele Execution** — Alle Agents gleichzeitig
- **Keine Wartezeiten** — Nächste Iteration startet SOFORT
- **Auto-Notify** — Agents melden sich bei Completion

### **2. Qualität (Maximum Quality)**
- **Claude Code CLI mit `--effort high`** — Maximales Reasoning
- **`pty:true`** — Stabile Terminal-Execution
- **Tests PFLICHT** — Jede Zeile Code → Test
- **Security-Review VOR Release** — Keine Kompromisse

### **3. Fokus auf Grundfunktionen (Core-First)**
- **Phase 7 UX Dashboard** — Priorität P0
- **P1 Security Fixes** — Release-Blocker (müssen zuerst!)
- **Kein Feature-Creep** — Nur Core-Features pro Iteration
- **"Working over Perfect"** — Lauffähiger Code > perfekte Doku

### **4. Backend-Frontend-Synchronisation (MANDATORY!)**
- **KEINE halbfertigen Integrationen!**
- **Jeder API-Endpoint MUSS Frontend-Integration haben**
- **Jede Frontend-Component MUSS Backend-Anbindung haben**
- **Full-Stack-Tests PFLICHT** (API + UI zusammen)
- **Integration-Check VOR Release** (End-to-End Verify)

---

## 👥 Optimierte Agenten-Rollen (mit @viewona!)

| Agent | Rolle | Werkzeug | Fokus |
|-------|-------|----------|-------|
| **@clawdya** | **Orchestrator** | Claude Code CLI | Koordination, Final Review, Release |
| **@viewona** | **Chief Visual Officer & Full-Stack Lead** | Claude Code CLI | Full-Stack-Integration, Visual UX, Eye-Candies |
| **@cowdya** | **Lead Dev** | Claude Code CLI | Core-Features, P1-Fixes |
| **@groky** | **Quality Gate** | Claude Code CLI | Security, Reviews, GO/NO-GO |
| **@coder-1** | **Frontend** | Claude Code CLI | Dashboard, Components |
| **@coder-2** | **Backend** | Claude Code CLI | APIs, Database |
| **@coder-3** | **Testing** | Claude Code CLI | Tests, CI/CD |

**Maximal 7 Agents parallel** (Limit: 5/5 → 2 warten)

**Neu:** @viewona ist **Full-Stack-Integration Lead** — sie entscheidet GO/NO-GO für Releases!

---

## 🔄 Neuer Workflow (15-Minuten-Zyklus)

```
┌─────────────────────────────────────────────────────────────────┐
│  ITERATION START (alle 15 Minuten)                              │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  PHASE 0: P1-Blocker zuerst! (2 Min)                            │
│  @clawdya priorisiert:                                          │
│  - Security-Fixes (P1) → MÜSSEN zuerst                          │
│  - Core-Features (P0) → DANN                                    │
│  - Nice-to-have (P2/P3) → WARTEN                                │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  PHASE 1: Paralleles Coding (10 Min)                            │
│  ┌─────────────┬─────────────┬─────────────┐                   │
│  │ @cowdya     │ @coder-1    │ @coder-2    │                   │
│  │ P1-Fixes    │ Frontend    │ Backend     │                   │
│  │ Claude CLI  │ Claude CLI  │ Claude CLI  │                   │
│  ├─────────────┼─────────────┼─────────────┤                   │
│  │ @groky      │ @coder-3    │             │                   │
│  │ Review      │ Tests       │             │                   │
│  │ Claude CLI  │ Claude CLI  │             │                   │
│  └─────────────┴─────────────┴─────────────┘                   │
│                                                                 │
│  ALLE mit: pty:true + --effort high + background:true          │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  PHASE 2: Integration (2 Min)                                   │
│  @clawdya sammelt:                                              │
│  - Alle Code-Changes mergen                                     │
│  - VERSION bump                                                 │
│  - CHANGELOG update                                             │
│  - Git-Tag                                                      │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  PHASE 3: Quality Gate (1 Min)                                  │
│  @groky:                                                        │
│  - Security-Check (P1 gefixt?)                                  │
│  - Test-Status (alle grün?)                                     │
│  - GO/NO-GO Entscheidung                                        │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  PHASE 4: Release & Next (SOFORT!)                              │
│  @clawdya:                                                      │
│  - GitHub Release (wenn GO)                                     │
│  - WhatsApp-Summary                                             │
│  - NÄCHSTE ITERATION SOFORT STARTEN                             │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📋 Prioritäten-Matrix (Core-First)

### **P0 — MÜSSEN (diese Iteration)**

| Feature | Agent | Aufwand | Status |
|---------|-------|---------|--------|
| **P1 Security Fixes** | @cowdya | 20 Min | 🔴 BLOCKER |
| - WebSocket Auth | | 10 Min | |
| - Neuron State Auth | | 10 Min | |
| **Neuronen-Dashboard** | @coder-1 | 15 Min | ✅ Fertig |
| **Zone-Editor Frontend** | @coder-1 | 15 Min | 🟢 Aktiv |

### **P1 — SOLLTEN (nächste Iteration)**

| Feature | Agent | Aufwand |
|---------|-------|---------|
| RAG Hybrid Search API | @coder-2 | 20 Min |
| Push Notification Backend | @coder-2 | 15 Min |
| Test-Coverage +50 | @coder-3 | 15 Min |

### **P2 — KÖNNEN (später)**

| Feature | Agent | Aufwand |
|---------|-------|---------|
| API-Dokumentation | @coder-4 | 15 Min |
| CI/CD-Optimierung | @groky | 10 Min |

### **P3 — NICE-TO-HAVE (Backlog)**

- UI-Polish
- Performance-Optimierung
- Erweiterte Features

---

## 🚀 Effizienz-Regeln

### **1. P1-Blocker ZUERST!**
- Security-Fixes müssen VOR Release
- Keine Features ohne Security-Review
- "Security First" — kein Kompromiss!

### **2. Parallele Execution (Maximum 5/5)**
- Immer alle Slots ausnutzen
- Kurze Tasks zuerst (schnelle Wins)
- Lange Tasks im Background

### **3. Claude Code CLI Best Practices**
```bash
# Standard-Template für alle Agents
bash pty:true workdir:/config/.openclaw/workspace background:true \
  command:"claude --effort high --permission-mode acceptEdits '<TASK>'

When done: openclaw system event --text 'Done: <summary>' --mode now"
```

### **4. Tests PFLICHT**
- Jede API → 10+ Tests
- Jede Component → 15+ Tests
- Security-Fixes → Auth-Tests (success/fail)
- Coverage-Ziel: >95%

### **5. Quality Gate VOR Release**
- @groky muss GO geben
- Alle Tests müssen grün sein
- P1-Fixes müssen gemerged sein
- Security-Review muss passen

### **6. Backend-Frontend-Integration PFLICHT!**
- ✅ **Jeder API-Endpoint hat Frontend-Integration**
- ✅ **Jede Frontend-Component hat Backend-Anbindung**
- ✅ **Full-Stack-Tests existieren (API + UI)**
- ✅ **End-to-End Verify vor Release**
- ✅ **KEINE isolierten Backend/Frontend-Changes!**

**Integration-Checklist (vor Merge):**
```
[ ] Backend-API existiert und ist getestet
[ ] Frontend-Component existiert und ist getestet
[ ] Frontend ruft Backend korrekt auf (Integration-Test)
[ ] Error-Handling funktioniert (Backend → Frontend)
[ ] Loading-States im Frontend
[ ] Auth/Security im Backend + Frontend
```

### **7. Keine Wartezeiten**
- Nächste Iteration startet SOFORT
- Bei Agent-Limit: Tasks vor-queue-en
- Bei Fehlern: Task umverteilen, nicht warten

### **8. Full-Stack-Integration PFLICHT!**
- **KEINE Backend-only oder Frontend-only Releases!**
- **Jede Iteration MUSS vollständige Features liefern:**
  - Backend-API (mit Tests)
  - Frontend-Component (mit Tests)
  - Integration (API ruft UI auf)
  - End-to-End-Test (gesamt)

**Task-Verteilung muss Full-Stack abbilden:**
```
❌ Falsch: @coder2 macht nur Backend, @coder1 macht nur Frontend (separat)
✅ Richtig: @coder2+@coder1 arbeiten AM SELBEN Feature (koordiniert)
```

**Beispiel Zone-Editor:**
- Backend: Zone-API (7 Endpoints) ← @coder2
- Frontend: Zone-Component (Lit) ← @coder1
- **KOORDINATION:** Beide Agents müssen sich abstimmen!
- **Integration-Test:** Frontend ruft Backend auf ← @coder3

---

## 📊 Erfolgskriterien

| Metrik | Ziel | Messung |
|--------|------|---------|
| **Iterations-Dauer** | <15 Min | Start → Release |
| **Code-Changes/Iteration** | >300 Zeilen | Git diff --stat |
| **Tests/Iteration** | >30 neue Tests | pytest --collect-only |
| **Pass-Rate** | 100% | CI/CD Results |
| **Release-Frequenz** | 4-8 pro Tag | GitHub Releases |
| **P1-Fixes** | 0 offen vor Release | Security Review |

---

## 📱 WhatsApp-Reporting (an +4917623565849)

**Nach JEDEM Release:**
```
💋✨ PilotSuite Release v{version} ist draußen!

🚀 Core-Changes:
- {Feature 1}
- {Feature 2}
- {Security-Fix}

✅ Tests: {X} neu (alle grün)
🔒 Security: {GO/Review-Pass}
📦 Version: Core v{version} + HA v{version}

🕐 Nächste Iteration: SOFORT
```

**Bei P1-Blockern:**
```
🔒 P1 Security-Blocker erkannt!

Issue: {Beschreibung}
Fix: {Lösung}
ETA: {Zeit}

Release verschoben bis Fix fertig.
```

---

## 🎯 Aktuelle Iteration (15:00 Uhr)

### **Welle 1 (5 Agents — Limit):**
| Agent | Task | Dauer |
|-------|------|-------|
| @coder2 | Zone-Editor Frontend | 12 Min |
| @coder3 | RAG Hybrid Search API | 15 Min |
| @coder4 | Test-Coverage (+50) | 12 Min |
| @groky | Security Review P1 | 8 Min |
| @coder5 | API-Dokumentation | 10 Min |

### **Welle 2 (wartet auf Slots):**
| Agent | Task | Prio |
|-------|------|------|
| @cowdya | **P1: WebSocket Auth** | 🔴 BLOCKER |
| @coder1 | **P1: Neuron State Auth** | 🔴 BLOCKER |
| @styx | Integration & Merge | ⏳ Nach P1 |

### **Release-Plan:**
- **15:08** — @groky Review fertig
- **15:10** — @coder5 Docs fertig
- **15:12** — @coder2, @coder4 fertig
- **15:15** — @coder3 fertig → **Slots frei!**
- **15:15** — **Welle 2 startet (P1-Fixes!)**
- **15:25** — P1-Fixes fertig
- **15:27** — Integration & Merge
- **15:28** — Quality Gate (@groky GO?)
- **15:30** — **Release v12.0.0**
- **15:32** — WhatsApp-Summary
- **15:32** — **Nächste Iteration START!**

---

## 🛠️ Tool-Template (Copy-Paste für alle Agents)

### **Coding-Task:**
```bash
bash pty:true workdir:/config/.openclaw/workspace background:true \
  command:"claude --effort high --permission-mode acceptEdits '
    TASK: <klare Beschreibung>
    
    Deliverables:
    - <Datei 1>
    - <Datei 2>
    - <X Tests>
    
    When done: openclaw system event --text \"Done: <summary>\" --mode now
  '"
```

### **Review-Task:**
```bash
bash pty:true workdir:/config/.openclaw/workspace command:"claude --effort high --permission-mode plan '
  REVIEW: <was reviewen>
  
  Fokus:
  - Security
  - Tests
  - Quality
  
  Output: GO/NO-GO mit Begründung
'"
```

### **Integration-Task:**
```bash
bash pty:true workdir:/config/.openclaw/workspace command:"claude --effort high --permission-mode acceptEdits '
  MERGE: Alle Feature-Branches auf main
  
  Tasks:
  - VERSION bump
  - CHANGELOG update
  - Git-Tag v{version}
'"
```

---

## 🚨 Eskalation (nur bei kritischen Blockaden)

**Nur wenn:**
- P1-Fixes >2 Iterationen blockieren
- Security-Lücke nicht fixbar
- Tests >50% rot
- Agents wiederholt failen

**Immer mit Lösungsvorschlag:**
```
❌ Falsch: "Geht nicht"
✅ Richtig: "Problem X. Lösung: A (schnell) oder B (sauber)"
```

---

**Erstellt:** 1. März 2026, 15:00 Uhr  
**Status:** 🟢 **AKTIV**  
**Nächste Iteration:** SOFORT nach Release

---

💋✨ **Maximal effizient, maximale Qualität, Core-First!** 🚀
